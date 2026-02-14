from __future__ import annotations

from dataclasses import dataclass

from PyQt5.QtCore import QSettings


@dataclass(frozen=True)
class AppearanceSettings:
    mode: str  # "light" or "dark"
    comfort: bool
    font_size: str  # "small", "medium", "large"
    window_size: str  # "compact", "standard", "maximized"


def load_appearance_settings() -> AppearanceSettings:
    settings = QSettings()
    mode = settings.value("appearance/mode", "light")
    comfort = settings.value("appearance/comfort", False, type=bool)
    font_size = settings.value("appearance/font_size", "medium")
    window_size = settings.value("appearance/window_size", "maximized")
    mode = str(mode).lower() if mode else "light"
    font_size = str(font_size).lower() if font_size else "medium"
    window_size = str(window_size).lower() if window_size else "maximized"
    if mode not in {"light", "dark"}:
        mode = "light"
    if font_size not in {"small", "medium", "large"}:
        font_size = "medium"
    if window_size not in {"compact", "standard", "maximized"}:
        window_size = "maximized"
    return AppearanceSettings(
        mode=mode, comfort=bool(comfort), font_size=font_size, window_size=window_size
    )


def save_appearance_settings(settings_obj: AppearanceSettings) -> None:
    settings = QSettings()
    settings.setValue("appearance/mode", settings_obj.mode)
    settings.setValue("appearance/comfort", settings_obj.comfort)
    settings.setValue("appearance/font_size", settings_obj.font_size)
    settings.setValue("appearance/window_size", settings_obj.window_size)
