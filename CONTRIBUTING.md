# Contributing

Thanks for helping build the GDG AI Grader. The project is early, so start with an issue and agree on the approach before opening a pull request.

## Development

1. Copy `.env.example` to `.env` and set a private `SECRET_KEY` and superadmin password.
2. Run `docker compose up --build` from the repository root. The API is at `http://localhost:8000`; its OpenAPI page is at `/docs`, and the frontend is at `http://localhost:5173`.
3. Mock grading is enabled by default and does not require a model download. Ollama is an optional Compose profile: `docker compose --profile ollama up --build`.

## Pull requests

- Link an assigned issue in every pull request.
- Keep changes focused and include tests for behavior changes.
- Use fake exam and student data only. Never commit real student answers or credentials.
- Treat every AI grade as a suggestion for an administrator to review.

## Roles

Public registration always creates a `user`. The first superadmin is seeded from `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD`; never expose those credentials outside local development.

