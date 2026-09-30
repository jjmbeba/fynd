"""Write the FastAPI OpenAPI document for the frontend generator."""

import json
import sys
from pathlib import Path
from typing import cast

from pydantic import AnyUrl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import Settings
from main import create_app


def main() -> None:
    app = create_app(
        Settings(
            database_url=cast(AnyUrl, "sqlite+aiosqlite:///./fynd.db"),
            environment="test",
        )
    )
    target = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"
    target.write_text(json.dumps(app.openapi(), indent=2) + "\n")


if __name__ == "__main__":
    main()
