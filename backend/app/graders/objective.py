from app.graders.base import GradeProposal, GradingContext


def _normalize(text: str) -> str:
    """Lowercase and collapse every run of whitespace into a single space."""
    return " ".join(text.casefold().split())


def _selections(text: str) -> frozenset[str]:
    """Split an answer on commas into an unordered set of normalized selections."""
    return frozenset(part for part in (_normalize(p) for p in text.split(",")) if part)


class ObjectiveGrader:
    """Grades objective questions deterministically against the answer key.

    Matching rules:
    - Case is ignored.
    - Leading, trailing and repeated inner whitespace is ignored.
    - Commas separate selections, so a multi-select answer is compared as an unordered
      set: "B, A" matches "A,B". Duplicate selections are ignored.
    - Marks are all or nothing: every selection must match, with none missing or extra.
    - Other punctuation is not ignored: "B." does not match "B".
    - A blank response scores 0 with its own feedback.
    - A question with no answer key scores 0 and is flagged for administrator review.
    """

    def grade(self, context: GradingContext) -> GradeProposal:
        key = _selections(context.correct_option or "")
        if not key:
            return GradeProposal(
                0,
                "This question has no answer key and needs administrator review.",
                needs_review=True,
            )
        selected = _selections(context.response)
        if not selected:
            return GradeProposal(0, "No answer was provided.")
        matched = selected == key
        return GradeProposal(
            score=context.max_marks if matched else 0,
            feedback="Correct answer." if matched else "The answer does not match the answer key.",
            evidence=[context.response] if matched else [],
        )