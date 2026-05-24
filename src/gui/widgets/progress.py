"""Download progress bar widget for a single download item."""

from __future__ import annotations

import customtkinter as ctk

from constants import DownloadStatus, ProgressInfo
from gui.theme import (
    ACCENT,
    BODY_BOLD_FONT,
    ERROR,
    PADDING,
    PADDING_SM,
    SMALL_FONT,
    SUCCESS,
    TEXT,
    TEXT_DIM,
    WARNING,
    frame_style,
    progressbar_style,
)


class DownloadProgressWidget(ctk.CTkFrame):
    """Compact progress display for one download – designed to stack in a list."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, **frame_style(), **kwargs)

        self.grid_columnconfigure(0, weight=1)

        # Row 0 — title + status badge
        self._title_row = ctk.CTkFrame(self, fg_color="transparent")
        self._title_row.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=(PADDING_SM, 2))
        self._title_row.grid_columnconfigure(0, weight=1)

        self._title_lbl = ctk.CTkLabel(
            self._title_row, text="Waiting...", anchor="w",
            font=BODY_BOLD_FONT, text_color=TEXT,
        )
        self._title_lbl.grid(row=0, column=0, sticky="w")

        self._status_lbl = ctk.CTkLabel(
            self._title_row, text="queued", anchor="e",
            font=SMALL_FONT, text_color=TEXT_DIM,
        )
        self._status_lbl.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Row 1 — progress bar
        self._progress = ctk.CTkProgressBar(self, **progressbar_style())
        self._progress.grid(row=1, column=0, sticky="ew", padx=PADDING, pady=2)
        self._progress.set(0)

        # Row 2 — stats row: percent | speed | ETA | size
        self._stats_row = ctk.CTkFrame(self, fg_color="transparent")
        self._stats_row.grid(row=2, column=0, sticky="ew", padx=PADDING, pady=(2, PADDING_SM))
        for i in range(4):
            self._stats_row.grid_columnconfigure(i, weight=1)

        self._pct_lbl = self._stat_label(self._stats_row, 0, "0 %")
        self._speed_lbl = self._stat_label(self._stats_row, 1, "-- B/s")
        self._eta_lbl = self._stat_label(self._stats_row, 2, "ETA --:--")
        self._size_lbl = self._stat_label(self._stats_row, 3, "-- / --")

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _stat_label(parent: ctk.CTkFrame, col: int, text: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            parent, text=text, font=SMALL_FONT, text_color=TEXT_DIM,
            anchor="center",
        )
        lbl.grid(row=0, column=col, sticky="ew")
        return lbl

    # ── Public API ─────────────────────────────────────────────────

    def update_progress(self, info: ProgressInfo) -> None:
        """Refresh all labels and the progress bar from a ProgressInfo."""
        # Title
        if info.title:
            title = info.title if len(info.title) <= 60 else info.title[:57] + "..."
            self._title_lbl.configure(text=title)

        # Status badge colour
        status_colours = {
            DownloadStatus.QUEUED: TEXT_DIM,
            DownloadStatus.DOWNLOADING: ACCENT,
            DownloadStatus.PROCESSING: WARNING,
            DownloadStatus.COMPLETED: SUCCESS,
            DownloadStatus.FAILED: ERROR,
            DownloadStatus.SKIPPED: TEXT_DIM,
        }
        colour = status_colours.get(info.status, TEXT_DIM)
        self._status_lbl.configure(text=info.status.value, text_color=colour)

        # Progress bar
        pct = max(0.0, min(info.percent, 100.0))
        self._progress.set(pct / 100.0)

        # Colour the bar on completion / failure
        if info.status == DownloadStatus.COMPLETED:
            self._progress.configure(progress_color=SUCCESS)
        elif info.status == DownloadStatus.FAILED:
            self._progress.configure(progress_color=ERROR)
        else:
            self._progress.configure(progress_color=ACCENT)

        # Stats
        self._pct_lbl.configure(text=f"{pct:.1f} %")
        self._speed_lbl.configure(text=info.speed_str)
        self._eta_lbl.configure(text=f"ETA {info.eta_str}")
        self._size_lbl.configure(text=info.size_str)

    def reset(self) -> None:
        """Reset to default / empty state."""
        self._title_lbl.configure(text="Waiting...")
        self._status_lbl.configure(text="queued", text_color=TEXT_DIM)
        self._progress.set(0)
        self._progress.configure(progress_color=ACCENT)
        self._pct_lbl.configure(text="0 %")
        self._speed_lbl.configure(text="-- B/s")
        self._eta_lbl.configure(text="ETA --:--")
        self._size_lbl.configure(text="-- / --")
