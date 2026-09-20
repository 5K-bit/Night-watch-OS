from __future__ import annotations

import pytest
from pydantic import ValidationError

from nightwatch.schemas import TaskIn


def test_task_title_is_trimmed() -> None:
    payload = TaskIn(title="  inspect OBEOS telemetry  ")
    assert payload.title == "inspect OBEOS telemetry"


def test_blank_task_title_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskIn(title="   \t\n  ")
