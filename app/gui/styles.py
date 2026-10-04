"""Presentation tokens for the CustomTkinter UI. No solver logic."""

from __future__ import annotations

from app.models.feedback import GRAY, GREEN, YELLOW

WINDOW_BG = "#0E0F12"
PANEL_BG = "#17181C"
PANEL_BORDER = "#2A2C33"
TILE_EMPTY = "#0E0F12"
TILE_BORDER = "#3A3A3C"
TILE_BORDER_ACTIVE = "#D4D6DA"
TILE_GRAY = "#3A3A3C"
TILE_YELLOW = "#C9B458"
TILE_GREEN = "#6AAA64"
KEY_UNKNOWN = "#818384"
KEY_TEXT = "#F8F8F8"
TEXT_PRIMARY = "#F3F4F6"
TEXT_MUTED = "#9CA3AF"
ACCENT = "#6AAA64"
ACCENT_HOVER = "#7EBE78"
ACCENT_DIM = "#3F6F3C"
ERROR = "#F87171"
SUCCESS = "#6AAA64"
INFO = "#9CA3AF"
BUTTON_BG = "#2A2C33"
BUTTON_HOVER = "#3A3D46"

TILE_COLORS = {
    None: TILE_EMPTY,
    GRAY: TILE_GRAY,
    YELLOW: TILE_YELLOW,
    GREEN: TILE_GREEN,
}

TILE_HOVER = {
    None: "#1A1B1F",
    GRAY: "#4A4A4C",
    YELLOW: "#D4C06A",
    GREEN: "#7EBE78",
}

KEY_COLORS = {
    None: KEY_UNKNOWN,
    GRAY: TILE_GRAY,
    YELLOW: TILE_YELLOW,
    GREEN: TILE_GREEN,
}

KEY_HOVER = {
    None: "#9A9C9E",
    GRAY: "#4A4A4C",
    YELLOW: "#D4C06A",
    GREEN: "#7EBE78",
}

QWERTY_ROWS = (
    tuple("qwertyuiop"),
    tuple("asdfghjkl"),
    tuple("zxcvbnm"),
)
