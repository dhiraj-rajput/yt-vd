"""URL input widget with paste button and validation indicator."""

from __future__ import annotations

import re
from collections.abc import Callable

import customtkinter as ctk

from constants import YOUTUBE_URL_PATTERNS
from gui.theme import (
    ERROR,
    SUCCESS,
    TEXT_DIM,
    button_style,
    entry_style,
)

_URL_RE = re.compile("|".join(YOUTUBE_URL_PATTERNS))


class URLInput(ctk.CTkFrame):
    """Composite widget: URL text entry + paste button + validation badge."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        placeholder: str = "Paste YouTube URL here...",
        on_valid_url: Callable[[str], None] | None = None,
        height: int = 44,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_valid_url = on_valid_url
        self._last_valid_url: str = ""

        # ── Row layout ────────────────────────────────────────────
        self.grid_columnconfigure(1, weight=1)

        # Validation indicator (left)
        self._indicator = ctk.CTkLabel(
            self, text="", width=24, font=("Segoe UI", 16),
            text_color=TEXT_DIM,
        )
        self._indicator.grid(row=0, column=0, padx=(0, 6))

        # URL entry (centre – stretches)
        entry_kwargs = entry_style()
        entry_kwargs["height"] = height
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            **entry_kwargs,
        )
        self._entry.grid(row=0, column=1, sticky="ew")
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<<Paste>>", lambda _: self.after(50, self._on_key))
        self._entry.bind("<Control-v>", lambda _: self.after(50, self._on_key))

        # Paste button (right)
        btn_kwargs = button_style()
        btn_kwargs["height"] = height
        self._paste_btn = ctk.CTkButton(
            self, text="Paste", width=42,
            command=self._paste_clipboard,
            **btn_kwargs,
        )
        self._paste_btn.grid(row=0, column=2, padx=(6, 0))

    # ── Public API ─────────────────────────────────────────────────

    def get_url(self) -> str:
        """Return the current URL text."""
        return str(self._entry.get()).strip()

    def set_url(self, url: str) -> None:
        """Programmatically set the URL."""
        self._entry.delete(0, "end")
        self._entry.insert(0, url)
        self._validate(url)

    def clear(self) -> None:
        """Clear the field and reset indicator."""
        self._entry.delete(0, "end")
        self._indicator.configure(text="", text_color=TEXT_DIM)
        self._last_valid_url = ""

    # ── Internals ──────────────────────────────────────────────────

    def _paste_clipboard(self) -> None:
        try:
            text = self.clipboard_get().strip()
        except Exception:
            return
        if text:
            self._entry.delete(0, "end")
            self._entry.insert(0, text)
            self._validate(text)

    def _on_key(self, _event=None) -> None:
        self._validate(self._entry.get().strip())

    def _validate(self, url: str) -> None:
        if not url:
            self._indicator.configure(text="", text_color=TEXT_DIM)
            return

        if _URL_RE.search(url):
            self._indicator.configure(text="OK", text_color=SUCCESS)
            if url != self._last_valid_url:
                self._last_valid_url = url
                if self._on_valid_url:
                    self._on_valid_url(url)
        else:
            self._indicator.configure(text="X", text_color=ERROR)
