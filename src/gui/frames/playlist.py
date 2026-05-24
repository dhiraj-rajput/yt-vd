"""Playlist tab — download entire playlists with per-video tracking."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from constants import (
    DEFAULT_PARALLEL_WORKERS,
    DownloadStatus,
    PlaylistInfo,
    ProgressInfo,
    QualityPreset,
)
from gui.theme import (
    ACCENT,
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
    WARNING,
    button_style,
    checkbox_style,
    dropdown_style,
    entry_style,
    frame_style,
    label_style,
    progressbar_style,
    slider_style,
)
from gui.widgets.progress import DownloadProgressWidget
from gui.widgets.url_input import URLInput


class PlaylistFrame(ctk.CTkFrame):
    """Playlist download tab with per-video selection and progress tracking."""

    def __init__(self, master: ctk.CTkBaseClass, msg_queue: queue.Queue, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._msg_queue = msg_queue
        self._playlist_info: PlaylistInfo | None = None
        self._video_checkboxes: list[tuple[ctk.BooleanVar, dict]] = []
        self._progress_widgets: dict[int, DownloadProgressWidget] = {}
        self._download_thread: threading.Thread | None = None
        self._output_dir = str(Path.home() / "Downloads")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)  # scrollable area expands
        row = 0

        # ── URL Input ─────────────────────────────────────────────
        ctk.CTkLabel(self, text="Playlist URL", **label_style(heading=True)).grid(
            row=row, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        row += 1

        url_row = ctk.CTkFrame(self, fg_color="transparent")
        url_row.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        url_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._url_input = URLInput(url_row)
        self._url_input.grid(row=0, column=0, sticky="ew")

        self._fetch_btn = ctk.CTkButton(
            url_row, text="Fetch Playlist", width=130,
            command=self._fetch_playlist, **button_style(accent=True),
        )
        self._fetch_btn.grid(row=0, column=1, padx=(8, 0))

        # ── Playlist info bar ─────────────────────────────────────
        self._info_lbl = ctk.CTkLabel(
            self, text="Enter a playlist URL and click Fetch Playlist.",
            font=BODY_FONT, text_color=TEXT_DIM, anchor="w",
        )
        self._info_lbl.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        row += 1

        # ── Options row ───────────────────────────────────────────
        opts = ctk.CTkFrame(self, **frame_style())
        opts.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        opts.grid_columnconfigure((1, 3, 5, 7), weight=1)
        row += 1

        # Quality
        ctk.CTkLabel(opts, text="Quality", **label_style(dim=True)).grid(
            row=0, column=0, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        self._quality_var = ctk.StringVar(value="Best")
        ctk.CTkOptionMenu(
            opts, variable=self._quality_var,
            values=["Best", "High (1080p)", "Medium (720p)", "Better (480p)", "Low (360p)", "Lowest"],
            width=150, **dropdown_style(),
        ).grid(row=0, column=1, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        # Format
        ctk.CTkLabel(opts, text="Format", **label_style(dim=True)).grid(
            row=0, column=2, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        self._format_var = ctk.StringVar(value="MP4")
        ctk.CTkOptionMenu(
            opts, variable=self._format_var, values=["MP4", "MKV", "WEBM"],
            width=100, **dropdown_style(),
        ).grid(row=0, column=3, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        # Start / End range
        ctk.CTkLabel(opts, text="Range", **label_style(dim=True)).grid(
            row=0, column=4, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        range_frame = ctk.CTkFrame(opts, fg_color="transparent")
        range_frame.grid(row=0, column=5, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        self._start_entry = ctk.CTkEntry(range_frame, width=50, placeholder_text="1", **entry_style())
        self._start_entry.pack(side="left")
        ctk.CTkLabel(range_frame, text="-", text_color=TEXT_DIM, font=BODY_FONT).pack(side="left", padx=4)
        self._end_entry = ctk.CTkEntry(range_frame, width=50, placeholder_text="end", **entry_style())
        self._end_entry.pack(side="left")

        # Workers slider
        ctk.CTkLabel(opts, text="Workers", **label_style(dim=True)).grid(
            row=0, column=6, padx=(PADDING, 4), pady=PADDING_SM, sticky="w")
        worker_frame = ctk.CTkFrame(opts, fg_color="transparent")
        worker_frame.grid(row=0, column=7, padx=(0, PADDING), pady=PADDING_SM, sticky="w")

        max_workers = os.cpu_count() or 4
        self._workers_var = ctk.IntVar(value=DEFAULT_PARALLEL_WORKERS)
        self._workers_slider = ctk.CTkSlider(
            worker_frame, from_=1, to=max_workers, number_of_steps=max_workers - 1,
            variable=self._workers_var, width=100, command=self._on_workers_changed,
            **slider_style(),
        )
        self._workers_slider.pack(side="left")
        self._workers_lbl = ctk.CTkLabel(
            worker_frame, text=str(DEFAULT_PARALLEL_WORKERS),
            width=24, font=SMALL_FONT, text_color=TEXT_DIM,
        )
        self._workers_lbl.pack(side="left", padx=(6, 0))

        # Output directory
        dir_row = ctk.CTkFrame(opts, fg_color="transparent")
        dir_row.grid(row=1, column=0, columnspan=8, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        dir_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(dir_row, text="Output", **label_style(dim=True)).grid(
            row=0, column=0, padx=(0, 8), sticky="w")
        self._dir_entry = ctk.CTkEntry(dir_row, **entry_style())
        self._dir_entry.insert(0, self._output_dir)
        self._dir_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(dir_row, text="Browse", width=80, command=self._browse_dir,
                       **button_style()).grid(row=0, column=2, padx=(6, 0))

        # ── Video list (scrollable) ───────────────────────────────
        self._video_scroll = ctk.CTkScrollableFrame(
            self, fg_color=SURFACE, corner_radius=CORNER_RADIUS, height=200,
        )
        self._video_scroll.grid(row=row, column=0, sticky="nsew", padx=PADDING, pady=PADDING_SM)
        self._video_scroll.grid_columnconfigure(0, weight=1)
        row += 1

        self._empty_lbl = ctk.CTkLabel(
            self._video_scroll, text="No playlist loaded",
            font=BODY_FONT, text_color=TEXT_DIM,
        )
        self._empty_lbl.grid(row=0, column=0, pady=PADDING_LG)

        # ── Select all / Deselect / Download ──────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        row += 1

        self._select_all_btn = ctk.CTkButton(
            btn_row, text="Select All", width=100, command=self._select_all, **button_style())
        self._select_all_btn.pack(side="left", padx=(0, 8))

        self._deselect_btn = ctk.CTkButton(
            btn_row, text="Deselect All", width=100, command=self._deselect_all, **button_style())
        self._deselect_btn.pack(side="left", padx=(0, 8))

        self._dl_btn = ctk.CTkButton(
            btn_row, text="Download Playlist", width=200,
            command=self._start_download, **button_style(accent=True))
        self._dl_btn.pack(side="right")

        # ── Overall progress ──────────────────────────────────────
        self._overall_progress = ctk.CTkProgressBar(self, **progressbar_style(), width=400)
        self._overall_progress.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, 4))
        self._overall_progress.set(0)
        row += 1

        self._status_lbl = ctk.CTkLabel(
            self, text="Ready", font=SMALL_FONT, text_color=TEXT_DIM, anchor="w")
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

    # ── Callbacks ──────────────────────────────────────────────────

    def _on_workers_changed(self, val: float) -> None:
        self._workers_lbl.configure(text=str(int(val)))

    def _browse_dir(self) -> None:
        d = filedialog.askdirectory(initialdir=self._output_dir)
        if d:
            self._output_dir = d
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, d)

    def _select_all(self) -> None:
        for var, _ in self._video_checkboxes:
            var.set(True)

    def _deselect_all(self) -> None:
        for var, _ in self._video_checkboxes:
            var.set(False)

    # ── Fetch playlist ─────────────────────────────────────────────

    def _fetch_playlist(self) -> None:
        url = self._url_input.get_url()
        if not url:
            self._status_lbl.configure(text="Enter a valid playlist URL.", text_color=ERROR)
            return
        self._fetch_btn.configure(state="disabled", text="Fetching...")
        self._status_lbl.configure(text="Fetching playlist info...", text_color=WARNING)
        t = threading.Thread(target=self._fetch_worker, args=(url,), daemon=True)
        t.start()

    def _fetch_worker(self, url: str) -> None:
        try:
            from core.playlist import fetch_playlist_info  # type: ignore[import]
            info = fetch_playlist_info(url)
            self._msg_queue.put(("playlist_info", info))
        except Exception as exc:
            self._msg_queue.put(("playlist_info_error", str(exc)))

    # ── Download ───────────────────────────────────────────────────

    def _start_download(self) -> None:
        if self._download_thread and self._download_thread.is_alive():
            self._status_lbl.configure(text="Download already in progress.", text_color=WARNING)
            return
        if not self._playlist_info:
            self._status_lbl.configure(text="Fetch a playlist first.", text_color=ERROR)
            return

        selected_pairs = [
            (idx, entry)
            for idx, (var, entry) in enumerate(self._video_checkboxes)
            if var.get()
        ]
        if not selected_pairs:
            self._status_lbl.configure(text="Select at least one video.", text_color=ERROR)
            return

        # Range
        start = self._start_entry.get().strip()
        end = self._end_entry.get().strip()
        start_idx = int(start) - 1 if start.isdigit() else 0
        end_idx = int(end) if end.isdigit() else len(selected_pairs)
        selected_pairs = selected_pairs[start_idx:end_idx]
        selected_entries = [entry for _, entry in selected_pairs]
        widget_indices = [idx for idx, _ in selected_pairs]

        quality_label = self._quality_var.get()
        preset = self._QUALITY_MAP.get(quality_label, QualityPreset.BEST)
        fmt = self._format_var.get().lower()
        workers = self._workers_var.get()
        output_dir = self._dir_entry.get().strip() or self._output_dir

        self._dl_btn.configure(state="disabled", text="Downloading...")
        self._overall_progress.set(0)
        self._status_lbl.configure(text=f"Downloading {len(selected_entries)} videos...", text_color=ACCENT)

        options = {
            "entries": selected_entries,
            "widget_indices": widget_indices,
            "quality": preset,
            "format": fmt,
            "workers": workers,
            "output_dir": output_dir,
            "playlist_title": self._playlist_info.title,
        }
        self._download_thread = threading.Thread(
            target=self._download_worker, args=(options,), daemon=True)
        self._download_thread.start()

    def _download_worker(self, options: dict) -> None:
        try:
            from core.parallel import download_parallel  # type: ignore[import]

            total = len(options["entries"])
            completed = 0

            def widget_index(worker_idx: int) -> int:
                indices = options.get("widget_indices") or []
                if 0 <= worker_idx < len(indices):
                    return indices[worker_idx]
                return worker_idx

            def on_video_done(idx: int, result) -> None:
                nonlocal completed
                completed += 1
                self._msg_queue.put(("playlist_video_done", (widget_index(idx), completed, total, result)))

            def on_progress(idx: int, info: ProgressInfo) -> None:
                self._msg_queue.put(("playlist_progress", (widget_index(idx), info)))

            results = download_parallel(
                entries=options["entries"],
                quality=options["quality"],
                fmt=options["format"],
                workers=options["workers"],
                output_dir=options["output_dir"],
                playlist_title=options["playlist_title"],
                on_video_done=on_video_done,
                on_progress=on_progress,
            )
            self._msg_queue.put(("playlist_complete", results))
        except Exception as exc:
            self._msg_queue.put(("playlist_error", str(exc)))

    # ── Queue message handler ──────────────────────────────────────

    def handle_message(self, tag: str, data) -> None:
        if tag == "playlist_info":
            self._playlist_info = data
            self._fetch_btn.configure(state="normal", text="Fetch Playlist")
            self._info_lbl.configure(
                text=f"{data.title}  -  {data.video_count} videos  -  {data.uploader}",
                text_color=TEXT,
            )
            self._populate_video_list(data)
            self._status_lbl.configure(text="Playlist loaded.", text_color=SUCCESS)

        elif tag == "playlist_info_error":
            self._fetch_btn.configure(state="normal", text="Fetch Playlist")
            self._info_lbl.configure(text=f"Error: {data}", text_color=ERROR)
            self._status_lbl.configure(text="Failed to fetch playlist.", text_color=ERROR)

        elif tag == "playlist_progress":
            idx, info = data
            if idx in self._progress_widgets:
                self._progress_widgets[idx].update_progress(info)

        elif tag == "playlist_video_done":
            idx, completed, total, result = data
            pct = completed / max(total, 1)
            self._overall_progress.set(pct)
            self._status_lbl.configure(
                text=f"Completed {completed}/{total} videos", text_color=ACCENT)
            if idx in self._progress_widgets:
                status = result.status if hasattr(result, "status") else DownloadStatus.COMPLETED
                percent = 0 if status == DownloadStatus.FAILED else 100
                done = ProgressInfo(
                    title=result.title if hasattr(result, "title") else "",
                    status=status, percent=percent,
                )
                self._progress_widgets[idx].update_progress(done)

        elif tag == "playlist_complete":
            self._overall_progress.set(1.0)
            self._dl_btn.configure(state="normal", text="Download Playlist")
            failed = 0
            for result in data or []:
                status = getattr(getattr(result, "status", None), "value", getattr(result, "status", None))
                if status == "failed":
                    failed += 1
            if failed:
                self._status_lbl.configure(text=f"Finished with {failed} failed download(s).", text_color=WARNING)
            else:
                self._status_lbl.configure(text="All downloads finished.", text_color=SUCCESS)

        elif tag == "playlist_error":
            self._dl_btn.configure(state="normal", text="Download Playlist")
            self._status_lbl.configure(text=f"Error: {data}", text_color=ERROR)

    # ── Helpers ────────────────────────────────────────────────────

    def _populate_video_list(self, info: PlaylistInfo) -> None:
        # Clear previous
        for w in self._video_scroll.winfo_children():
            w.destroy()
        self._video_checkboxes.clear()
        self._progress_widgets.clear()

        for idx, entry in enumerate(info.entries):
            row_frame = ctk.CTkFrame(self._video_scroll, **frame_style())
            row_frame.grid(row=idx, column=0, sticky="ew", padx=2, pady=2)
            row_frame.grid_columnconfigure(1, weight=1)

            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                row_frame, text="", variable=var, width=24,
                **checkbox_style(),
            )
            cb.grid(row=0, column=0, padx=(PADDING_SM, 4), pady=PADDING_SM)

            title = entry.get("title", f"Video {idx + 1}")
            if len(title) > 55:
                title = title[:52] + "..."
            dur = entry.get("duration", 0)
            mins, secs = divmod(int(dur), 60)
            dur_str = f"{mins}:{secs:02d}"

            lbl = ctk.CTkLabel(
                row_frame, text=f"{idx + 1}. {title}  ({dur_str})",
                font=BODY_FONT, text_color=TEXT, anchor="w",
            )
            lbl.grid(row=0, column=1, sticky="w", padx=(0, PADDING_SM), pady=PADDING_SM)

            self._video_checkboxes.append((var, entry))

            pw = DownloadProgressWidget(row_frame)
            pw.grid(row=1, column=0, columnspan=2, sticky="ew", padx=PADDING_SM, pady=(0, PADDING_SM))
            self._progress_widgets[idx] = pw
