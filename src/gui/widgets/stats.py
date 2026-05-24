"""Aggregate download statistics widget."""

from __future__ import annotations

import customtkinter as ctk

from gui.theme import (
    BG_LIGHT,
    CORNER_RADIUS,
    PADDING_SM,
    SMALL_FONT,
    SUBHEADING_FONT,
    TEXT,
    TEXT_DIM,
    frame_style,
)


def _fmt_bytes(b: int) -> str:
    if b <= 0:
        return "0 B"
    if b >= 1e9:
        return f"{b / 1e9:.2f} GB"
    if b >= 1e6:
        return f"{b / 1e6:.1f} MB"
    if b >= 1e3:
        return f"{b / 1e3:.1f} KB"
    return f"{b} B"


class StatsWidget(ctk.CTkFrame):
    """Shows aggregate stats: active downloads, completed, total data, speed."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, **frame_style(), **kwargs)

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._cards: list[tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        labels = [
            ("Active", "0"),
            ("Completed", "0"),
            ("Downloaded", "0 B"),
            ("Speed", "-- B/s"),
        ]
        for col, (title, value) in enumerate(labels):
            card = ctk.CTkFrame(self, fg_color=BG_LIGHT, corner_radius=CORNER_RADIUS)
            card.grid(row=0, column=col, padx=PADDING_SM, pady=PADDING_SM, sticky="nsew")
            card.grid_rowconfigure((0, 1), weight=1)

            t = ctk.CTkLabel(card, text=title, font=SMALL_FONT, text_color=TEXT_DIM)
            t.grid(row=0, column=0, padx=PADDING_SM, pady=(PADDING_SM, 0), sticky="w")

            v = ctk.CTkLabel(card, text=value, font=SUBHEADING_FONT, text_color=TEXT)
            v.grid(row=1, column=0, padx=PADDING_SM, pady=(0, PADDING_SM), sticky="w")

            self._cards.append((t, v))

        # Internal counters
        self._active = 0
        self._completed = 0
        self._total_bytes = 0
        self._current_speed = 0.0
        self._poll_id: str | None = None

    # ── Public API ─────────────────────────────────────────────────

    def set_active(self, n: int) -> None:
        self._active = n
        self._cards[0][1].configure(text=str(n))

    def set_completed(self, n: int) -> None:
        self._completed = n
        self._cards[1][1].configure(text=str(n))

    def add_bytes(self, n: int) -> None:
        self._total_bytes += n
        self._cards[2][1].configure(text=_fmt_bytes(self._total_bytes))

    def set_total_bytes(self, n: int) -> None:
        self._total_bytes = n
        self._cards[2][1].configure(text=_fmt_bytes(self._total_bytes))

    def set_speed(self, bps: float) -> None:
        self._current_speed = bps
        self._cards[3][1].configure(text=self._speed_text(bps))

    def reset(self) -> None:
        self._active = 0
        self._completed = 0
        self._total_bytes = 0
        self._current_speed = 0.0
        self._cards[0][1].configure(text="0")
        self._cards[1][1].configure(text="0")
        self._cards[2][1].configure(text="0 B")
        self._cards[3][1].configure(text="-- B/s")

    # ── Internals ──────────────────────────────────────────────────

    @staticmethod
    def _speed_text(bps: float) -> str:
        if bps <= 0:
            return "-- B/s"
        if bps >= 1e9:
            return f"{bps / 1e9:.1f} GB/s"
        if bps >= 1e6:
            return f"{bps / 1e6:.1f} MB/s"
        if bps >= 1e3:
            return f"{bps / 1e3:.1f} KB/s"
        return f"{bps:.0f} B/s"
