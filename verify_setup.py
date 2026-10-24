"""
Verification Script:
1. Tests Stockfish engine connection via python-chess.
2. Tests fetching a live game from Chess.com public API.
"""

import os
import shutil
import chess
import chess.engine
import requests

def test_stockfish():
    print("🔍 Testing Stockfish...")
    
    # 1. Check local project bin/ folder first
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin", "stockfish"))
    if os.path.exists(local_path) and os.access(local_path, os.X_OK):
        stockfish_path = local_path
    else:
        # Fallback to system path
        stockfish_path = shutil.which("stockfish")

    if not stockfish_path:
        print("❌ Error: Stockfish not found at ./bin/stockfish or system PATH.")
        return False

    print(f"  ✓ Stockfish binary found at: {stockfish_path}")

    # Initialize engine and evaluate starting board
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        board = chess.Board()
        info = engine.analyse(board, chess.engine.Limit(depth=10))
        score = info["score"].relative.score(mate_score=10000)
        best_move = info["pv"][0] if "pv" in info else None
        print(f"  ✓ Engine working! Start position eval: {score} cp, Top move: {best_move}")
    return True


def test_chess_com_fetch():
    print("\n🔍 Testing Chess.com Game Fetcher...")
    sample_game_id = "105829182391"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    url = f"https://www.chess.com/callback/live/game/{sample_game_id}"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            game_data = data.get("game", {})
            pgn = game_data.get("pgn", "")
            white = game_data.get("user1", {}).get("username", "Unknown")
            black = game_data.get("user2", {}).get("username", "Unknown")
            print(f"  ✓ Chess.com API connected!")
            print(f"  ✓ Sample game fetched: {white} vs {black}")
            print(f"  ✓ Moves PGN length: {len(pgn)} characters")
            return True
        else:
            print(f"  ⚠ Failed to fetch: Status {res.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠ Network error: {e}")
        return False


if __name__ == "__main__":
    sf_ok = test_stockfish()
    cc_ok = test_chess_com_fetch()

    print("\n" + "="*50)
    if sf_ok and cc_ok:
        print("🎉 ALL SYSTEMS READY! We can build the analysis engine.")
    else:
        print("⚠️ Some setup checks failed. Please check the error above.")
    print("="*50)