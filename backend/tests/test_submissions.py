import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.auth import create_access_token
from app.database import get_session
from app.main import app
from app.models import Answer, Exam, ExamStatus, Question, QuestionType, Role, Submission, User


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine):
    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_user(engine, email, role=Role.user, is_active=True):
    with Session(engine) as session:
        user = User(email=email, password_hash="fake-test-hash", role=role, is_active=is_active)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def add_exam(engine, creator, title="Sample exam", status=ExamStatus.open, questions=2):
    """Create an exam with the given number of short-answer questions. Returns the ids."""
    with Session(engine) as session:
        exam = Exam(title=title, duration_min=30, status=status, created_by=creator.id)
        session.add(exam)
        session.flush()
        question_ids = []
        for number in range(questions):
            question = Question(
                exam_id=exam.id,
                type=QuestionType.short,
                text=f"Question {number + 1}?",
                max_marks=2,
            )
            session.add(question)
            session.flush()
            question_ids.append(question.id)
        session.commit()
        return exam.id, question_ids


def auth(user):
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def answers(*pairs):
    return {"answers": [{"question_id": q, "response": r} for q, r in pairs]}


def rows(engine, model):
    with Session(engine) as session:
        return session.exec(select(model)).all()


@pytest.fixture
def setup(engine):
    admin = add_user(engine, "admin@example.test", Role.admin)
    learner = add_user(engine, "learner@example.test")
    exam_id, question_ids = add_exam(engine, admin)
    return learner, exam_id, question_ids


def test_a_valid_submission_is_saved(client, engine, setup):
    learner, exam_id, (q1, q2) = setup
    response = client.post(
        f"/exams/{exam_id}/submit",
        json=answers((q1, "first answer"), (q2, "second answer")),
        headers=auth(learner),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["exam_id"] == exam_id
    assert body["status"] == "submitted"
    (submission,) = rows(engine, Submission)
    assert submission.id == body["id"]
    saved = {a.question_id: a.response for a in rows(engine, Answer)}
    assert saved == {q1: "first answer", q2: "second answer"}


def test_the_submission_belongs_to_the_logged_in_user(client, engine, setup):
    learner, exam_id, (q1, _) = setup
    other = add_user(engine, "other@example.test")
    client.post(f"/exams/{exam_id}/submit", json=answers((q1, "mine")), headers=auth(learner))
    client.post(f"/exams/{exam_id}/submit", json=answers((q1, "theirs")), headers=auth(other))
    owners = {s.user_id for s in rows(engine, Submission)}
    assert owners == {learner.id, other.id}


@pytest.mark.parametrize("status", [ExamStatus.draft, ExamStatus.closed, ExamStatus.published])
def test_exams_that_are_not_open_reject_submissions(client, engine, setup, status):
    learner, _, _ = setup
    admin = add_user(engine, "second-admin@example.test", Role.admin)
    exam_id, (q1, _) = add_exam(engine, admin, status=status)
    response = client.post(
        f"/exams/{exam_id}/submit", json=answers((q1, "late")), headers=auth(learner)
    )
    assert response.status_code == 404
    assert rows(engine, Submission) == []
    assert rows(engine, Answer) == []


def test_an_unknown_exam_is_not_found(client, engine, setup):
    learner, _, (q1, _) = setup
    response = client.post("/exams/9999/submit", json=answers((q1, "a")), headers=auth(learner))
    assert response.status_code == 404
    assert rows(engine, Submission) == []


def test_a_question_cannot_be_answered_twice(client, engine, setup):
    learner, exam_id, (q1, _) = setup
    response = client.post(
        f"/exams/{exam_id}/submit",
        json=answers((q1, "first try"), (q1, "second try")),
        headers=auth(learner),
    )
    assert response.status_code == 422
    assert rows(engine, Submission) == []
    assert rows(engine, Answer) == []


def test_answers_must_belong_to_the_selected_exam(client, engine, setup):
    learner, exam_id, (q1, _) = setup
    admin = add_user(engine, "other-admin@example.test", Role.admin)
    _, (foreign_question, _) = add_exam(engine, admin, title="A different exam")
    response = client.post(
        f"/exams/{exam_id}/submit",
        json=answers((q1, "fine"), (foreign_question, "wrong exam")),
        headers=auth(learner),
    )
    assert response.status_code == 422
    assert rows(engine, Submission) == []
    assert rows(engine, Answer) == []


def test_an_unknown_question_is_rejected(client, engine, setup):
    learner, exam_id, _ = setup
    response = client.post(
        f"/exams/{exam_id}/submit", json=answers((9999, "a")), headers=auth(learner)
    )
    assert response.status_code == 422
    assert rows(engine, Submission) == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"answers": "not a list"},
        {"answers": [{"question_id": 1}]},
        {"answers": [{"response": "no question id"}]},
        {"answers": [{"question_id": "abc", "response": "a"}]},
    ],
)
def test_a_malformed_payload_is_rejected(client, engine, setup, payload):
    learner, exam_id, _ = setup
    response = client.post(f"/exams/{exam_id}/submit", json=payload, headers=auth(learner))
    assert response.status_code == 422
    assert rows(engine, Submission) == []


def test_submitting_needs_a_login(client, engine, setup):
    _, exam_id, (q1, _) = setup
    response = client.post(f"/exams/{exam_id}/submit", json=answers((q1, "a")))
    assert response.status_code in (401, 403)
    assert rows(engine, Submission) == []


def test_a_bad_token_is_rejected(client, engine, setup):
    _, exam_id, (q1, _) = setup
    response = client.post(
        f"/exams/{exam_id}/submit",
        json=answers((q1, "a")),
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401
    assert rows(engine, Submission) == []


def test_an_inactive_user_cannot_submit(client, engine, setup):
    _, exam_id, (q1, _) = setup
    inactive = add_user(engine, "inactive@example.test", is_active=False)
    response = client.post(
        f"/exams/{exam_id}/submit", json=answers((q1, "a")), headers=auth(inactive)
    )
    assert response.status_code == 401
    assert rows(engine, Submission) == []


def test_results_only_list_the_logged_in_users_own_submissions(client, engine, setup):
    learner, exam_id, (q1, _) = setup
    other = add_user(engine, "other@example.test")
    client.post(f"/exams/{exam_id}/submit", json=answers((q1, "mine")), headers=auth(learner))
    client.post(f"/exams/{exam_id}/submit", json=answers((q1, "theirs")), headers=auth(other))
    with Session(engine) as session:
        exam = session.get(Exam, exam_id)
        exam.status = ExamStatus.published
        session.add(exam)
        session.commit()

    mine = client.get("/me/results", headers=auth(learner)).json()
    assert len(mine) == 1
    assert [item["response"] for item in mine[0]["answers"]] == ["mine"]
    theirs = client.get("/me/results", headers=auth(other)).json()
    assert [item["response"] for item in theirs[0]["answers"]] == ["theirs"]