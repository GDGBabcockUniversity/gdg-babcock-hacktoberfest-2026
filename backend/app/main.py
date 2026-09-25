from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.auth import hash_password
from app.config import get_settings
from app.database import create_db_and_tables, engine
from app.models import Role, User
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.exams import router as exams_router
from app.routers.grades import router as grades_router
from app.routers.results import router as results_router
from app.routers.submissions import router as submissions_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    settings = get_settings()
    if settings.seed_admin_email and settings.seed_admin_password:
        with Session(engine) as session:
            email = settings.seed_admin_email.lower()
            if session.exec(select(User).where(User.email == email)).first() is None:
                session.add(User(email=email, password_hash=hash_password(settings.seed_admin_password), role=Role.superadmin))
                session.commit()
    yield


app = FastAPI(title=get_settings().app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(exams_router)
app.include_router(submissions_router)
app.include_router(grades_router)
app.include_router(results_router)
app.include_router(admin_router)
