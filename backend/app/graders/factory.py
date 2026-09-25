from app.config import get_settings
from app.graders.base import Grader
from app.graders.mock import MockGrader


def get_grader() -> Grader:
    mode = get_settings().grader_mode.casefold()
    if mode == "mock":
        return MockGrader()
    raise RuntimeError(f"Unsupported GRADER_MODE={mode!r}; only mock mode is available in the MVP skeleton")

