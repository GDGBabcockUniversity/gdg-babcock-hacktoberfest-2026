from app.config import get_settings
from app.graders.base import Grader
from app.graders.mock import MockGrader
from app.graders.rubric import RubricGrader


def get_grader() -> Grader:
    mode = get_settings().grader_mode.casefold()
    if mode == "mock":
        return MockGrader()
    if mode == "ollama":
        return RubricGrader()
    raise RuntimeError(f"Unsupported GRADER_MODE={mode!r}; use 'mock' or 'ollama'")