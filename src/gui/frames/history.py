"""History tab — browsable download history."""

from __future__ import annotations

import queue
import threading
from tkinter import messagebox

import customtkinter as ctk

from gui.theme import (
    BG_LIGHT,
    BODY_BOLD_FONT,
    BODY_FONT,
    CORNER_RADIUS,
    ERROR,
    PADDING,
    PADDING_LG,
    PADDING_SM,
    SMALL_FONT,
    SUCCESS,
    SURFACE,
    TEXT,
    TEXT_DIM,
    button_style,
    label_style,
)


class HistoryFrame(ctk.CTkFrame):
    """Download history tab with scrollable list and clear/refresh buttons."""

    def __init__(self, master: ctk.CTkBaseClass, msg_queue: queue.Queue, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._msg_queue = msg_queue

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        row = 0

        # ── Header row ────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(PADDING, 4))
        header.grid_columnconfigure(0, weight=1)
        row += 1

        ctk.CTkLabel(header, text="Download History", **label_style(heading=True)).grid(
            row=0, column=0, sticky="w")

        self._refresh_btn = ctk.CTkButton(
            header, text="Refresh", width=100,
            command=self._refresh, **button_style())
        self._refresh_btn.grid(row=0, column=1, padx=(8, 0))

        self._clear_btn = ctk.CTkButton(
            header, text="Clear", width=90,
            command=self._clear_history, **button_style())
        self._clear_btn.grid(row=0, column=2, padx=(8, 0))

        # ── Column headers ────────────────────────────────────────
        col_header = ctk.CTkFrame(self, fg_color=BG_LIGHT, corner_radius=CORNER_RADIUS)
        col_header.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(PADDING_SM, 2))
        col_header.grid_columnconfigure(0, weight=3)
        col_header.grid_columnconfigure(1, weight=1)
        col_header.grid_columnconfigure(2, weight=1)
        col_header.grid_columnconfigure(3, weight=1)
        col_header.grid_columnconfigure(4, weight=1)
        row += 1

        for col, hdr in enumerate(["Title", "Quality", "Format", "Size", "Date"]):
            ctk.CTkLabel(
                col_header, text=hdr, font=BODY_BOLD_FONT, text_color=TEXT_DIM,
                anchor="w",
            ).grid(row=0, column=col, sticky="w", padx=PADDING_SM, pady=PADDING_SM)

        # ── Scrollable list ───────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=SURFACE, corner_radius=CORNER_RADIUS,
        )
        self._scroll.grid(row=row, column=0, sticky="nsew", padx=PADDING, pady=PADDING_SM)
        self._scroll.grid_columnconfigure(0, weight=3)
        self._scroll.grid_columnconfigure(1, weight=1)
        self._scroll.grid_columnconfigure(2, weight=1)
        self._scroll.grid_columnconfigure(3, weight=1)
        self._scroll.grid_columnconfigure(4, weight=1)
        row += 1

        self._empty_lbl = ctk.CTkLabel(
            self._scroll, text="No download history",
            font=BODY_FONT, text_color=TEXT_DIM,
        )
        self._empty_lbl.grid(row=0, column=0, columnspan=5, pady=PADDING_LG)

        # ── Status ────────────────────────────────────────────────
        self._status_lbl = ctk.CTkLabel(
            self, text="", font=SMALL_FONT, text_color=TEXT_DIM, anchor="w")
        self._status_lbl.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))

        # Initial load
        self._refresh()

    # ── Actions ────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._refresh_btn.configure(state="disabled")
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self) -> None:
        try:
            from core.history import get_history  # type: ignore[import]
            records = get_history()
            self._msg_queue.put(("history_loaded", records))
        except Exception as exc:
            self._msg_queue.put(("history_error", str(exc)))

    def _clear_history(self) -> None:
        if not messagebox.askyesno("Clear History", "Delete all download history?"):
            return
        threading.Thread(target=self._clear_worker, daemon=True).start()

    def _clear_worker(self) -> None:
        try:
            from core.history import clear_history  # type: ignore[import]
            clear_history()
            self._msg_queue.put(("history_cleared", None))
        except Exception as exc:
            self._msg_queue.put(("history_error", str(exc)))

    # ── Queue message handler ──────────────────────────────────────

    def handle_message(self, tag: str, data) -> None:
        if tag == "history_loaded":
            self._refresh_btn.configure(state="normal")
            self._populate(data)
            self._status_lbl.configure(
                text=f"{len(data)} records", text_color=TEXT_DIM)

        elif tag == "history_cleared":
            self._populate([])
            self._status_lbl.configure(text="History cleared.", text_color=SUCCESS)

        elif tag == "history_error":
            self._refresh_btn.configure(state="normal")
            self._status_lbl.configure(text=f"Error: {data}", text_color=ERROR)

    # ── Populate ───────────────────────────────────────────────────

    def _populate(self, records: list) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        if not records:
            self._empty_lbl = ctk.CTkLabel(
                self._scroll, text="No download history",
                font=BODY_FONT, text_color=TEXT_DIM,
            )
            self._empty_lbl.grid(row=0, column=0, columnspan=5, pady=PADDING_LG)
            return

        for idx, rec in enumerate(records):
            bg = SURFACE if idx % 2 == 0 else BG_LIGHT

            title = rec.get("title", "Unknown")
            if len(title) > 45:
                title = title[:42] + "..."

            quality = rec.get("quality", "--")
            fmt = rec.get("format", "--")

            size_bytes = rec.get("file_size", 0)
            if size_bytes >= 1e9:
                size_str = f"{size_bytes / 1e9:.1f} GB"
            elif size_bytes >= 1e6:
                size_str = f"{size_bytes / 1e6:.1f} MB"
            elif size_bytes >= 1e3:
                size_str = f"{size_bytes / 1e3:.1f} KB"
            else:
                size_str = f"{size_bytes} B"

            date_str = rec.get("downloaded_at", rec.get("date", rec.get("timestamp", "--")))
            if isinstance(date_str, str) and len(date_str) > 16:
                date_str = date_str[:16].replace("T", " ")

            values = [title, quality, fmt, size_str, date_str]
            for col, val in enumerate(values):
                ctk.CTkLabel(
                    self._scroll, text=val, font=BODY_FONT,
                    text_color=TEXT, anchor="w", fg_color=bg,
                ).grid(row=idx, column=col, sticky="ew", padx=1, pady=1)
