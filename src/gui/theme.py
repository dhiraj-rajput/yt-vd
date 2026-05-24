"""Dark theme colours, fonts, and widget styling for yt-vd GUI."""

from __future__ import annotations

import customtkinter as ctk

# ── Colour Palette ──────────────────────────────────────────────────────────
BG_DARK = "#111315"
BG_MEDIUM = "#181c20"
BG_LIGHT = "#23292f"
ACCENT = "#2f9c95"
ACCENT_HOVER = "#38b8af"
TEXT = "#f2f5f3"
TEXT_DIM = "#98a2a5"
SUCCESS = "#4daa57"
WARNING = "#d79b35"
ERROR = "#d45b5b"

# Secondary / surface
SURFACE = "#1b2025"
SURFACE_HOVER = "#252c33"
BORDER = "#303943"
ENTRY_BG = "#101418"
ENTRY_BORDER = "#303943"

# ── Font Definitions ───────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_MONO = "Cascadia Code"

HEADING_FONT = (FONT_FAMILY, 18, "bold")
SUBHEADING_FONT = (FONT_FAMILY, 14, "bold")
BODY_FONT = (FONT_FAMILY, 13)
BODY_BOLD_FONT = (FONT_FAMILY, 13, "bold")
SMALL_FONT = (FONT_FAMILY, 11)
MONO_FONT = (FONT_MONO, 12)

# ── Widget Defaults ────────────────────────────────────────────────────────
CORNER_RADIUS = 8
BUTTON_CORNER = 8
BUTTON_HEIGHT = 36
ENTRY_HEIGHT = 38
PADDING = 12
PADDING_SM = 6
PADDING_LG = 20

# ── Reusable Style Kwargs ──────────────────────────────────────────────────

def button_style(*, accent: bool = False) -> dict:
    """Return common kwargs for CTkButton."""
    if accent:
        return dict(
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=BUTTON_CORNER,
            height=BUTTON_HEIGHT,
            font=BODY_BOLD_FONT,
        )
    return dict(
        fg_color=SURFACE,
        hover_color=SURFACE_HOVER,
        text_color=TEXT,
        corner_radius=BUTTON_CORNER,
        height=BUTTON_HEIGHT,
        font=BODY_FONT,
    )


def entry_style() -> dict:
    """Return common kwargs for CTkEntry."""
    return dict(
        fg_color=ENTRY_BG,
        border_color=ENTRY_BORDER,
        text_color=TEXT,
        placeholder_text_color=TEXT_DIM,
        corner_radius=CORNER_RADIUS,
        height=ENTRY_HEIGHT,
        font=BODY_FONT,
    )


def label_style(*, dim: bool = False, heading: bool = False) -> dict:
    """Return common kwargs for CTkLabel."""
    return dict(
        text_color=TEXT_DIM if dim else TEXT,
        font=HEADING_FONT if heading else BODY_FONT,
    )


def frame_style(*, transparent: bool = False) -> dict:
    """Return common kwargs for CTkFrame."""
    if transparent:
        return dict(fg_color="transparent")
    return dict(
        fg_color=SURFACE,
        corner_radius=CORNER_RADIUS,
    )


def dropdown_style() -> dict:
    """Return common kwargs for CTkOptionMenu / CTkComboBox."""
    return dict(
        fg_color=ENTRY_BG,
        button_color=BG_LIGHT,
        button_hover_color=SURFACE_HOVER,
        text_color=TEXT,
        dropdown_fg_color=BG_MEDIUM,
        dropdown_text_color=TEXT,
        dropdown_hover_color=SURFACE_HOVER,
        corner_radius=CORNER_RADIUS,
        font=BODY_FONT,
        dropdown_font=BODY_FONT,
    )


def checkbox_style() -> dict:
    """Return common kwargs for CTkCheckBox."""
    return dict(
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        border_color=BORDER,
        text_color=TEXT,
        font=BODY_FONT,
        corner_radius=4,
        checkbox_width=20,
        checkbox_height=20,
    )


def slider_style() -> dict:
    """Return common kwargs for CTkSlider."""
    return dict(
        fg_color=BG_LIGHT,
        progress_color=ACCENT,
        button_color=ACCENT,
        button_hover_color=ACCENT_HOVER,
    )


def progressbar_style() -> dict:
    """Return common kwargs for CTkProgressBar."""
    return dict(
        fg_color=BG_LIGHT,
        progress_color=ACCENT,
        corner_radius=CORNER_RADIUS,
        height=10,
    )


# ── Apply Theme ────────────────────────────────────────────────────────────

def apply_theme(root: ctk.CTk) -> None:
    """Configure the CustomTkinter appearance and colour theme on *root*."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root.configure(fg_color=BG_DARK)
