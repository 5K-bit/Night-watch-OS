from __future__ import annotations

import uvicorn

from nightwatch.app import create_app
from nightwatch.settings import HOST, PORT


def main() -> None:
    uvicorn.run(create_app(), host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()

