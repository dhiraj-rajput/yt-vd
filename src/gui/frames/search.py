"""Search tab — search YouTube and download results."""

from __future__ import annotations

import queue
import threading

import customtkinter as ctk

from constants import (
    QualityPreset,
)
from gui.theme import (
    ACCENT,
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
    WARNING,
    button_style,
    dropdown_style,
    entry_style,
    frame_style,
    label_style,
)


class SearchFrame(ctk.CTkFrame):
    """YouTube search tab with result list and inline download buttons."""

    def __init__(self, master: ctk.CTkBaseClass, msg_queue: queue.Queue, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._msg_queue = msg_queue
        self._search_thread: threading.Thread | None = None
        self._results: list[dict] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        row = 0

        # ── Search bar ────────────────────────────────────────────
        ctk.CTkLabel(self, text="Search YouTube", **label_style(heading=True)).grid(
            row=row, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        row += 1

        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING_SM))
        search_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search for videos...", **entry_style())
        self._search_entry.grid(row=0, column=0, sticky="ew")
        self._search_entry.bind("<Return>", lambda _: self._do_search())

        self._search_btn = ctk.CTkButton(
            search_row, text="Search", width=110,
            command=self._do_search, **button_style(accent=True))
        self._search_btn.grid(row=0, column=1, padx=(8, 0))

        # ── Quality + Format dropdowns ────────────────────────────
        opts_row = ctk.CTkFrame(self, fg_color="transparent")
        opts_row.grid(row=row, column=0, sticky="w", padx=PADDING, pady=(0, PADDING_SM))
        row += 1

        ctk.CTkLabel(opts_row, text="Quality", **label_style(dim=True)).pack(side="left", padx=(0, 4))
        self._quality_var = ctk.StringVar(value="Best")
        ctk.CTkOptionMenu(
            opts_row, variable=self._quality_var,
            values=["Best", "High (1080p)", "Medium (720p)", "Better (480p)", "Low (360p)", "Lowest"],
            width=150, **dropdown_style(),
        ).pack(side="left", padx=(0, PADDING))

        ctk.CTkLabel(opts_row, text="Format", **label_style(dim=True)).pack(side="left", padx=(0, 4))
        self._format_var = ctk.StringVar(value="MP4")
        ctk.CTkOptionMenu(
            opts_row, variable=self._format_var,
            values=["MP4", "MKV", "WEBM"], width=100, **dropdown_style(),
        ).pack(side="left")

        # ── Results area (scrollable) ─────────────────────────────
        self._results_scroll = ctk.CTkScrollableFrame(
            self, fg_color=SURFACE, corner_radius=CORNER_RADIUS,
        )
        self._results_scroll.grid(row=row, column=0, sticky="nsew", padx=PADDING, pady=PADDING_SM)
        self._results_scroll.grid_columnconfigure(0, weight=1)
        row += 1

        self._empty_lbl = ctk.CTkLabel(
            self._results_scroll, text="Search for videos above",
            font=BODY_FONT, text_color=TEXT_DIM,
        )
        self._empty_lbl.grid(row=0, column=0, pady=PADDING_LG)

        # ── Status ────────────────────────────────────────────────
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

    # ── Search ─────────────────────────────────────────────────────

    def _do_search(self) -> None:
        query = self._search_entry.get().strip()
        if not query:
            return
        if self._search_thread and self._search_thread.is_alive():
            return
        self._search_btn.configure(state="disabled", text="Searching...")
        self._status_lbl.configure(text="Searching...", text_color=WARNING)
        self._search_thread = threading.Thread(
            target=self._search_worker, args=(query,), daemon=True)
        self._search_thread.start()

    def _search_worker(self, query: str) -> None:
        try:
            from core.search import search_youtube  # type: ignore[import]
            results = search_youtube(query, max_results=15)
            self._msg_queue.put(("search_results", results))
        except Exception as exc:
            self._msg_queue.put(("search_error", str(exc)))

    # ── Download from result ───────────────────────────────────────

    def _download_result(self, url: str, btn: ctk.CTkButton) -> None:
        quality_label = self._quality_var.get()
        preset = self._QUALITY_MAP.get(quality_label, QualityPreset.BEST)
        fmt = self._format_var.get().lower()
        btn.configure(state="disabled", text="...")
        self._status_lbl.configure(text="Starting download...", text_color=ACCENT)

        def worker() -> None:
            try:
                from core.downloader import download_video  # type: ignore[import]
                result = download_video(url=url, quality=preset, fmt=fmt)
                self._msg_queue.put(("search_dl_complete", (result, btn)))
            except Exception as exc:
                self._msg_queue.put(("search_dl_error", (str(exc), btn)))

        threading.Thread(target=worker, daemon=True).start()

    # ── Queue message handler ──────────────────────────────────────

    def handle_message(self, tag: str, data) -> None:
        if tag == "search_results":
            self._results = data
            self._search_btn.configure(state="normal", text="Search")
            self._populate_results(data)
            self._status_lbl.configure(
                text=f"Found {len(data)} results.", text_color=SUCCESS)

        elif tag == "search_error":
            self._search_btn.configure(state="normal", text="Search")
            self._status_lbl.configure(text=f"Error: {data}", text_color=ERROR)

        elif tag == "search_dl_complete":
            result, btn = data
            btn.configure(state="normal", text="Download")
            status = getattr(getattr(result, "status", None), "value", getattr(result, "status", None))
            if status == "failed":
                self._status_lbl.configure(
                    text=f"Error: {result.error_message}", text_color=ERROR)
            else:
                self._status_lbl.configure(
                    text=f"Downloaded: {result.title}", text_color=SUCCESS)
                self._msg_queue.put(("stats_completed", result))

        elif tag == "search_dl_error":
            msg, btn = data
            btn.configure(state="normal", text="Download")
            self._status_lbl.configure(text=f"Error: {msg}", text_color=ERROR)

    # ── Helpers ────────────────────────────────────────────────────

    def _populate_results(self, results: list) -> None:
        for w in self._results_scroll.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(
                self._results_scroll, text="No results found.",
                font=BODY_FONT, text_color=TEXT_DIM,
            ).grid(row=0, column=0, pady=PADDING_LG)
            return

        def _lookup(item, *names, default=None):
            if isinstance(item, dict):
                for name in names:
                    if name in item:
                        return item[name]
                return default
            for name in names:
                value = getattr(item, name, None)
                if value is not None:
                    return value
            return default

        for idx, item in enumerate(results):
            card = ctk.CTkFrame(self._results_scroll, **frame_style())
            card.grid(row=idx, column=0, sticky="ew", padx=2, pady=3)
            card.grid_columnconfigure(0, weight=1)

            # Title
            title = _lookup(item, "title") or "Unknown"
            if len(title) > 70:
                title = title[:67] + "..."
            ctk.CTkLabel(
                card, text=title, font=BODY_BOLD_FONT, text_color=TEXT, anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=PADDING_SM, pady=(PADDING_SM, 0))

            # Meta row: channel, duration, views
            dur = _lookup(item, "duration", default=0) or 0
            mins, secs = divmod(int(dur), 60)
            dur_str = f"{mins}:{secs:02d}"
            channel = _lookup(item, "channel", "uploader") or "Unknown"
            views = _lookup(item, "view_count", default=0) or 0
            if views >= 1_000_000:
                views_str = f"{views / 1_000_000:.1f}M views"
            elif views >= 1_000:
                views_str = f"{views / 1_000:.1f}K views"
            else:
                views_str = f"{views} views"

            meta = f"{channel}  -  {dur_str}  -  {views_str}"
            ctk.CTkLabel(
                card, text=meta, font=SMALL_FONT, text_color=TEXT_DIM, anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=PADDING_SM, pady=(0, PADDING_SM))

            # Download button
            url = _lookup(item, "url", "webpage_url", default="")
            dl_btn = ctk.CTkButton(
                card, text="Download", width=92,
                **button_style(accent=True),
            )
            dl_btn.configure(command=lambda u=url, b=dl_btn: self._download_result(u, b))
            dl_btn.grid(row=0, column=1, rowspan=2, padx=PADDING_SM, pady=PADDING_SM)
