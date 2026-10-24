"""
Test Game Review Pipeline:
Parses a game, runs Stockfish MultiPV analysis, and generates GM coaching advice.
"""

from src.chess_fetcher import parse_pgn_to_game
from src.engine import GameAnalyzer
from src.coach import generate_coach_advice
from tabulate import tabulate

# A famous miniature game with a brilliant tactical blunder:
# Legal's Mate (De Kermur Sire de Legal vs Saint Brie)
SAMPLE_PGN = """
[Event "Paris"]
[Site "Paris FRA"]
[Date "1750.??.??"]
[White "Sire de Legal"]
[Black "Saint Brie"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 Bxd1 6. Bxf7+ Ke7 7. Nd5# 1-0
"""

def main():
    print("♟️  Loading PGN game...")
    game = parse_pgn_to_game(SAMPLE_PGN)

    print("🤖 Starting Stockfish 19 MultiPV analysis (Depth 14)...")
    analyzer = GameAnalyzer(depth=14)
    results = analyzer.analyze_game(game)
    analyzer.close()

    print(f"✓ Analyzed {results['total_moves']} moves!")
    print(f"✓ Found {len(results['blunders'])} critical blunders/turning points.")

    # 1. Print Move Classification Table
    table_rows = []
    for m in results["moves"]:
        table_rows.append([
            f"{m['move_no']}. {m['color']}",
            m["played_move"],
            m["classification"],
            m["best_move"],
            f"{m['eval_after']/100:+.2f}"
        ])

    print("\n" + "="*60)
    print("📊 FULL MOVE-BY-MOVE REVIEW")
    print("="*60)
    print(tabulate(table_rows, headers=["Turn", "Played", "Badge", "Best Move", "Eval"], tablefmt="github"))

    # 2. Test AI Coach on the biggest blunder in the game
    if results["blunders"]:
        biggest_blunder = results["blunders"][0]
        print("\n" + "="*60)
        print(f"🎓 AI GRANDMASTER COACH: Analyzing Blunder ({biggest_blunder['color']} played {biggest_blunder['played_move']})")
        print("="*60)
        
        advice = generate_coach_advice(biggest_blunder)
        print(f"❌ What Went Wrong:\n   {advice.get('what_went_wrong')}\n")
        print(f"💡 The Missed Plan:\n   {advice.get('the_missed_plan')}\n")
        print(f"🧠 Grandmaster Thought Process:\n   {advice.get('how_to_think')}\n")

if __name__ == "__main__":
    main()