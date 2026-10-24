"""
AI Grandmaster Coach via Groq API.
Translates Stockfish calculations into clear, strategic lessons and plans.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

COACH_PROMPT_TEMPLATE = """
You are a charismatic, world-class Chess Grandmaster and coach (in the style of Peter Svidler and Daniel Naroditsky).
Analyze this critical turning point from an amateur's game:

- Player: {color}
- Move Played: {played_move}
- Resulting Verdict: {classification} (Win chance dropped by {win_loss}%)
- Engine's Best Move: {best_move}
- Top 3 Plans Stockfish Considered:
{plans_text}

Provide an insightful, encouraging coaching breakdown in JSON strictly matching this schema:
{{
  "what_went_wrong": "1-2 sentences explaining what tactical trap or strategic error the player committed.",
  "the_missed_plan": "1-2 sentences explaining the idea/plan behind the best move ({best_move}) and why it works.",
  "how_to_think": "A golden rule or mental checklist for the player to spot this in future games."
}}
"""

def generate_coach_advice(blunder_item: dict) -> dict:
    """Calls Groq to generate Grandmaster explanations for a blunder or mistake."""
    if not GROQ_API_KEY:
        return {
            "what_went_wrong": "Missing GROQ_API_KEY in .env.",
            "the_missed_plan": f"The engine recommended {blunder_item['best_move']}.",
            "how_to_think": "Always calculate checks, captures, and threats."
        }

    client = Groq(api_key=GROQ_API_KEY)

    # Format the top plans
    plans_text = ""
    for idx, p in enumerate(blunder_item.get("top_plans", []), start=1):
        plans_text += f"  Plan {idx}: {p['move']} (Eval: {p['score_cp']/100:+.2f}) -> Line: {p['line']}\n"

    prompt = COACH_PROMPT_TEMPLATE.format(
        color=blunder_item["color"],
        played_move=blunder_item["played_move"],
        classification=blunder_item["classification"],
        win_loss=blunder_item["win_loss"],
        best_move=blunder_item["best_move"],
        plans_text=plans_text
    )

    # Active Groq models in order of quality
    candidate_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]

    for model_name in candidate_models:
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized chess analysis engine. Output only valid raw JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                model=model_name,
                response_format={"type": "json_object"},
                temperature=0.3
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except Exception:
            continue

    return {
        "what_went_wrong": "Could not contact AI coach model.",
        "the_missed_plan": f"Recommended move was {blunder_item['best_move']}.",
        "how_to_think": "Calculate checks, captures, and threats."
    }