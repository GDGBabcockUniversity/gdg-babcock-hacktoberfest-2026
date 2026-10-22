import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app.graders.base import Grader, GradingContext
from app.models import QuestionType

DATASET_PATH = Path(__file__).with_name("dataset.json")
DEFAULT_TOLERANCE = 0.1  # a grade "agrees" when it is within 10% of the question's max marks
EXACT_EPSILON = 0.01


@dataclass
class EvalCase:
    id: str
    question_type: QuestionType
    question: str
    max_marks: float
    response: str
    reference_score: float
    note: str
    correct_option: str | None = None
    model_answer: str | None = None
    rubric_points: list[dict] | None = None


@dataclass
class CaseResult:
    case: EvalCase
    score: float
    needs_review: bool
    feedback: str

    @property
    def difference(self) -> float:
        """AI score minus the reference score, in marks."""
        return self.score - self.case.reference_score


@dataclass
class Stats:
    count: int
    agreement_rate: float  # share of cases within the tolerance
    exact_rate: float  # share of cases with the same score
    mean_absolute_error: float  # average size of the gap, as a share of max marks
    bias: float  # average signed gap, as a share of max marks (positive means too generous)
    review_rate: float  # share of cases flagged needs_review


def load_cases(path: Path = DATASET_PATH) -> list[EvalCase]:
    """Read the dataset file and check it is well formed."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    questions = {question["id"]: question for question in data["questions"]}
    cases: list[EvalCase] = []
    seen: set[str] = set()
    for item in data["cases"]:
        if item["id"] in seen:
            raise ValueError(f"Duplicate case id: {item['id']}")
        seen.add(item["id"])
        if item["question"] not in questions:
            raise ValueError(f"Case {item['id']} uses an unknown question: {item['question']}")
        question = questions[item["question"]]
        reference = item["reference_score"]
        if not 0 <= reference <= question["max_marks"]:
            raise ValueError(f"Case {item['id']} has a reference score outside 0 to max marks.")
        cases.append(
            EvalCase(
                id=item["id"],
                question_type=QuestionType(question["question_type"]),
                question=question["question"],
                max_marks=question["max_marks"],
                response=item["response"],
                reference_score=reference,
                note=item["note"],
                correct_option=question.get("correct_option"),
                model_answer=question.get("model_answer"),
                rubric_points=question.get("rubric_points"),
            )
        )
    return cases


def run_cases(grader: Grader, cases: list[EvalCase]) -> list[CaseResult]:
    """Grade every case. Scores are clamped to 0..max marks, like the grading route does."""
    results = []
    for case in cases:
        proposal = grader.grade(
            GradingContext(
                question_type=case.question_type,
                question=case.question,
                response=case.response,
                max_marks=case.max_marks,
                correct_option=case.correct_option,
                model_answer=case.model_answer,
                rubric_points=case.rubric_points or [],
            )
        )
        score = min(max(proposal.score, 0), case.max_marks)
        results.append(CaseResult(case, score, proposal.needs_review, proposal.feedback))
    return results


def disagrees(result: CaseResult, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    return abs(result.difference) > tolerance * result.case.max_marks + 1e-9


def compute_stats(results: list[CaseResult], tolerance: float = DEFAULT_TOLERANCE) -> Stats:
    if not results:
        return Stats(0, 0.0, 0.0, 0.0, 0.0, 0.0)
    count = len(results)
    gaps = [result.difference / result.case.max_marks for result in results]
    return Stats(
        count=count,
        agreement_rate=sum(not disagrees(r, tolerance) for r in results) / count,
        exact_rate=sum(abs(r.difference) <= EXACT_EPSILON for r in results) / count,
        mean_absolute_error=sum(abs(gap) for gap in gaps) / count,
        bias=sum(gaps) / count,
        review_rate=sum(r.needs_review for r in results) / count,
    )


def _percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def _row(label: str, stats: Stats) -> str:
    return (
        f"| {label} | {stats.count} | {_percent(stats.agreement_rate)} | "
        f"{_percent(stats.exact_rate)} | {_percent(stats.mean_absolute_error)} | "
        f"{stats.bias * 100:+.0f}% | {_percent(stats.review_rate)} |"
    )


def format_report(
    results: list[CaseResult], grader_name: str, tolerance: float = DEFAULT_TOLERANCE
) -> str:
    lines = [
        "# Grader agreement report",
        "",
        f"Grader: {grader_name}",
        f"Cases: {len(results)} (synthetic, scored by hand)",
        f"Agreement tolerance: within {tolerance * 100:.0f}% of the question's max marks",
        "",
        "| Group | Cases | Agreement | Exact match | Mean error | Bias | Flagged for review |",
        "|---|---|---|---|---|---|---|",
        _row("All", compute_stats(results, tolerance)),
    ]
    for question_type in QuestionType:
        group = [r for r in results if r.case.question_type == question_type]
        if group:
            lines.append(_row(question_type.value, compute_stats(group, tolerance)))

    wrong = [r for r in results if disagrees(r, tolerance)]
    flagged = sum(r.needs_review for r in wrong)
    lines += [
        "",
        f"Disagreements: {len(wrong)} of {len(results)}, {flagged} of them flagged for review.",
    ]
    if wrong:
        lines += [
            "",
            "| Case | Reference | AI | Flagged | Why the reference is what it is |",
            "|---|---|---|---|---|",
        ]
        for r in wrong:
            lines.append(
                f"| {r.case.id} | {r.case.reference_score:g} | {r.score:g} | "
                f"{'yes' if r.needs_review else 'no'} | {r.case.note} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    from app.graders.factory import get_grader

    parser = argparse.ArgumentParser(description="Compare the configured grader with hand scores.")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                        help="share of max marks that still counts as agreement (default 0.1)")
    parser.add_argument("--output", type=Path, help="also write the report to this file")
    args = parser.parse_args(argv)

    grader = get_grader()
    report = format_report(run_cases(grader, load_cases()), type(grader).__name__, args.tolerance)
    print(report)
    if args.output:
        args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()