from typing import Annotated
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select

from app.dependencies import SessionDep, get_current_user, require_roles
from app.models import Answer, Exam, ExamStatus, Question, Submission, User, Exam, Role
from app.schemas import SubmissionInput, SubmissionListItem, SubmissionListResponse

AdminDep = Annotated[User, Depends(require_roles(Role.admin, Role.superadmin)),]

router = APIRouter(tags=["submissions"])


@router.post("/exams/{exam_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_exam(exam_id: int, payload: SubmissionInput, session: SessionDep, user: Annotated[User, Depends(get_current_user)]):
    
    exam = session.get(Exam, exam_id)
    if exam is None or exam.status != ExamStatus.open:
        raise HTTPException(status_code=404, detail="Open exam not found")
    submitted_ids = [answer.question_id for answer in payload.answers]
    if len(submitted_ids) != len(set(submitted_ids)):
        raise HTTPException(status_code=422, detail="Each question can only be answered once")
    valid_ids = set(session.exec(select(Question.id).where(Question.exam_id == exam_id)).all())
    if any(question_id not in valid_ids for question_id in submitted_ids):
        raise HTTPException(status_code=422, detail="Answer contains a question outside this exam")
    submission = Submission(exam_id=exam_id, user_id=user.id)
    session.add(submission)
    session.flush()
    for answer in payload.answers:
        session.add(Answer(submission_id=submission.id, **answer.model_dump()))
    session.commit()
    session.refresh(submission)
    return {"id": submission.id, "exam_id": exam_id, "status": submission.status}

@router.get(
    "/submissions",
    response_model=SubmissionListResponse,
    summary="List learner submissions",
    description="Admin-only endpoint for reviewing learner submissions.",
    status_code=status.HTTP_200_OK,
)
def list_submissions(
    session: SessionDep, 
    Admin: AdminDep,
    exam_id: int | None = Query(default=None, description="Filter submissions by exam ID"),
    submission_status: str | None = Query(default=None, alias="status", description="Filter submissions by status..."),
    page: int = Query(default=1, ge=1, description="Page number, starts at 1."),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of submissions per page. Max is 100."),
):
   
    filters = []
    if exam_id is not None:
        filters.append(Submission.exam_id == exam_id)
    if submission_status is not None:
        filters.append(Submission.status == submission_status)

    count_statement = select(func.count(Submission.id)).where(*filters)
    total = session.exec(count_statement).one()

    statement = (
        select(
            Submission,
            User,
            Exam,
            func.count(distinct(Answer.id)).label("total_answers"),
            func.count(distinct(Grade.id)).label("graded_answers"),
            func.coalesce(
               func.sum(case({Grade.needs_review == True: 1}, else_=0)), 
                0
            ).label("needs_review"),
        )
        .join(User, Submission.user_id == User.id)
        .join(Exam, Submission.exam_id == Exam.id)
        .outerjoin(Answer, Answer.submission_id == Submission.id)
        .outerjoin(Grade, Grade.answer_id == Answer.id)
        .where(*filters)
        .group_by(Submission.id, User.id, Exam.id)
    )

    offset = (page - 1) * page_size
    rows = session.exec(
        statement
        .order_by(Submission.submitted_at.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    items = [
        SubmissionListItem(
            submission_id=submission.id,
            learner_id=learner.id,
            learner_email=learner.email,
            exam_id=exam.id,
            exam_title=exam.title,
            status=submission.status,
            submitted_at=submission.submitted_at.isoformat(),
            total_answers=total_answers,
            graded_answers=graded_answers,
            needs_review=needs_review,
        )
        for (submission, learner, exam, total_answers, graded_answers, needs_review) in rows
    ]

    total_pages = ceil(total / page_size) if total else 0

    return SubmissionListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )