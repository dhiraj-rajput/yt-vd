"""Main application window for the yt-vd GUI using CustomTkinter."""

from __future__ import annotations

import logging
import queue
from typing import Any

import customtkinter as ctk

from gui.frames.audio import AudioFrame
from gui.frames.download import DownloadFrame
from gui.frames.history import HistoryFrame
from gui.frames.playlist import PlaylistFrame
from gui.frames.search import SearchFrame
from gui.frames.settings import SettingsFrame
from gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_LIGHT,
    BG_MEDIUM,
    PADDING,
    PADDING_SM,
    SMALL_FONT,
    TEXT_DIM,
    apply_theme,
)

logger = logging.getLogger(__name__)


class YTDownloaderApp(ctk.CTk):
    """Main YouTube Downloader application window."""

    def __init__(self) -> None:
        super().__init__()

        # Apply dark theme
        apply_theme(self)

        # Main window configuration
        self.title("yt-vd - YouTube Downloader")
        self.geometry("980x720")
        self.minsize(860, 620)

        # Thread-safe communication queue
        self.msg_queue: queue.Queue = queue.Queue()

        # Overall aggregate statistics
        self.active_workers = 0
        self.total_completed = 0
        self.total_downloaded_bytes = 0

        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Tab Navigation ──────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(
            self,
            segmented_button_fg_color=BG_MEDIUM,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_color=BG_LIGHT,
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=PADDING, pady=(PADDING, PADDING_SM))

        # Add tabs
        self.tabview.add("Download")
        self.tabview.add("Playlist")
        self.tabview.add("Audio")
        self.tabview.add("Search")
        self.tabview.add("History")
        self.tabview.add("Settings")

        # Instantiate frame classes inside tabs
        self.download_frame = DownloadFrame(self.tabview.tab("Download"), self.msg_queue)
        self.download_frame.pack(fill="both", expand=True)

        self.playlist_frame = PlaylistFrame(self.tabview.tab("Playlist"), self.msg_queue)
        self.playlist_frame.pack(fill="both", expand=True)

        self.audio_frame = AudioFrame(self.tabview.tab("Audio"), self.msg_queue)
        self.audio_frame.pack(fill="both", expand=True)

        self.search_frame = SearchFrame(self.tabview.tab("Search"), self.msg_queue)
        self.search_frame.pack(fill="both", expand=True)

        self.history_frame = HistoryFrame(self.tabview.tab("History"), self.msg_queue)
        self.history_frame.pack(fill="both", expand=True)

        self.settings_frame = SettingsFrame(self.tabview.tab("Settings"), self.msg_queue)
        self.settings_frame.pack(fill="both", expand=True)

        # ── Status Bar (Bottom) ─────────────────────────────────────────────
        self.status_bar = ctk.CTkFrame(self, fg_color=BG_MEDIUM, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=SMALL_FONT,
            text_color=TEXT_DIM,
            anchor="w",
        )
        self.status_lbl.grid(row=0, column=0, padx=PADDING, pady=4, sticky="w")

        self.stats_lbl = ctk.CTkLabel(
            self.status_bar,
            text="Completed: 0  |  Downloaded: 0 B",
            font=SMALL_FONT,
            text_color=TEXT_DIM,
            anchor="e",
        )
        self.stats_lbl.grid(row=0, column=1, padx=PADDING, pady=4, sticky="e")

        # Start polling the thread queue
        self.poll_queue()

    def poll_queue(self) -> None:
        """Poll the thread-safe message queue for updates from background threads."""
        try:
            while True:
                tag, data = self.msg_queue.get_nowait()

                # Check target component based on tag prefix or exact tag
                if tag.startswith("playlist_"):
                    self.playlist_frame.handle_message(tag, data)
                elif tag.startswith("download_") or tag.startswith("video_info"):
                    self.download_frame.handle_message(tag, data)
                elif tag.startswith("audio_"):
                    self.audio_frame.handle_message(tag, data)
                elif tag.startswith("search_"):
                    self.search_frame.handle_message(tag, data)
                elif tag.startswith("history_"):
                    self.history_frame.handle_message(tag, data)
                elif tag.startswith("stats_"):
                    self.handle_stats_message(tag, data)

                self.msg_queue.task_done()
        except queue.Empty:
            pass

        # Schedule the next queue poll check in 100 ms
        self.after(100, self.poll_queue)

    def handle_stats_message(self, tag: str, data: Any) -> None:
        """Update aggregate download stats shown in the status bar."""
        if tag == "stats_completed":
            self.total_completed += 1
            if hasattr(data, "file_size") and data.file_size:
                self.total_downloaded_bytes += data.file_size

        # Update labels
        self.stats_lbl.configure(
            text=f"Completed: {self.total_completed}  |  Downloaded: {self.format_size(self.total_downloaded_bytes)}"
        )

    def set_status(self, message: str) -> None:
        """Set the status bar message text."""
        self.status_lbl.configure(text=message)

    @staticmethod
    def format_size(b: int) -> str:
        """Helper to format byte count to human-readable string."""
        if b <= 0:
            return "0 B"
        if b >= 1e9:
            return f"{b / 1e9:.1f} GB"
        if b >= 1e6:
            return f"{b / 1e6:.1f} MB"
        if b >= 1e3:
            return f"{b / 1e3:.1f} KB"
        return f"{b} B"


def main() -> None:
    """Entry point for the GUI application."""
    app = YTDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
