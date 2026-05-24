"""Download tab — single video download with quality/format options."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from constants import (
    DownloadStatus,
    ProgressInfo,
    QualityPreset,
    VideoInfo,
)
from gui.theme import (
    ACCENT,
    BG_MEDIUM,
    BODY_BOLD_FONT,
    CORNER_RADIUS,
    ERROR,
    PADDING,
    PADDING_SM,
    SMALL_FONT,
    SUCCESS,
    TEXT,
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


class DownloadFrame(ctk.CTkFrame):
    """Single-video download tab."""

    def __init__(self, master: ctk.CTkBaseClass, msg_queue: queue.Queue, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._msg_queue = msg_queue
        self._current_info: VideoInfo | None = None
        self._download_thread: threading.Thread | None = None
        self._output_dir = str(Path.home() / "Downloads")

        self.grid_columnconfigure(0, weight=1)
        row = 0

        # ── Section: URL Input ────────────────────────────────────
        section_lbl = ctk.CTkLabel(self, text="Video URL", **label_style(heading=True))
        section_lbl.grid(row=row, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        row += 1

        self._url_input = URLInput(self, on_valid_url=self._on_url_entered)
        self._url_input.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        row += 1

        # ── Section: Video Info ───────────────────────────────────
        self._info_frame = ctk.CTkFrame(self, **frame_style())
        self._info_frame.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        self._info_frame.grid_columnconfigure(1, weight=1)
        row += 1

        self._thumb_lbl = ctk.CTkLabel(
            self._info_frame, text="", width=100, height=56,
            font=("Segoe UI", 32), text_color=TEXT_DIM,
            fg_color=BG_MEDIUM, corner_radius=CORNER_RADIUS,
        )
        self._thumb_lbl.grid(row=0, column=0, rowspan=2, padx=PADDING_SM, pady=PADDING_SM)

        self._title_lbl = ctk.CTkLabel(
            self._info_frame, text="No video loaded", anchor="w",
            font=BODY_BOLD_FONT, text_color=TEXT,
        )
        self._title_lbl.grid(row=0, column=1, sticky="w", padx=(0, PADDING), pady=(PADDING_SM, 0))

        self._duration_lbl = ctk.CTkLabel(
            self._info_frame, text="Duration: --:--", anchor="w",
            font=SMALL_FONT, text_color=TEXT_DIM,
        )
        self._duration_lbl.grid(row=1, column=1, sticky="w", padx=(0, PADDING), pady=(0, PADDING_SM))

        # ── Section: Options ──────────────────────────────────────
        opts_frame = ctk.CTkFrame(self, **frame_style())
        opts_frame.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        opts_frame.grid_columnconfigure((1, 3), weight=1)
        row += 1

        # Quality
        ctk.CTkLabel(opts_frame, text="Quality", **label_style(dim=True)).grid(
            row=0, column=0, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        self._quality_var = ctk.StringVar(value="Best")
        quality_options = ["Best", "High (1080p)", "Medium (720p)", "Better (480p)", "Low (360p)", "Lowest"]
        self._quality_menu = ctk.CTkOptionMenu(
            opts_frame, variable=self._quality_var, values=quality_options,
            width=160, **dropdown_style(),
        )
        self._quality_menu.grid(row=0, column=1, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        # Format
        ctk.CTkLabel(opts_frame, text="Format", **label_style(dim=True)).grid(
            row=0, column=2, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        self._format_var = ctk.StringVar(value="MP4")
        self._format_menu = ctk.CTkOptionMenu(
            opts_frame, variable=self._format_var,
            values=["MP4", "MKV", "WEBM"], width=120,
            **dropdown_style(),
        )
        self._format_menu.grid(row=0, column=3, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        # Output directory
        ctk.CTkLabel(opts_frame, text="Output", **label_style(dim=True)).grid(
            row=1, column=0, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        dir_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
        dir_row.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0, PADDING), pady=PADDING_SM)
        dir_row.grid_columnconfigure(0, weight=1)

        self._dir_entry = ctk.CTkEntry(dir_row, **entry_style())
        self._dir_entry.insert(0, self._output_dir)
        self._dir_entry.grid(row=0, column=0, sticky="ew")

        self._browse_btn = ctk.CTkButton(
            dir_row, text="Browse", width=80, command=self._browse_dir,
            **button_style(),
        )
        self._browse_btn.grid(row=0, column=1, padx=(6, 0))

        # Checkboxes
        cb_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        cb_frame.grid(row=2, column=0, columnspan=4, sticky="w", padx=PADDING, pady=(0, PADDING_SM))

        self._sub_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_frame, text="Subtitles", variable=self._sub_var, **checkbox_style()).pack(
            side="left", padx=(0, PADDING))

        self._sub_lang_entry = ctk.CTkEntry(cb_frame, width=64, **entry_style())
        self._sub_lang_entry.insert(0, "en")
        self._sub_lang_entry.pack(side="left", padx=(0, PADDING))

        self._thumb_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_frame, text="Thumbnail", variable=self._thumb_var, **checkbox_style()).pack(
            side="left", padx=(0, PADDING))

        self._sponsor_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_frame, text="SponsorBlock", variable=self._sponsor_var, **checkbox_style()).pack(
            side="left")

        # ── Download Button ───────────────────────────────────────
        self._download_btn = ctk.CTkButton(
            self, text="Download", width=220,
            command=self._start_download, **button_style(accent=True),
        )
        self._download_btn.grid(row=row, column=0, pady=PADDING)
        row += 1

        # ── Progress Area ─────────────────────────────────────────
        self._progress_widget = DownloadProgressWidget(self)
        self._progress_widget.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        row += 1

        # ── Status Label ──────────────────────────────────────────
        self._status_lbl = ctk.CTkLabel(
            self, text="Ready", font=SMALL_FONT, text_color=TEXT_DIM, anchor="w",
        )
        self._status_lbl.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))

    # ── Quality mapping ────────────────────────────────────────────

    _QUALITY_MAP = {
        "Best": QualityPreset.BEST,
        "High (1080p)": QualityPreset.HIGH,
        "Medium (720p)": QualityPreset.MEDIUM,
        "Better (480p)": QualityPreset.BETTER,
        "Low (360p)": QualityPreset.LOW,
        "Lowest": QualityPreset.LOWEST,
    }

    # ── Internal callbacks ─────────────────────────────────────────

    def _browse_dir(self) -> None:
        d = filedialog.askdirectory(initialdir=self._output_dir)
        if d:
            self._output_dir = d
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, d)

    def _on_url_entered(self, url: str) -> None:
        """Fetch video info in a background thread."""
        self._set_status("Fetching video info...", WARNING)
        self._title_lbl.configure(text="Loading...")
        self._duration_lbl.configure(text="Duration: --:--")
        t = threading.Thread(target=self._fetch_info_worker, args=(url,), daemon=True)
        t.start()

    def _fetch_info_worker(self, url: str) -> None:
        try:
            from core.utils import fetch_video_info  # type: ignore[import]
            info = fetch_video_info(url)
            self._msg_queue.put(("video_info", info))
        except Exception as exc:
            self._msg_queue.put(("video_info_error", str(exc)))

    def _start_download(self) -> None:
        url = self._url_input.get_url()
        if not url:
            self._set_status("Please enter a valid URL.", ERROR)
            return

        if self._download_thread and self._download_thread.is_alive():
            self._set_status("A download is already running.", WARNING)
            return

        quality_label = self._quality_var.get()
        preset = self._QUALITY_MAP.get(quality_label, QualityPreset.BEST)
        fmt = self._format_var.get().lower()
        output_dir = self._dir_entry.get().strip() or self._output_dir

        options = {
            "url": url,
            "quality": preset,
            "format": fmt,
            "output_dir": output_dir,
            "subtitles": self._sub_var.get(),
            "sub_lang": self._sub_lang_entry.get().strip() or "en",
            "thumbnail": self._thumb_var.get(),
            "sponsorblock": self._sponsor_var.get(),
        }

        self._progress_widget.reset()
        self._set_status("Starting download...", ACCENT)
        self._download_btn.configure(state="disabled", text="Downloading...")

        self._download_thread = threading.Thread(
            target=self._download_worker, args=(options,), daemon=True,
        )
        self._download_thread.start()

    def _download_worker(self, options: dict) -> None:
        try:
            from core.downloader import download_video  # type: ignore[import]

            def progress_callback(info: ProgressInfo) -> None:
                self._msg_queue.put(("download_progress", info))

            result = download_video(
                url=options["url"],
                quality=options["quality"],
                fmt=options["format"],
                output_dir=options["output_dir"],
                subtitles=options["subtitles"],
                sub_lang=options["sub_lang"],
                thumbnail=options["thumbnail"],
                sponsorblock=options["sponsorblock"],
                progress_callback=progress_callback,
            )
            self._msg_queue.put(("download_complete", result))
        except Exception as exc:
            self._msg_queue.put(("download_error", str(exc)))

    # ── Queue processing (called from app.py poll loop) ────────────

    def handle_message(self, tag: str, data) -> None:
        """Handle a message from the worker thread. Called on the main thread."""
        if tag == "video_info":
            self._current_info = data
            title = data.title if len(data.title) <= 70 else data.title[:67] + "..."
            self._title_lbl.configure(text=title)
            mins, secs = divmod(int(data.duration), 60)
            hours, mins = divmod(mins, 60)
            dur_str = f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins:02d}:{secs:02d}"
            self._duration_lbl.configure(text=f"Duration: {dur_str}  -  {data.uploader}")
            self._set_status("Video info loaded.", SUCCESS)

        elif tag == "video_info_error":
            self._title_lbl.configure(text="Failed to load video info")
            self._set_status(f"Error: {data}", ERROR)

        elif tag == "download_progress":
            self._progress_widget.update_progress(data)

        elif tag == "download_complete":
            if data.status == DownloadStatus.FAILED:
                err_info = ProgressInfo(
                    title=data.title or "Download",
                    status=DownloadStatus.FAILED,
                    percent=0,
                )
                self._progress_widget.update_progress(err_info)
                self._set_status(f"Error: {data.error_message}", ERROR)
                self._download_btn.configure(state="normal", text="Download")
                return

            done_info = ProgressInfo(
                title=data.title or "Download",
                status=DownloadStatus.COMPLETED,
                percent=100.0,
            )
            self._progress_widget.update_progress(done_info)
            self._set_status(f"Download complete: {data.title}", SUCCESS)
            self._download_btn.configure(state="normal", text="Download")
            self._msg_queue.put(("stats_completed", data))

        elif tag == "download_error":
            err_info = ProgressInfo(status=DownloadStatus.FAILED, percent=0)
            self._progress_widget.update_progress(err_info)
            self._set_status(f"Error: {data}", ERROR)
            self._download_btn.configure(state="normal", text="Download")

    # ── Helpers ────────────────────────────────────────────────────

    def _set_status(self, text: str, colour: str = TEXT_DIM) -> None:
        self._status_lbl.configure(text=text, text_color=colour)
