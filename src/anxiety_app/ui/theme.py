from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from anxiety_app.core.preferences import AppearanceSettings


_FONT_SCALES = {
    "small": 0.9,
    "medium": 1.0,
    "large": 1.15,
}


_PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg_main": "#F6F9F7",
        "bg_gradient": "#E8EFEA",
        "panel": "#FFFFFF",
        "border": "#B8C4BE",
        "text_primary": "#2E3A34",
        "text_secondary": "#6B7C74",
        "text_muted": "#9AA8A1",
        "primary": "#5FAE6E",
        "primary_hover": "#3E7F52",
        "fill_soft": "#CFEAD6",
        "fill_hover": "#B7DDC0",
        "accent_green": "#A7D98B",
        "accent_blue": "#7FAFD4",
        "accent_amber": "#E6B85C",
        "accent_red": "#D97C7C",
        "toast_success": "#E6F4EA",
        "toast_info": "#E8F1F8",
        "toast_warn": "#FAF3E3",
        "toast_error": "#F3E9E9",
        "scroll_handle": "#A8CBB1",
        "check_border": "#A8B5AE",
        "text_title": "#1f2a30",
        "text_title_alt": "#1b2428",
        "text_sidebar": "#25333a",
        "text_secondary_alt": "#4c5b60",
        "text_secondary_alt2": "#516169",
    },
    "light_comfort": {
        "bg_main": "#EEF3EF",
        "bg_gradient": "#E3ECE6",
        "panel": "#F6FAF7",
        "border": "#BFCBC5",
        "text_primary": "#3A4A44",
        "text_secondary": "#72837B",
        "text_muted": "#8FA19A",
        "primary": "#7DB893",
        "primary_hover": "#6AA980",
        "fill_soft": "#DFEDE4",
        "fill_hover": "#D0E4D8",
        "accent_green": "#7FBF95",
        "accent_blue": "#9DBBD3",
        "accent_amber": "#E7C98A",
        "accent_red": "#D9A3A3",
        "toast_success": "#E2F0E7",
        "toast_info": "#E6EEF4",
        "toast_warn": "#FAF3E3",
        "toast_error": "#F3E9E9",
        "scroll_handle": "#A9C2B2",
        "check_border": "#9FB0A8",
        "text_title": "#33423C",
        "text_title_alt": "#33423C",
        "text_sidebar": "#33423C",
        "text_secondary_alt": "#6F8078",
        "text_secondary_alt2": "#6F8078",
    },
    "dark": {
        "bg_main": "#131816",
        "bg_gradient": "#1A201E",
        "panel": "#1F2623",
        "border": "#2A332F",
        "text_primary": "#E0EAE4",
        "text_secondary": "#A8B5AE",
        "text_muted": "#7A8982",
        "primary": "#6BCF8E",
        "primary_hover": "#5CBF82",
        "fill_soft": "#213329",
        "fill_hover": "#2A4035",
        "accent_green": "#6BCF8E",
        "accent_blue": "#7FA6BF",
        "accent_amber": "#C9A96F",
        "accent_red": "#B88383",
        "toast_success": "#213329",
        "toast_info": "#1F2C33",
        "toast_warn": "#2C271E",
        "toast_error": "#2D2121",
        "scroll_handle": "#47534D",
        "check_border": "#7A8982",
        "text_title": "#DCE7E1",
        "text_title_alt": "#DCE7E1",
        "text_sidebar": "#DCE7E1",
        "text_secondary_alt": "#A6B3AC",
        "text_secondary_alt2": "#A6B3AC",
    },
    "dark_comfort": {
        "bg_main": "#171C1A",
        "bg_gradient": "#1F2623",
        "panel": "#242C29",
        "border": "#2D3733",
        "text_primary": "#D3DED8",
        "text_secondary": "#9FB0A8",
        "text_muted": "#7F9189",
        "primary": "#74B48A",
        "primary_hover": "#639E78",
        "fill_soft": "#213228",
        "fill_hover": "#2A3D34",
        "accent_green": "#74B48A",
        "accent_blue": "#7FA6BF",
        "accent_amber": "#C9A96F",
        "accent_red": "#B88383",
        "toast_success": "#22352C",
        "toast_info": "#1F2C33",
        "toast_warn": "#2C271E",
        "toast_error": "#2D2121",
        "scroll_handle": "#3C4843",
        "check_border": "#7F9189",
        "text_title": "#D6E0DB",
        "text_title_alt": "#D6E0DB",
        "text_sidebar": "#D6E0DB",
        "text_secondary_alt": "#9FB0A8",
        "text_secondary_alt2": "#9FB0A8",
    },
}


def _palette_for(settings_obj: AppearanceSettings) -> dict[str, str]:
    key = settings_obj.mode
    if settings_obj.comfort:
        key = f"{key}_comfort"
    return _PALETTES.get(key, _PALETTES["light"])


def _color_mapping(palette: dict[str, str]) -> dict[str, str]:
    return {
        "#F6F9F7": palette["bg_main"],
        "#E8EFEA": palette["bg_gradient"],
        "#FFFFFF": palette["panel"],
        "#ffffff": palette["panel"],
        "#DDE5E0": palette["border"],
        "#2E3A34": palette["text_primary"],
        "#6B7C74": palette["text_secondary"],
        "#A8B5AE": palette["check_border"],
        "#A8CBB1": palette["scroll_handle"],
        "#CFEAD6": palette["fill_soft"],
        "#B7DDC0": palette["fill_hover"],
        "#5FAE6E": palette["primary"],
        "#3E7F52": palette["primary_hover"],
        "#A7D98B": palette["accent_green"],
        "#7FAFD4": palette["accent_blue"],
        "#E6B85C": palette["accent_amber"],
        "#D97C7C": palette["accent_red"],
        "#E6F4EA": palette["toast_success"],
        "#E8F1F8": palette["toast_info"],
        "#FAF3E3": palette["toast_warn"],
        "#F3E9E9": palette["toast_error"],
        "#E8EFEA": palette["bg_gradient"],
        "#1b2428": palette["text_title_alt"],
        "#1f2a30": palette["text_title"],
        "#25333a": palette["text_sidebar"],
        "#4c5b60": palette["text_secondary_alt"],
        "#516169": palette["text_secondary_alt2"],
    }


def _scale_fonts(qss: str, scale: float) -> str:
    def repl(match: re.Match[str]) -> str:
        size = int(round(float(match.group(1)) * scale))
        size = max(size, 11)
        return f"font-size: {size}px"

    return re.sub(r"font-size:\s*(\d+)px", repl, qss)


def build_stylesheet(style_path: Path, settings_obj: AppearanceSettings) -> str:
    base = style_path.read_text() if style_path.exists() else ""
    palette = _palette_for(settings_obj)
    mapping = _color_mapping(palette)
    for key, value in mapping.items():
        base = base.replace(key, value)
    base = base.replace("background: #FFFFFF;", f"background: {palette['panel']};")
    base = base.replace("background: #ffffff;", f"background: {palette['panel']};")
    base = base.replace("background-color: #ffffff;", f"background-color: {palette['panel']};")
    scale = _FONT_SCALES.get(settings_obj.font_size, 1.0)
    base = _scale_fonts(base, scale)
    return base


def apply_theme(
    app: QApplication | None, style_path: Path, settings_obj: AppearanceSettings
) -> None:
    if app is None:
        return
    css = build_stylesheet(style_path, settings_obj)
    app.setStyleSheet(css)
    palette_data = _palette_for(settings_obj)
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(palette_data["bg_main"]))
    palette.setColor(QPalette.WindowText, QColor(palette_data["text_primary"]))
    palette.setColor(QPalette.Base, QColor(palette_data["panel"]))
    palette.setColor(QPalette.Text, QColor(palette_data["text_primary"]))
    palette.setColor(QPalette.Button, QColor(palette_data["panel"]))
    palette.setColor(QPalette.ButtonText, QColor(palette_data["text_primary"]))
    palette.setColor(QPalette.Highlight, QColor(palette_data["primary"]))
    palette.setColor(QPalette.HighlightedText, QColor(palette_data["text_primary"]))
    palette.setColor(QPalette.ToolTipBase, QColor(palette_data["panel"]))
    palette.setColor(QPalette.ToolTipText, QColor(palette_data["text_primary"]))
    app.setPalette(palette)
