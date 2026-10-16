import pytest

from app.graders.base import GradingContext
from app.graders.objective import ObjectiveGrader
from app.models import QuestionType

MAX_MARKS = 2


def grade(response, correct):
    context = GradingContext(
        question_type=QuestionType.objective,
        question="Sample question?",
        response=response,
        max_marks=MAX_MARKS,
        correct_option=correct,
    )
    return ObjectiveGrader().grade(context)


def test_correct_answer_gets_full_marks():
    proposal = grade("B", "B")
    assert proposal.score == MAX_MARKS
    assert proposal.feedback == "Correct answer."
    assert proposal.needs_review is False


def test_incorrect_answer_gets_zero():
    proposal = grade("C", "B")
    assert proposal.score == 0
    assert proposal.feedback == "The answer does not match the answer key."


@pytest.mark.parametrize("response", ["", "   ", "\n\t"])
def test_blank_response_gets_zero_with_its_own_feedback(response):
    proposal = grade(response, "B")
    assert proposal.score == 0
    assert proposal.feedback == "No answer was provided."


@pytest.mark.parametrize("response", ["b", "B", " b ", "\tB\n"])
def test_case_and_outer_whitespace_are_ignored(response):
    assert grade(response, "B").score == MAX_MARKS


def test_inner_whitespace_is_collapsed():
    assert grade("new   york", "New York").score == MAX_MARKS


def test_other_punctuation_is_not_ignored():
    assert grade("B.", "B").score == 0


@pytest.mark.parametrize("response", ["A,B", "B,A", "a , b", " B, A "])
def test_multi_select_ignores_order_case_and_spacing(response):
    assert grade(response, "A, B").score == MAX_MARKS


@pytest.mark.parametrize("response", ["A", "A,B,C", "A,C"])
def test_multi_select_is_all_or_nothing(response):
    assert grade(response, "A,B").score == 0


def test_duplicate_selections_are_ignored():
    assert grade("A,A,B", "A,B").score == MAX_MARKS


@pytest.mark.parametrize("correct", [None, "", "   "])
def test_missing_answer_key_is_flagged_for_review(correct):
    proposal = grade("B", correct)
    assert proposal.score == 0
    assert proposal.needs_review is True