# GDG Babcock Hacktoberfest 2026

## Hacktoberfest Open Source Contributions Welcome

Welcome to the GDG AI Grader project from GDG on Campus Babcock University!

This repository is part of our community's Hacktoberfest work. Whether this is your first open source contribution or you already have experience, you are welcome to learn, build, review, document, test, and contribute with us.

## About Hacktoberfest

Hacktoberfest is a global celebration of open source that runs throughout October. The 2026 program highlights hands-on learning, experimentation, and building with open-source AI and open-weight models. The format and participation details can change, so check the [official Hacktoberfest website](https://hacktoberfest.com/) and [FAQ](https://hacktoberfest.com/questions/) for the current guidance.

## About This Project

GDG AI Grader is an open-source exam grading assistant. It helps educators review AI-suggested grades and feedback; a human administrator remains responsible for every final grade.

The project includes a React frontend and a FastAPI backend. Contributions can improve the user experience, grading workflow, accessibility, tests, documentation, or support for open-weight models.

## How to Participate with GDG Babcock

1. Visit the [official Hacktoberfest website](https://hacktoberfest.com/) and review the current participation information.
2. Read the [Hacktoberfest FAQ](https://hacktoberfest.com/questions/) and this repository's [contributor guide](CONTRIBUTING.md).
3. Browse the [open issues](https://github.com/GDGBabcockUniversity/gdg-babcock-hacktoberfest-2026/issues) and choose a scoped task that interests you.
4. Comment on the issue and follow its assignment instructions before starting substantial work.
5. Make a focused contribution that meets the issue's acceptance criteria. Code, documentation, design, testing, research, and issue triage can all help the project.
6. Open a pull request that explains the change and links the issue. Follow the repository's review guidance and respond to maintainer feedback.
7. Check GDG Babcock announcements for participant forms, event details, and community updates when they are published.

Please follow the current official Hacktoberfest participation format. Contributions to this repository are welcome as community project work; do not assume a pull request automatically counts toward an official Hacktoberfest milestone.

## Project Setup

### Docker Compose

Prerequisite: Docker with the Compose plugin.

From the repository root, create a local environment file and set private development credentials:

```bash
cp .env.example .env
```

Then start the application:

```bash
docker compose up --build
```

Open the frontend at [http://localhost:5173](http://localhost:5173). The FastAPI documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Mock grading is enabled by default and does not require a model server. To start the optional Ollama service:

```bash
docker compose --profile ollama up --build
```

### Frontend only

Prerequisite: Node.js and npm. From `frontend/`:

```bash
npm install
npm run dev
```

For a production build, run `npm run build` from the same directory.

### Backend only

Prerequisite: Python 3.12 or newer. From `backend/`, create and activate a virtual environment, install the dependencies, then run the API:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend reads its settings from environment variables. For the complete local workflow, use Docker Compose from the repository root, which supplies the database URL and development settings.

## Repositories to Contribute To

- [GDG AI Grader](https://github.com/GDGBabcockUniversity/gdg-babcock-hacktoberfest-2026): the project in this repository.
- More GDG Babcock community projects may be announced during the event.

## Safety and Review

- Use fictional exam and student data only. Never commit real student answers or credentials.
- Public registration creates learner accounts. Local Compose setup seeds a development superadmin; change the example credentials before sharing an environment.
- Treat every AI grade as a suggestion for an administrator to review.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for pull request and development guidance.
