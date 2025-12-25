from __future__ import annotations

import os
from pathlib import Path


def _default_data_dir() -> Path:
    # Linux-first local app convention
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "nightwatch"
    return Path.home() / ".local" / "share" / "nightwatch"


DATA_DIR = Path(os.environ.get("NIGHTWATCH_DATA_DIR", str(_default_data_dir()))).expanduser()
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.environ.get("NIGHTWATCH_DB_PATH", str(DATA_DIR / "nightwatch.db"))).expanduser()

HOST = os.environ.get("NIGHTWATCH_HOST", "127.0.0.1")
PORT = int(os.environ.get("NIGHTWATCH_PORT", "8037"))

