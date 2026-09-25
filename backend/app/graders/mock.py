from app.graders.base import GradeProposal, GradingContext


class MockGrader:
    """Stable, deterministic fake grades for local development and UI work."""

    def grade(self, context: GradingContext) -> GradeProposal:
        if context.question_type.value == "objective":
            from app.graders.objective import ObjectiveGrader

            return ObjectiveGrader().grade(context)
        if not context.response.strip():
            return GradeProposal(0, "No answer was provided.")
        score = round(context.max_marks * 0.7, 2)
        return GradeProposal(
            score=score,
            feedback="Mock grade: a sample score for interface development; review before publishing.",
            evidence=[context.response[:200]],
            needs_review=True,
        )

