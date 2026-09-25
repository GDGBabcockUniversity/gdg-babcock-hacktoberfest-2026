from app.graders.base import GradeProposal, GradingContext


class ObjectiveGrader:
    def grade(self, context: GradingContext) -> GradeProposal:
        correct = (context.correct_option or "").strip().casefold()
        response = context.response.strip().casefold()
        matched = bool(correct) and response == correct
        return GradeProposal(
            score=context.max_marks if matched else 0,
            feedback="Correct answer." if matched else "The answer does not match the answer key.",
            evidence=[context.response] if matched else [],
        )

