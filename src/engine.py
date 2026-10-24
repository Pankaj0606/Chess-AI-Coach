"""
Stockfish Game Analysis Engine (Optimized & Fast).
- MultiPV = 3 evaluation
- Time-capped per move (snappy 8-10 second full-game analysis)
- Progress callback support for Streamlit UI
"""

import os
import shutil
import chess
import chess.engine
import chess.pgn
from typing import List, Dict, Optional, Callable

# Locate local Stockfish binary
STOCKFISH_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin", "stockfish"))
if not os.path.exists(STOCKFISH_PATH):
    STOCKFISH_PATH = shutil.which("stockfish") or "/opt/homebrew/bin/stockfish"


def win_percentage(cp_score: float) -> float:
    """Converts centipawn evaluation into winning probability [0.0, 1.0]."""
    return 1.0 / (1.0 + 10.0 ** (-cp_score / 400.0))


def classify_move(win_diff: float, is_sacrifice: bool, played_is_best: bool) -> str:
    """Classifies a move based on win% loss and material sacrifice."""
    if played_is_best and is_sacrifice:
        return "Brilliant"
    if win_diff <= 0.02:
        return "Best"
    elif win_diff <= 0.05:
        return "Excellent"
    elif win_diff <= 0.10:
        return "Inaccuracy"
    elif win_diff <= 0.20:
        return "Mistake"
    else:
        return "Blunder"


class GameAnalyzer:
    def __init__(self, depth: int = 12, max_time_per_move: float = 0.08, **kwargs):
        self.depth = depth
        self.max_time = max_time_per_move
        if not os.path.exists(STOCKFISH_PATH):
            raise FileNotFoundError(f"Stockfish not found at: {STOCKFISH_PATH}")
        self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        self.engine.configure({"Threads": 2, "Hash": 128})

    def close(self):
        try:
            self.engine.quit()
        except Exception:
            pass

    def analyze_game(self, game: chess.pgn.Game, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """Analyzes all moves with responsive progress updates."""
        board = game.board()
        moves_list = list(game.mainline_moves())
        total_moves = len(moves_list)

        move_analyses = []
        blunders = []

        move_num = 1
        is_white_turn = True

        for idx, move in enumerate(moves_list):
            if progress_callback:
                progress_callback(idx + 1, total_moves)

            fen_before = board.fen()
            
            # Fast & Accurate: stop at either depth 12 or 0.08 seconds (whichever is faster)
            limit = chess.engine.Limit(time=self.max_time, depth=self.depth)

            # Analyze candidate lines (MultiPV=3)
            info_before = self.engine.analyse(board, limit, multipv=3)

            top_plans = []
            for pv_item in info_before:
                pv = pv_item.get("pv", [])
                if pv:
                    cand_move = pv[0]
                    score_rel = pv_item["score"].relative.score(mate_score=10000) or 0
                    line_uci = " ".join([m.uci() for m in pv[:4]])
                    top_plans.append({
                        "move": board.san(cand_move),
                        "move_uci": cand_move.uci(),
                        "score_cp": score_rel,
                        "line": line_uci
                    })

            best_move = info_before[0]["pv"][0] if (info_before and info_before[0].get("pv")) else move
            best_move_san = board.san(best_move)
            best_score = info_before[0]["score"].relative.score(mate_score=10000) or 0
            best_win_pct = win_percentage(best_score)

            # Check for sacrifice
            is_capture = board.is_capture(move)
            piece_moved = board.piece_at(move.from_square)
            is_sacrifice = False
            if piece_moved and piece_moved.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN] and not is_capture:
                is_sacrifice = board.is_attacked_by(not board.turn, move.to_square)

            san_move = board.san(move)
            played_is_best = (move == best_move)

            # Make the move on the board
            board.push(move)
            fen_after = board.fen()

            # Analyze position AFTER the move
            if board.is_checkmate():
                played_score = 10000
            elif board.is_stalemate() or board.is_insufficient_material():
                played_score = 0
            else:
                info_after = self.engine.analyse(board, chess.engine.Limit(time=0.04, depth=10))
                played_score = -(info_after["score"].relative.score(mate_score=10000) or 0)

            played_win_pct = win_percentage(played_score)
            win_loss = max(0.0, best_win_pct - played_win_pct)
            classification = classify_move(win_loss, is_sacrifice, played_is_best)

            analysis_entry = {
                "move_no": move_num,
                "color": "White" if is_white_turn else "Black",
                "played_move": san_move,
                "best_move": best_move_san,
                "eval_before": best_score,
                "eval_after": played_score,
                "win_loss": round(win_loss * 100, 1),
                "classification": classification,
                "fen_before": fen_before,
                "fen_after": fen_after,
                "top_plans": top_plans
            }
            move_analyses.append(analysis_entry)

            if classification in ["Blunder", "Mistake"]:
                blunders.append(analysis_entry)

            if not is_white_turn:
                move_num += 1
            is_white_turn = not is_white_turn

        return {
            "total_moves": len(move_analyses),
            "moves": move_analyses,
            "blunders": blunders
        }