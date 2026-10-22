import math

import httpx
import pytest

from app.graders import semantic
from app.graders.base import GradingContext
from app.graders.semantic import EmbeddingError, SemanticGrader, cosine_similarity
from app.models import QuestionType

MAX_MARKS = 4
MODEL_ANSWER = "Water boils at 100 degrees Celsius at sea level."
ANSWER = "At sea level, water boils at 100 degrees Celsius."


def with_similarity(similarity):
    """A pair of embeddings whose cosine similarity is exactly the number given."""
    return [[1.0, 0.0], [similarity, math.sqrt(1 - similarity**2)]]


class FakeEmbed:
    """Returns scripted embeddings and records every request."""

    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, texts):
        self.calls.append(texts)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def grade(embed, response=ANSWER, model_answer=MODEL_ANSWER, points=(), question_type=None):
    context = GradingContext(
        question_type=question_type or QuestionType.short,
        question="At what temperature does water boil?",
        response=response,
        max_marks=MAX_MARKS,
        model_answer=model_answer,
        rubric_points=list(points),
    )
    return SemanticGrader(embed=embed).grade(context)


def points(*keyword_lists):
    return [{"description": "point", "marks": 1, "keywords": words} for words in keyword_lists]


def test_cosine_similarity_basics():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1)
    assert cosine_similarity([2, 0], [5, 0]) == pytest.approx(1)


@pytest.mark.parametrize("a, b", [([], []), ([1, 2], [1]), ([0, 0], [1, 1])])
def test_cosine_similarity_rejects_unusable_embeddings(a, b):
    with pytest.raises(EmbeddingError):
        cosine_similarity(a, b)


@pytest.mark.parametrize("similarity", [0.0, 0.3, 0.49])
def test_below_the_lower_threshold_scores_zero_without_review(similarity):
    proposal = grade(FakeEmbed(with_similarity(similarity)))
    assert proposal.score == 0
    assert proposal.needs_review is False


@pytest.mark.parametrize("similarity", [0.86, 0.9, 1.0])
def test_above_the_upper_threshold_scores_full_marks_without_review(similarity):
    proposal = grade(FakeEmbed(with_similarity(similarity)))
    assert proposal.score == MAX_MARKS
    assert proposal.needs_review is False


@pytest.mark.parametrize(
    "similarity, expected",
    [(0.5, 0), (0.675, 2), (0.85, 4), (0.6, 1.14), (0.8, 3.43)],
)
def test_between_the_thresholds_scales_linearly_and_needs_review(similarity, expected):
    proposal = grade(FakeEmbed(with_similarity(similarity)))
    assert proposal.score == pytest.approx(expected, abs=0.01)
    assert proposal.needs_review is True


def test_feedback_reports_the_similarity():
    proposal = grade(FakeEmbed(with_similarity(0.9)))
    assert proposal.feedback == "Similarity to the model answer: 0.90."


def test_both_texts_are_embedded_in_one_request():
    embed = FakeEmbed(with_similarity(0.9))
    grade(embed)
    assert embed.calls == [[MODEL_ANSWER, ANSWER]]


def test_all_keywords_present_changes_nothing():
    proposal = grade(FakeEmbed(with_similarity(0.9)), points=points(["water", "boils"]))
    assert proposal.score == MAX_MARKS
    assert "Missing" not in proposal.feedback


def test_missing_keywords_reduce_marks_by_the_share_found():
    proposal = grade(
        FakeEmbed(with_similarity(0.9)),
        response="The water is hot.",
        points=points(["water", "boils", "celsius", "100"]),
    )
    assert proposal.score == pytest.approx(MAX_MARKS * 1 / 4)
    assert proposal.feedback.endswith("Missing required keywords: boils, celsius, 100.")


def test_keywords_ignore_case_and_spacing():
    proposal = grade(
        FakeEmbed(with_similarity(0.9)),
        response="WATER   BOILS at sea level",
        points=points(["water boils"]),
    )
    assert proposal.score == MAX_MARKS


def test_keywords_must_be_whole_words():
    proposal = grade(
        FakeEmbed(with_similarity(0.9)),
        response="It is an ionic bond.",
        points=points(["ion"]),
    )
    assert proposal.score == 0


def test_keywords_are_collected_across_points_without_duplicates():
    proposal = grade(
        FakeEmbed(with_similarity(0.9)),
        response="Water boils.",
        points=points(["water", "Boils"], ["WATER", "celsius"]),
    )
    # Three distinct keywords (water, boils, celsius), two found.
    assert proposal.score == pytest.approx(MAX_MARKS * 2 / 3, abs=0.01)


def test_keywords_cannot_rescue_a_low_similarity():
    proposal = grade(FakeEmbed(with_similarity(0.2)), points=points(["water"]))
    assert proposal.score == 0


def test_blank_answer_scores_zero_without_calling_the_model():
    embed = FakeEmbed(with_similarity(0.9))
    proposal = grade(embed, response="   ")
    assert proposal.score == 0
    assert proposal.feedback == "No answer was provided."
    assert embed.calls == []


@pytest.mark.parametrize("model_answer", [None, "", "   "])
def test_missing_model_answer_is_flagged_for_review(model_answer):
    embed = FakeEmbed(with_similarity(0.9))
    proposal = grade(embed, model_answer=model_answer)
    assert proposal.score == 0
    assert proposal.needs_review is True
    assert embed.calls == []


@pytest.mark.parametrize(
    "result",
    [
        EmbeddingError("server down"),
        [[1.0, 0.0]],
        [[1.0, 0.0], [1.0]],
        [[0.0, 0.0], [1.0, 0.0]],
    ],
)
def test_embedding_problems_score_zero_and_flag_review(result):
    proposal = grade(FakeEmbed(result))
    assert proposal.score == 0
    assert proposal.needs_review is True


def test_objective_questions_go_to_the_objective_grader():
    embed = FakeEmbed(with_similarity(0.9))
    context = GradingContext(
        question_type=QuestionType.objective,
        question="Pick one.",
        response="b",
        max_marks=1,
        correct_option="B",
    )
    assert SemanticGrader(embed=embed).grade(context).score == 1
    assert embed.calls == []


def test_ollama_embed_returns_the_embeddings(monkeypatch):
    sent = {}

    def fake_post(url, json, timeout):
        sent["url"], sent["json"] = url, json
        return httpx.Response(200, json={"embeddings": [[1.0, 2.0], [3.0, 4.0]]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(semantic.httpx, "post", fake_post)
    assert semantic.ollama_embed(["a", "b"]) == [[1.0, 2.0], [3.0, 4.0]]
    assert sent["url"].endswith("/api/embed")
    assert sent["json"]["input"] == ["a", "b"]


@pytest.mark.parametrize("failure", ["http_error", "bad_body"])
def test_ollama_embed_wraps_failures(monkeypatch, failure):
    def fake_post(url, json, timeout):
        request = httpx.Request("POST", url)
        if failure == "http_error":
            raise httpx.ConnectError("refused", request=request)
        return httpx.Response(200, json={"oops": 1}, request=request)

    monkeypatch.setattr(semantic.httpx, "post", fake_post)
    with pytest.raises(EmbeddingError):
        semantic.ollama_embed(["a", "b"])