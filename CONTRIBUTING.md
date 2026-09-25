# Contributing to GDG AI Grader

Thanks for helping build the GDG Babcock Hacktoberfest project. The codebase is intentionally approachable so a contributor can choose one boundary, make a focused change, and understand its effect. Contributions can improve the application code, user experience, tests, documentation, accessibility, or grading workflow.

## 1. Fork and clone

1. Open the [project repository](https://github.com/GDGBabcockUniversity/gdg-babcock-hacktoberfest-2026) on GitHub and select **Fork**.
2. Clone your fork and enter the project:

   ```bash
   git clone https://github.com/YOUR-USERNAME/gdg-babcock-hacktoberfest-2026.git
   cd gdg-babcock-hacktoberfest-2026
   ```

3. Add the original repository as `upstream`:

   ```bash
   git remote add upstream https://github.com/GDGBabcockUniversity/gdg-babcock-hacktoberfest-2026.git
   ```

4. For the Docker Compose workflow, copy the development environment file and replace the example secrets:

   ```bash
   cp .env.example .env
   ```

Never commit `.env`, tokens, credentials, or machine-specific settings.

## 2. Backend setup

Use Python 3.12, matching the Docker image. Create a virtual environment and install the backend dependencies:

```bash
cd backend
cp ../.env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The API runs at <http://localhost:8000>; interactive API docs are at <http://localhost:8000/docs>.

## 3. Frontend setup

Use Node.js 20 or newer in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Create a production build with `npm run build` from `frontend/`.

## 4. Run the full application

Docker Compose starts the backend and frontend together. From the repository root:

```bash
docker compose up --build
```

The frontend is at <http://localhost:5173> and API docs are at <http://localhost:8000/docs>. Compose uses a local SQLite database and seeds a development superadmin from `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`. Change the example credentials before sharing an environment.

## 5. Grading mode

The default `GRADER_MODE=mock` works without a model server. The current grader factory only supports mock mode; model-backed grading is planned contributor work. The optional Ollama Compose profile can start an Ollama service, but the current application does not call it yet.

Every grade is a proposal for administrator review. The application must not publish an AI-suggested grade as final without human approval.

## 6. Understand the application

The backend is a FastAPI application assembled in `backend/app/main.py`. SQLModel entities are in `backend/app/models/entities.py`, request and response schemas are in `backend/app/schemas.py`, and API routes are grouped under `backend/app/routers/`:

- `auth.py` handles registration and login.
- `exams.py` handles exam and question workflows.
- `submissions.py` accepts learner answers.
- `grades.py` handles grade proposals and administrator review.
- `results.py` serves learner results.
- `admin.py` manages administrator accounts.

The frontend is a Vite and React app under `frontend/src/`. Keep components and page behavior focused as routes and workflows are added.

## 7. Grader implementations

The grader interface lives in `backend/app/graders/base.py`. `GradingContext` carries the question and answer data, `GradeProposal` represents a suggested score and feedback, and the `Grader` protocol defines the grading boundary. Implementations and selection logic live in the same directory; `factory.py` currently returns `MockGrader`.

A new grader should implement the protocol, return a proposal that stays within the question's mark limit, and identify ambiguous results for human review. Keep external model calls behind this interface so the rest of the application can use mock mode in local development and tests.

## 8. Add or change an API route

Put route handlers in the matching module under `backend/app/routers/`, define or update payloads in `backend/app/schemas.py`, and register new routers in `backend/app/main.py`. Use the existing authentication and role dependencies for protected operations. Check the generated OpenAPI docs at `/docs` to confirm the API contract.

## 9. Data and privacy

Use fictional exams, learners, and answers in examples and development data. Never commit real student submissions, grades, credentials, or other private information. Public registration always creates a `user`; privileged roles must only be assigned through authorized administrative workflows.

## 10. Run checks

Backend syntax check, from `backend/`:

```bash
python3 -m compileall -q app
```

Frontend production build, from `frontend/`:

```bash
npm run build
```

When adding behavior, include focused tests with the change. Tests should use fabricated data and must not require live model services or real student submissions.

## 11. Branch naming

Create a branch from an up-to-date `main`:

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
git switch -c feat/exam-list-page
```

Use `feat/short-name`, `fix/short-name`, `docs/short-name`, or `test/short-name`. Keep one issue per branch.

## 12. Commit conventions

Use a short imperative Conventional Commit message:

```text
feat: add exam list page
fix: reject scores above the question limit
docs: clarify local backend setup
test: cover objective grading edge cases
```

Keep commits reviewable. Avoid unrelated formatting or dependency changes.

## 13. Claim an issue

Comment on an issue before starting and briefly describe your intended approach. Wait for a maintainer to assign it when the issue requires assignment. Ask questions on the issue so the answers help future contributors. If you can no longer work on it, leave a comment so it can be reassigned.

Choose an issue that fits your experience. Keep `good first issue` contributions small and propose a follow-up issue if the solution grows beyond its acceptance criteria. Follow the current [Hacktoberfest participation guidance](https://hacktoberfest.com/questions/) rather than assuming every pull request counts toward an event milestone.

## 14. Pull request requirements

Before opening a pull request:

- link the issue with `Closes #NUMBER`;
- explain what changed and why;
- include manual verification steps and report the checks you ran;
- add or update focused tests for behavior changes;
- update setup documentation when commands or environment variables change;
- include a screenshot for visible UI changes;
- keep generated files, model weights, secrets, and unrelated changes out of the pull request.

Keep pull requests focused and respond constructively to maintainer feedback. Use fabricated data only, and preserve human review for all AI-suggested grades.
