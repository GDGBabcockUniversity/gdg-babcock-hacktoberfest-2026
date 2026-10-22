import math
import re
from collections.abc import Callable

import httpx

from app.config import get_settings
from app.graders.base import GradeProposal, GradingContext
from app.graders.objective import ObjectiveGrader

# An embed function takes a list of texts and returns one embedding (a list of numbers)
# per text, in the same order. Tests pass a fake one, so no model server is needed.
EmbedFn = Callable[[list[str]], list[list[float]]]

LOWER_THRESHOLD = 0.5
UPPER_THRESHOLD = 0.85


class EmbeddingError(Exception):
    """The model server failed, or returned embeddings that cannot be compared."""


def ollama_embed(texts: list[str]) -> list[list[float]]:
    """Get one embedding per text from Ollama."""
    settings = get_settings()
    try:
        reply = httpx.post(
            f"{settings.ollama_url}/api/embed",
            json={"model": settings.ollama_embedding_model, "input": texts},
            timeout=120,
        )
        reply.raise_for_status()
        return reply.json()["embeddings"]
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise EmbeddingError(str(error)) from error


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """How alike two embeddings point: 1 is identical meaning, 0 unrelated, -1 opposite."""
    if len(a) != len(b) or not a:
        raise EmbeddingError("Embeddings have different sizes or are empty.")
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        raise EmbeddingError("An embedding is all zeros, so it cannot be compared.")
    return sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _required_keywords(rubric_points: list[dict]) -> list[str]:
    """Every keyword from every rubric point, normalized, without duplicates."""
    seen: dict[str, None] = {}
    for point in rubric_points:
        for keyword in point.get("keywords") or []:
            cleaned = _normalize(keyword)
            if cleaned:
                seen.setdefault(cleaned)
    return list(seen)


def _contains_keyword(text: str, keyword: str) -> bool:
    """Whole word or phrase match, so "ion" does not match "ionic"."""
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


class SemanticGrader:
    """Grades short answers by meaning, using embeddings from Ollama.

    How a grade is worked out:
    - The model answer and the student's answer are both turned into embeddings, and their
      cosine similarity is measured.
    - Similarity below 0.5 scores zero. Similarity above 0.85 scores full marks.
    - From 0.5 to 0.85 the score rises in a straight line from zero to full marks.
    - Similarity from 0.5 to 0.85 (both ends included) is ambiguous, so the grade is flagged
      needs_review. Clear zeros and clear full marks are not.
    - Required keywords are every keyword on the question's rubric points. Matching ignores
      case and spacing and needs a whole word or phrase. The marks from similarity are
      multiplied by the share of required keywords found, so missing 1 of 4 keeps 75%.
      The feedback lists the missing keywords. With no keywords this step does nothing.
    - A blank answer scores 0 without calling the model.
    - A question with no model answer, or any embedding failure, scores 0 and is flagged
      needs_review.
    - Objective questions are handed to ObjectiveGrader.
    """

    def __init__(
        self,
        embed: EmbedFn = ollama_embed,
        lower: float = LOWER_THRESHOLD,
        upper: float = UPPER_THRESHOLD,
    ) -> None:
        self._embed = embed
        self._lower = lower
        self._upper = upper

    def grade(self, context: GradingContext) -> GradeProposal:
        if context.question_type.value == "objective":
            return ObjectiveGrader().grade(context)
        if not context.response.strip():
            return GradeProposal(0, "No answer was provided.")
        if not (context.model_answer or "").strip():
            return GradeProposal(
                0,
                "This question has no model answer and needs administrator review.",
                needs_review=True,
            )

        try:
            vectors = self._embed([context.model_answer, context.response])
            if len(vectors) != 2:
                raise EmbeddingError("Expected two embeddings.")
            similarity = cosine_similarity(vectors[0], vectors[1])
        except EmbeddingError:
            return GradeProposal(
                0,
                "The answer could not be compared by meaning and needs review.",
                needs_review=True,
            )

        fraction = self._fraction(similarity)
        feedback = f"Similarity to the model answer: {similarity:.2f}."

        keywords = _required_keywords(context.rubric_points)
        if keywords:
            text = _normalize(context.response)
            missing = [word for word in keywords if not _contains_keyword(text, word)]
            fraction *= (len(keywords) - len(missing)) / len(keywords)
            if missing:
                feedback += " Missing required keywords: " + ", ".join(missing) + "."

        return GradeProposal(
            score=round(min(fraction * context.max_marks, context.max_marks), 2),
            feedback=feedback,
            evidence=[context.response[:200]],
            needs_review=self._lower <= similarity <= self._upper,
        )

    def _fraction(self, similarity: float) -> float:
        """The share of full marks that a similarity earns, from 0 to 1."""
        if similarity < self._lower:
            return 0.0
        if similarity > self._upper:
            return 1.0
        return (similarity - self._lower) / (self._upper - self._lower)