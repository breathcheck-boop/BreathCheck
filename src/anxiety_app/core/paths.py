from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir


def get_app_data_dir(app_name: str) -> Path:
    path = Path(user_data_dir(app_name, "BreathCheck"))
    path.mkdir(parents=True, exist_ok=True)
    return path
