from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from anxiety_app.core.paths import get_app_data_dir

def _resolve_db_path(raw_path: str, app_name: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = get_app_data_dir(app_name) / path
    return path


@dataclass(frozen=True)
class AppConfig:
    app_name: str
    debug: bool
    db_path: Path
    ai_api_key_env: str
    ai_model: str


def load_config() -> AppConfig:
    load_dotenv()
    app_name = os.getenv("APP_NAME", "BreathCheck")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    db_path = _resolve_db_path(os.getenv("DB_PATH", "breathcheck.db"), app_name)
    ai_api_key_env = os.getenv("AI_API_KEY", "")
    ai_model = os.getenv("AI_MODEL", "gpt-5.2")
    return AppConfig(
        app_name=app_name,
        debug=debug,
        db_path=db_path,
        ai_api_key_env=ai_api_key_env,
        ai_model=ai_model,
    )
