"""
Phase 9 — LLM Explanation Service

Builds on Phase 8's RAGPipeline, adding what a production UI actually needs:
  1. A tighter, word-limited prompt (Member 3 renders this directly in the UI)
  2. Different framing for exploitation vs. exploration recommendations
  3. Post-generation validation — catches the LLM stating a different-looking
     score despite being told not to
  4. A template-based fallback (no LLM, can't fail) for when the LLM call
     errors out or fails validation — a recommendation card should never go
     blank just because an API call timed out

RUN THIS LOCALLY (needs Phase 8's setup — OPENROUTER_API_KEY, Chroma, etc).

Usage:
    from explanation_service import ExplanationService

    service = ExplanationService()
    result = service.generate_explanation(
        food_id="x8l5__beef-gyro",
        ml_score=0.87,
        confidence_class="high",
        is_exploration=False,
    )
    print(result["explanation"], "| source:", result["source"])
"""

import re
import pandas as pd
from rag_pipeline import RAGPipeline

KNOWLEDGE_BASE_PATH = "food_knowledge_base.csv"


def validate_explanation(explanation: str, ml_score: float) -> bool:
    """
    Catches the LLM stating a DIFFERENT score-like number than the one it was
    given — e.g. "an 8/10 match" or "0.65 confidence" when ml_score was 0.87.
    This is a heuristic, not a perfect parser: it flags any decimal or
    fraction pattern that doesn't correspond to the actual score, erring
    toward being cautious (false positives just trigger the safe fallback,
    which is a fine trade — a false negative here would let a wrong number
    reach the user).
    """
    # Pattern 1: decimals like "0.65" or "0.87"
    decimals = re.findall(r"\b0\.\d{1,3}\b", explanation)
    for d in decimals:
        if abs(float(d) - ml_score) > 0.05:
            return False

    # Pattern 2: fractions like "8/10", "4/5"
    fractions = re.findall(r"\b(\d+)/(\d+)\b", explanation)
    for num, denom in fractions:
        implied_score = int(num) / int(denom)
        if abs(implied_score - ml_score) > 0.1:
            return False

    return True


def build_fallback_explanation(document: str, confidence_class: str, is_exploration: bool) -> str:
    """Pure-code fallback, no LLM — used when the LLM call fails or its
    output fails validation. Deliberately plain rather than trying to be
    clever, since reliability matters more than flair here."""
    name = document.split(" is ")[0] if " is " in document else document.split(".")[0]
    if is_exploration:
        return f"{name} — something a bit different worth trying, based on tastes similar to yours."
    conf_phrase = {
        "high": "a strong match for your taste",
        "medium": "a likely good fit",
        "low": "worth a try based on your preferences",
    }.get(confidence_class, "matched to your preferences")
    return f"{name} — {conf_phrase}."


class ExplanationService:
    def __init__(self):
        self.rag = RAGPipeline()
        kb = pd.read_csv(KNOWLEDGE_BASE_PATH, encoding="utf-8")
        self.knowledge_by_id = kb.set_index("food_id")["knowledge_document"].to_dict()

    def generate_explanation(self, food_id: str, ml_score: float,
                              confidence_class: str = "medium",
                              is_exploration: bool = False) -> dict:
        document = self.knowledge_by_id.get(food_id)
        if document is None:
            return {
                "food_id": food_id, "explanation": "No information available for this food.",
                "ml_score": ml_score, "source": "error", "validation_passed": False,
            }

        if is_exploration:
            framing = (
                "This is an EXPLORATION recommendation — the user hasn't shown a strong "
                "preference here yet, so frame it as something new/different worth trying, "
                "not a confident match."
            )
        else:
            framing = (
                "This is a high-confidence EXPLOITATION recommendation — frame it as "
                "matching the user's established taste."
            )

        system_prompt = (
            "You write ONE short sentence (max 20 words) explaining a food recommendation "
            "to a user in a mobile app. Use ONLY the facts given — never invent ingredients "
            "or nutrition claims. NEVER state any score, percentage, or rating number "
            "yourself — the app displays the score separately, your job is just the "
            "qualitative reason."
        )
        user_prompt = f"{framing}\n\nFood information: {document}\n\nWrite the one-sentence explanation."

        try:
            explanation = self.rag._call_llm(system_prompt, user_prompt)
        except Exception:
            explanation = None

        if explanation and validate_explanation(explanation, ml_score):
            source = "llm"
        else:
            explanation = build_fallback_explanation(document, confidence_class, is_exploration)
            source = "fallback_template"

        return {
            "food_id": food_id,
            "explanation": explanation,
            "ml_score": ml_score,
            "confidence_class": confidence_class,
            "is_exploration": is_exploration,
            "source": source,  # "llm" or "fallback_template" — useful for debugging/QA
        }


if __name__ == "__main__":
    service = ExplanationService()
    sample_food_id = next(iter(service.knowledge_by_id))

    print("=== Exploitation example ===")
    print(service.generate_explanation(sample_food_id, ml_score=0.91, confidence_class="high", is_exploration=False))

    print("\n=== Exploration example ===")
    print(service.generate_explanation(sample_food_id, ml_score=0.42, confidence_class="low", is_exploration=True))
