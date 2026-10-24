"""
Streamlit Web App: Free AI Chess Game Review & Coach.
Paste any Chess.com game link or PGN to get deep Stockfish 19 analysis + GM coaching.
"""

import streamlit as st
import chess
import chess.svg
import chess.pgn
import base64
from src.chess_fetcher import fetch_from_chess_com, parse_pgn_to_game
from src.engine import GameAnalyzer
from src.coach import generate_coach_advice

st.set_page_config(page_title="AI Chess Coach & Game Review", page_icon="♟️", layout="wide")

# Custom CSS for dark-mode aesthetic cards and badges
st.markdown("""
<style>
    .badge-best { background-color: #22c55e; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-excellent { background-color: #3b82f6; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-inaccuracy { background-color: #eab308; color: black; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-mistake { background-color: #f97316; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-blunder { background-color: #ef4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-brilliant { background-color: #a855f7; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .plan-box { background-color: #1e293b; border-left: 4px solid #38bdf8; padding: 12px; margin-bottom: 10px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

st.title("♟️ AI Chess Coach & Game Review")
st.caption("Powered by Stockfish 19 & Groq LLM — 100% Free Game Review with Strategic Plans")

# Preloaded Legal's Mate sample PGN
DEFAULT_PGN = """1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 Bxd1 6. Bxf7+ Ke7 7. Nd5# 1-0"""

with st.sidebar:
    st.header("📥 Input Game")
    input_method = st.radio("Choose Input:", ["Chess.com URL", "Paste PGN Text"])
    
    game_url = ""
    pgn_input = ""
    
    if input_method == "Chess.com URL":
        game_url = st.text_input("Chess.com Game Link:", placeholder="https://www.chess.com/game/live/123456789")
    else:
        pgn_input = st.text_area("PGN Moves:", value=DEFAULT_PGN, height=180)
        
    engine_depth = st.slider("Stockfish Depth:", min_value=10, max_value=18, value=12)
    flip_board = st.checkbox("Flip Board (View as Black)", value=False)
    start_btn = st.button("🚀 Analyze Game", type="primary", use_container_width=True)

# Session state to store analysis results across page interactions
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
    st.session_state.game_meta = {}
    st.session_state.move_idx = 0

if start_btn:
    pgn_to_analyze = ""
    uci_moves_to_analyze = []
    meta = {}
    
    try:
        if input_method == "Chess.com URL":
            if not game_url:
                st.error("Please enter a valid Chess.com link.")
                st.stop()
            with st.spinner("📡 Fetching game from Chess.com..."):
                fetch_res = fetch_from_chess_com(game_url)
                pgn_to_analyze = fetch_res["pgn"]
                uci_moves_to_analyze = fetch_res.get("uci_moves", [])
                meta = fetch_res
        else:
            pgn_to_analyze = pgn_input
            meta = {"white": "White", "black": "Black", "result": "Analyzed Game"}

        game = parse_pgn_to_game(pgn_to_analyze, uci_moves=uci_moves_to_analyze)
        
        # UI Live Progress Bar
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_ui_progress(current, total):
            pct = int((current / total) * 100)
            full_move_no = (current + 1) // 2
            side = "White" if current % 2 != 0 else "Black"
            progress_bar.progress(current / total)
            status_text.text(f"🤖 Stockfish 19 analyzing: Move {full_move_no} ({side}) • {pct}% completed ({current}/{total} turns)")

        analyzer = GameAnalyzer(depth=engine_depth, max_time_per_move=0.08)
        results = analyzer.analyze_game(game, progress_callback=update_ui_progress)
        analyzer.close()

        progress_bar.empty()
        status_text.empty()
        
        if not results["moves"]:
            st.warning("⚠️ No valid moves were found in this game.")
            st.stop()
            
        st.session_state.analysis_results = results
        st.session_state.game_meta = meta
        st.session_state.move_idx = 0
        st.success("✓ Analysis Complete!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error during analysis: {e}")

# ==========================================
# RENDER ANALYSIS DASHBOARD
# ==========================================
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    meta = st.session_state.game_meta
    total_moves = results["total_moves"]
    full_move_count = (total_moves + 1) // 2
    
    # Calculate Overall Accuracy
    white_acc_loss = [m["win_loss"] for m in results["moves"] if m["color"] == "White"]
    black_acc_loss = [m["win_loss"] for m in results["moves"] if m["color"] == "Black"]
    white_acc = max(0.0, round(100.0 - (sum(white_acc_loss) / len(white_acc_loss) * 2), 1)) if white_acc_loss else 100.0
    black_acc = max(0.0, round(100.0 - (sum(black_acc_loss) / len(black_acc_loss) * 2), 1)) if black_acc_loss else 100.0

    # Top Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⚪ White", meta.get("white", "White"), delta=f"{white_acc}% Acc")
    m2.metric("⚫ Black", meta.get("black", "Black"), delta=f"{black_acc}% Acc")
    m3.metric("📏 Game Length", f"{full_move_count} Moves ({total_moves} Turns)")
    m4.metric("🏆 Result", meta.get("result", "Complete"))
    
    st.divider()

    # Move Navigation Controls
    col_nav1, col_nav2, col_nav3, col_nav4, col_slider = st.columns([1, 1, 1, 1, 6])
    
    with col_nav1:
        if st.button("⏮ First"):
            st.session_state.move_idx = 0
    with col_nav2:
        if st.button("◀ Prev"):
            st.session_state.move_idx = max(0, st.session_state.move_idx - 1)
    with col_nav3:
        if st.button("Next ▶"):
            st.session_state.move_idx = min(total_moves - 1, st.session_state.move_idx + 1)
    with col_nav4:
        if st.button("⏭ Last"):
            st.session_state.move_idx = total_moves - 1
            
    with col_slider:
        st.session_state.move_idx = st.slider(
            "Move Navigator", 0, total_moves - 1, st.session_state.move_idx,
            label_visibility="collapsed"
        )

    current_move = results["moves"][st.session_state.move_idx]
    
    # Layout: Board on Left, Coach & Plans on Right
    board_col, coach_col = st.columns([5, 6])
    
    with board_col:
        board = chess.Board(current_move["fen_after"])
        parsed_board_before = chess.Board(current_move["fen_before"])
        
        # Visual Arrows: Red for played blunder, Green for engine's best move
        arrows = []
        played_move_obj = None
        best_move_obj = None
        
        # 1. Best Move Arrow (Green)
        try:
            best_move_obj = parsed_board_before.parse_san(current_move["best_move"])
        except Exception:
            try:
                best_move_obj = chess.Move.from_uci(current_move["best_move"])
            except Exception:
                best_move_obj = None

        if best_move_obj:
            arrows.append(chess.svg.Arrow(best_move_obj.from_square, best_move_obj.to_square, color="#22c55ecc"))
            
        # 2. Played Move Arrow (Red if blunder, Blue if good)
        arrow_color = "#ef4444cc" if current_move["classification"] in ["Blunder", "Mistake"] else "#3b82f6aa"
        try:
            played_move_obj = parsed_board_before.parse_san(current_move["played_move"])
        except Exception:
            try:
                played_move_obj = chess.Move.from_uci(current_move["played_move"])
            except Exception:
                played_move_obj = None

        if played_move_obj:
            arrows.append(chess.svg.Arrow(played_move_obj.from_square, played_move_obj.to_square, color=arrow_color))

        # Render SVG Chessboard
        orientation = chess.BLACK if flip_board else chess.WHITE
        board_svg = chess.svg.board(
            board=board,
            size=450,
            arrows=arrows,
            orientation=orientation,
            lastmove=played_move_obj
        )
        
        # Display SVG cleanly in Streamlit
        b64_svg = base64.b64encode(board_svg.encode('utf-8')).decode('utf-8')
        st.markdown(f'<img src="data:image/svg+xml;base64,{b64_svg}" width="100%"/>', unsafe_allow_html=True)
        
        # Clean Chess Notation Caption
        full_move_num = (st.session_state.move_idx // 2) + 1
        eval_display = "Checkmate" if abs(current_move['eval_after']) >= 9900 else f"{current_move['eval_after']/100:+.2f}"
        st.write(f"**Move {full_move_num}** • **{current_move['color']}** played **{current_move['played_move']}** | Engine Eval: **{eval_display}**")

    with coach_col:
        badge_class = f"badge-{current_move['classification'].lower()}"
        st.markdown(f"### Verdict: <span class='{badge_class}'>{current_move['classification']}</span>", unsafe_allow_html=True)
        
        if current_move["classification"] in ["Blunder", "Mistake", "Inaccuracy"]:
            st.error(f"Win probability dropped by **{current_move['win_loss']}%**! Best move was **{current_move['best_move']}**.")
            
            # Cache Coach Advice so moving Next/Prev is instantaneous
            if "coach_advice" not in current_move:
                with st.spinner("🎓 Coach is reviewing this position..."):
                    current_move["coach_advice"] = generate_coach_advice(current_move)
            coach_advice = current_move["coach_advice"]
                
            st.markdown("#### 🎓 Grandmaster Coach Breakdown")
            st.info(f"**❌ What Went Wrong:**\n\n{coach_advice.get('what_went_wrong')}")
            st.success(f"**💡 The Missed Plan:**\n\n{coach_advice.get('the_missed_plan')}")
            st.warning(f"**🧠 Mental Rule to Remember:**\n\n{coach_advice.get('how_to_think')}")
        else:
            st.success(f"Great move! Maintained the position's advantage.")
            
        st.divider()
        
        # Display Stockfish's Top 3 Strategic Directions
        st.markdown("#### 🧭 Top 3 Plans Considered by Stockfish")
        for idx, plan in enumerate(current_move.get("top_plans", []), 1):
            eval_str = f"{plan['score_cp']/100:+.2f}"
            st.markdown(f"""
            <div class="plan-box">
                <b>Plan {idx}: <span style="color: #38bdf8;">{plan['move']}</span> (Eval: {eval_str})</b><br>
                <small style="color: #94a3b8;">Continuations: {plan['line']}</small>
            </div>
            """, unsafe_allow_html=True)