import json

import pytest

from app.evaluation import harness
from app.evaluation.harness import (
    CaseResult,
    EvalCase,
    compute_stats,
    disagrees,
    format_report,
    load_cases,
    run_cases,
)
from app.graders.base import GradeProposal
from app.graders.mock import MockGrader
from app.models import QuestionType


class FakeGrader:
    """Gives every answer the same proposal and records the contexts it was shown."""

    def __init__(self, score, needs_review=False):
        self.proposal = GradeProposal(score=score, feedback="fake", needs_review=needs_review)
        self.contexts = []

    def grade(self, context):
        self.contexts.append(context)
        return self.proposal


def make_case(reference=2, max_marks=4, case_id="c1", question_type=QuestionType.short):
    return EvalCase(
        id=case_id,
        question_type=question_type,
        question="Q?",
        max_marks=max_marks,
        response="answer",
        reference_score=reference,
        note="note",
    )


def make_result(
    reference, score, max_marks=10, needs_review=False, question_type=QuestionType.short
):
    case = make_case(reference, max_marks, question_type=question_type)
    return CaseResult(case, score, needs_review, "fake")


def write_dataset(path, questions, cases):
    path.write_text(json.dumps({"questions": questions, "cases": cases}), encoding="utf-8")
    return path


QUESTION = {"id": "q", "question_type": "short", "question": "Q?", "max_marks": 4}
CASE = {"id": "c1", "question": "q", "response": "a", "reference_score": 2, "note": "n"}


def test_bundled_dataset_has_thirty_cases_across_all_three_types():
    cases = load_cases()
    assert len(cases) == 30
    counts = {kind: sum(c.question_type == kind for c in cases) for kind in QuestionType}
    assert all(count > 0 for count in counts.values())


def test_bundled_dataset_is_well_formed():
    cases = load_cases()
    assert len({c.id for c in cases}) == len(cases)
    for case in cases:
        assert 0 <= case.reference_score <= case.max_marks
        if case.question_type == QuestionType.objective:
            assert case.correct_option
        else:
            assert case.model_answer
            assert sum(p["marks"] for p in case.rubric_points) == case.max_marks


def test_load_cases_rejects_duplicate_ids(tmp_path):
    path = write_dataset(tmp_path / "d.json", [QUESTION], [CASE, CASE])
    with pytest.raises(ValueError, match="Duplicate"):
        load_cases(path)


def test_load_cases_rejects_unknown_questions(tmp_path):
    path = write_dataset(tmp_path / "d.json", [QUESTION], [{**CASE, "question": "missing"}])
    with pytest.raises(ValueError, match="unknown question"):
        load_cases(path)


@pytest.mark.parametrize("reference", [-1, 5])
def test_load_cases_rejects_reference_scores_out_of_range(tmp_path, reference):
    path = write_dataset(tmp_path / "d.json", [QUESTION], [{**CASE, "reference_score": reference}])
    with pytest.raises(ValueError, match="outside"):
        load_cases(path)


def test_run_cases_passes_the_question_details_to_the_grader():
    grader = FakeGrader(score=1)
    run_cases(grader, load_cases())
    assert len(grader.contexts) == 30
    theory = next(c for c in grader.contexts if c.question_type == QuestionType.theory)
    assert theory.model_answer
    assert theory.rubric_points


@pytest.mark.parametrize("score, expected", [(99, 4), (-3, 0), (2.5, 2.5)])
def test_run_cases_keeps_scores_between_zero_and_max_marks(score, expected):
    results = run_cases(FakeGrader(score=score), [make_case(max_marks=4)])
    assert results[0].score == expected


def test_perfect_agreement():
    stats = compute_stats([make_result(5, 5), make_result(0, 0)])
    assert stats.count == 2
    assert stats.agreement_rate == 1
    assert stats.exact_rate == 1
    assert stats.mean_absolute_error == 0
    assert stats.bias == 0


def test_error_and_bias_are_shares_of_max_marks():
    stats = compute_stats([make_result(5, 8, max_marks=10), make_result(5, 4, max_marks=10)])
    assert stats.mean_absolute_error == pytest.approx(0.2)  # gaps of 30% and 10%
    assert stats.bias == pytest.approx(0.1)  # +30% and -10% average to +10%
    assert stats.exact_rate == 0


def test_the_tolerance_edge_counts_as_agreement():
    assert disagrees(make_result(5, 6, max_marks=10)) is False
    assert disagrees(make_result(5, 6.5, max_marks=10)) is True
    assert disagrees(make_result(5, 4, max_marks=10)) is False
    assert disagrees(make_result(5, 3.5, max_marks=10)) is True


def test_a_wider_tolerance_agrees_with_more_cases():
    results = [make_result(5, 7, max_marks=10)]
    assert compute_stats(results, tolerance=0.1).agreement_rate == 0
    assert compute_stats(results, tolerance=0.2).agreement_rate == 1


def test_review_rate_counts_flagged_cases():
    stats = compute_stats([make_result(5, 5, needs_review=True), make_result(5, 5)])
    assert stats.review_rate == 0.5


def test_no_results_gives_zeros():
    stats = compute_stats([])
    assert (stats.count, stats.agreement_rate, stats.mean_absolute_error) == (0, 0, 0)


def test_report_shows_groups_and_disagreements():
    results = [
        make_result(10, 10, question_type=QuestionType.objective),
        make_result(10, 0, needs_review=True, question_type=QuestionType.theory),
        make_result(10, 0, question_type=QuestionType.theory),
    ]
    report = format_report(results, "FakeGrader")
    assert "Grader: FakeGrader" in report
    assert "| All | 3 |" in report
    assert "| objective | 1 | 100% |" in report
    assert "| theory | 2 | 0% |" in report
    assert "| short |" not in report
    assert "Disagreements: 2 of 3, 1 of them flagged for review." in report


def test_report_with_full_agreement_has_no_disagreement_table():
    report = format_report([make_result(5, 5)], "FakeGrader")
    assert "Disagreements: 0 of 1, 0 of them flagged for review." in report
    assert "| Case |" not in report


def test_the_mock_grader_runs_over_the_whole_dataset():
    results = run_cases(MockGrader(), load_cases())
    assert len(results) == 30
    assert "Grader: MockGrader" in format_report(results, "MockGrader")


def test_command_line_prints_and_saves_the_report(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("app.graders.factory.get_grader", lambda: MockGrader())
    output = tmp_path / "report.md"
    harness.main(["--output", str(output)])
    assert "# Grader agreement report" in capsys.readouterr().out
    assert output.read_text(encoding="utf-8").startswith("# Grader agreement report")