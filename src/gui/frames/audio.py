"""Audio tab — extract or download audio-only streams."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from constants import (
    DownloadStatus,
    ProgressInfo,
)
from gui.theme import (
    ACCENT,
    ERROR,
    PADDING,
    PADDING_SM,
    SMALL_FONT,
    SUCCESS,
    TEXT_DIM,
    WARNING,
    button_style,
    checkbox_style,
    dropdown_style,
    entry_style,
    frame_style,
    label_style,
)
from gui.widgets.progress import DownloadProgressWidget
from gui.widgets.url_input import URLInput


class AudioFrame(ctk.CTkFrame):
    """Audio extraction / download tab."""

    def __init__(self, master: ctk.CTkBaseClass, msg_queue: queue.Queue, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._msg_queue = msg_queue
        self._download_thread: threading.Thread | None = None
        self._output_dir = str(Path.home() / "Music")

        self.grid_columnconfigure(0, weight=1)
        row = 0

        # ── URL Input ─────────────────────────────────────────────
        ctk.CTkLabel(self, text="Audio URL", **label_style(heading=True)).grid(
            row=row, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        row += 1

        self._url_input = URLInput(self)
        self._url_input.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        row += 1

        # ── Options ───────────────────────────────────────────────
        opts = ctk.CTkFrame(self, **frame_style())
        opts.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        opts.grid_columnconfigure((1, 3), weight=1)
        row += 1

        # Audio format
        ctk.CTkLabel(opts, text="Format", **label_style(dim=True)).grid(
            row=0, column=0, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        self._fmt_var = ctk.StringVar(value="MP3")
        ctk.CTkOptionMenu(
            opts, variable=self._fmt_var,
            values=["MP3", "M4A", "FLAC", "WAV", "Opus"],
            width=120, **dropdown_style(),
        ).grid(row=0, column=1, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        # Bitrate
        ctk.CTkLabel(opts, text="Bitrate", **label_style(dim=True)).grid(
            row=0, column=2, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        self._bitrate_var = ctk.StringVar(value="192k")
        ctk.CTkOptionMenu(
            opts, variable=self._bitrate_var,
            values=["128k", "192k", "256k", "320k"],
            width=100, **dropdown_style(),
        ).grid(row=0, column=3, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        # Embed thumbnail checkbox
        self._thumb_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts, text="Embed thumbnail as album art",
            variable=self._thumb_var, **checkbox_style(),
        ).grid(row=1, column=0, columnspan=4, padx=PADDING, pady=(0, PADDING_SM), sticky="w")

        # Output directory
        dir_row = ctk.CTkFrame(opts, fg_color="transparent")
        dir_row.grid(row=2, column=0, columnspan=4, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        dir_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(dir_row, text="Output", **label_style(dim=True)).grid(
            row=0, column=0, padx=(0, 8), sticky="w")
        self._dir_entry = ctk.CTkEntry(dir_row, **entry_style())
        self._dir_entry.insert(0, self._output_dir)
        self._dir_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(dir_row, text="Browse", width=80, command=self._browse_dir,
                       **button_style()).grid(row=0, column=2, padx=(6, 0))

        # ── Download Button ───────────────────────────────────────
        self._dl_btn = ctk.CTkButton(
            self, text="Extract Audio", width=220,
            command=self._start_download, **button_style(accent=True),
        )
        self._dl_btn.grid(row=row, column=0, pady=PADDING)
        row += 1

        # ── Progress ──────────────────────────────────────────────
        self._progress_widget = DownloadProgressWidget(self)
        self._progress_widget.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        row += 1

        # ── Status ────────────────────────────────────────────────
        self._status_lbl = ctk.CTkLabel(
            self, text="Ready", font=SMALL_FONT, text_color=TEXT_DIM, anchor="w")
        self._status_lbl.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))

    # ── Callbacks ──────────────────────────────────────────────────

    def _browse_dir(self) -> None:
        d = filedialog.askdirectory(initialdir=self._output_dir)
        if d:
            self._output_dir = d
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, d)

    def _start_download(self) -> None:
        url = self._url_input.get_url()
        if not url:
            self._status_lbl.configure(text="Enter a valid URL.", text_color=ERROR)
            return
        if self._download_thread and self._download_thread.is_alive():
            self._status_lbl.configure(text="Download already running.", text_color=WARNING)
            return

        fmt = self._fmt_var.get().lower()
        bitrate = self._bitrate_var.get()
        embed_thumb = self._thumb_var.get()
        output_dir = self._dir_entry.get().strip() or self._output_dir

        self._progress_widget.reset()
        self._dl_btn.configure(state="disabled", text="Extracting...")
        self._status_lbl.configure(text="Starting audio extraction...", text_color=ACCENT)

        options = {
            "url": url, "format": fmt, "bitrate": bitrate,
            "embed_thumbnail": embed_thumb, "output_dir": output_dir,
        }
        self._download_thread = threading.Thread(
            target=self._download_worker, args=(options,), daemon=True)
        self._download_thread.start()

    def _download_worker(self, options: dict) -> None:
        try:
            from core.audio import download_audio  # type: ignore[import]

            def progress_callback(info: ProgressInfo) -> None:
                self._msg_queue.put(("audio_progress", info))

            result = download_audio(
                url=options["url"],
                audio_format=options["format"],
                bitrate=options["bitrate"],
                embed_thumbnail=options["embed_thumbnail"],
                output_dir=options["output_dir"],
                progress_callback=progress_callback,
            )
            self._msg_queue.put(("audio_complete", result))
        except Exception as exc:
            self._msg_queue.put(("audio_error", str(exc)))

    # ── Queue message handler ──────────────────────────────────────

    def handle_message(self, tag: str, data) -> None:
        if tag == "audio_progress":
            self._progress_widget.update_progress(data)

        elif tag == "audio_complete":
            if data.status == DownloadStatus.FAILED:
                err = ProgressInfo(
                    title=data.title or "Audio",
                    status=DownloadStatus.FAILED,
                )
                self._progress_widget.update_progress(err)
                self._dl_btn.configure(state="normal", text="Extract Audio")
                self._status_lbl.configure(text=f"Error: {data.error_message}", text_color=ERROR)
                return

            done = ProgressInfo(
                title=data.title if hasattr(data, "title") else "Audio",
                status=DownloadStatus.COMPLETED, percent=100,
            )
            self._progress_widget.update_progress(done)
            self._dl_btn.configure(state="normal", text="Extract Audio")
            self._status_lbl.configure(text="Audio extraction complete!", text_color=SUCCESS)
            self._msg_queue.put(("stats_completed", data))

        elif tag == "audio_error":
            err = ProgressInfo(status=DownloadStatus.FAILED)
            self._progress_widget.update_progress(err)
            self._dl_btn.configure(state="normal", text="Extract Audio")
            self._status_lbl.configure(text=f"Error: {data}", text_color=ERROR)
