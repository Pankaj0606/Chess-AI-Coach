# ♟️ AI Chess Coach & Free Game Review

An open-source, interactive Chess Game Review and Coaching web application powered by **Stockfish 19** and **Groq LLMs**. 

Instead of paying for premium Chess.com Diamond memberships, paste any Chess.com game link or PGN to receive:
- **Move-by-move classification:** 🟢 Best, 🔵 Excellent, 🟡 Inaccuracy, 🟠 Mistake, 🔴 Blunder, and 🟣 Brilliant moves.
- **Visual Board Arrows:** Green arrows for engine-recommended lines, Red arrows for tactical errors.
- **MultiPV = 3 Strategic Plans:** Explores the top 3 alternative continuations for any position so you learn *how to think* rather than just seeing a single move.
- **Grandmaster Coach Insights:** AI-generated pedagogical explanations highlighting missed plans, tactical traps, and mental checklists to remember.
- **Overall Game Accuracy:** Win-probability-based accuracy scores for both players.

---

## 🛠️ Tech Stack

- **Engine:** Stockfish 19 (UCI protocol via `python-chess`)
- **AI Explanations:** Groq API (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`)
- **Frontend / Dashboard:** Streamlit
- **Board Rendering:** Python `chess.svg` with native SVG vector rendering

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Pankaj0606/Chess-AI-Coach.git
cd Chess-AI-Coach