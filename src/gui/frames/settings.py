"""Settings tab — persistent configuration for yt-vd defaults."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from constants import (
    DEFAULT_PARALLEL_WORKERS,
)
from gui.theme import (
    BODY_FONT,
    ERROR,
    PADDING,
    PADDING_SM,
    SMALL_FONT,
    SUCCESS,
    TEXT,
    TEXT_DIM,
    button_style,
    checkbox_style,
    dropdown_style,
    entry_style,
    frame_style,
    label_style,
    slider_style,
)


class SettingsFrame(ctk.CTkFrame):
    """Application settings / preferences tab."""

    def __init__(self, master: ctk.CTkBaseClass, msg_queue: queue.Queue, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._msg_queue = msg_queue

        self.grid_columnconfigure(0, weight=1)
        row = 0

        # ── Heading ───────────────────────────────────────────────
        ctk.CTkLabel(self, text="Settings", **label_style(heading=True)).grid(
            row=row, column=0, sticky="w", padx=PADDING, pady=(PADDING, PADDING_SM))
        row += 1

        # ── Settings card ─────────────────────────────────────────
        card = ctk.CTkFrame(self, **frame_style())
        card.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        card.grid_columnconfigure(1, weight=1)
        row += 1

        cr = 0  # card row counter

        # Default quality
        self._quality_var = ctk.StringVar(value="Best")
        cr = self._add_dropdown(card, cr, "Default Quality",
            ["Best", "High (1080p)", "Medium (720p)", "Better (480p)", "Low (360p)", "Lowest"],
            self._quality_var)

        # Default format
        self._format_var = ctk.StringVar(value="MP4")
        cr = self._add_dropdown(card, cr, "Default Format",
            ["MP4", "MKV", "WEBM"], self._format_var)

        # Default output directory
        dir_row = ctk.CTkFrame(card, fg_color="transparent")
        ctk.CTkLabel(card, text="Default Output Dir", **label_style(dim=True)).grid(
            row=cr, column=0, sticky="w", padx=PADDING, pady=PADDING_SM)
        dir_row.grid(row=cr, column=1, sticky="ew", padx=(0, PADDING), pady=PADDING_SM)
        dir_row.grid_columnconfigure(0, weight=1)
        cr += 1

        self._dir_entry = ctk.CTkEntry(dir_row, **entry_style())
        self._dir_entry.insert(0, str(Path.home() / "Downloads"))
        self._dir_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(dir_row, text="Browse", width=80, command=self._browse_dir,
                       **button_style()).grid(row=0, column=1, padx=(6, 0))

        # Parallel workers
        ctk.CTkLabel(card, text="Parallel Workers", **label_style(dim=True)).grid(
            row=cr, column=0, sticky="w", padx=PADDING, pady=PADDING_SM)
        w_frame = ctk.CTkFrame(card, fg_color="transparent")
        w_frame.grid(row=cr, column=1, sticky="w", padx=(0, PADDING), pady=PADDING_SM)
        cr += 1

        max_w = os.cpu_count() or 4
        self._workers_var = ctk.IntVar(value=DEFAULT_PARALLEL_WORKERS)
        self._workers_slider = ctk.CTkSlider(
            w_frame, from_=1, to=max_w, number_of_steps=max_w - 1,
            variable=self._workers_var, width=160,
            command=self._on_workers_changed, **slider_style(),
        )
        self._workers_slider.pack(side="left")
        self._workers_lbl = ctk.CTkLabel(
            w_frame, text=str(DEFAULT_PARALLEL_WORKERS),
            width=30, font=BODY_FONT, text_color=TEXT,
        )
        self._workers_lbl.pack(side="left", padx=(8, 0))

        # Default audio format
        self._audio_fmt_var = ctk.StringVar(value="MP3")
        cr = self._add_dropdown(card, cr, "Audio Format",
            ["MP3", "M4A", "FLAC", "WAV", "Opus"], self._audio_fmt_var)

        # Default audio bitrate
        self._audio_br_var = ctk.StringVar(value="192k")
        cr = self._add_dropdown(card, cr, "Audio Bitrate",
            ["128k", "192k", "256k", "320k"], self._audio_br_var)

        # Subtitle language
        ctk.CTkLabel(card, text="Subtitle Language", **label_style(dim=True)).grid(
            row=cr, column=0, sticky="w", padx=PADDING, pady=PADDING_SM)
        self._sub_lang_entry = ctk.CTkEntry(card, placeholder_text="en", width=120, **entry_style())
        self._sub_lang_entry.grid(row=cr, column=1, sticky="w", padx=(0, PADDING), pady=PADDING_SM)
        cr += 1

        # ── Checkboxes ────────────────────────────────────────────
        cb_card = ctk.CTkFrame(self, **frame_style())
        cb_card.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING_SM)
        row += 1

        self._embed_thumb_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cb_card, text="Embed Thumbnail", variable=self._embed_thumb_var,
                         **checkbox_style()).grid(
            row=0, column=0, padx=PADDING, pady=PADDING_SM, sticky="w")

        self._embed_meta_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(cb_card, text="Embed Metadata", variable=self._embed_meta_var,
                         **checkbox_style()).grid(
            row=0, column=1, padx=PADDING, pady=PADDING_SM, sticky="w")

        self._sponsorblock_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_card, text="SponsorBlock", variable=self._sponsorblock_var,
                         **checkbox_style()).grid(
            row=0, column=2, padx=PADDING, pady=PADDING_SM, sticky="w")

        # ── Action buttons ────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=PADDING)
        row += 1

        self._save_btn = ctk.CTkButton(
            btn_row, text="Save Settings", width=160,
            command=self._save_settings, **button_style(accent=True))
        self._save_btn.pack(side="left", padx=(0, 12))

        self._reset_btn = ctk.CTkButton(
            btn_row, text="Reset to Defaults", width=160,
            command=self._reset_defaults, **button_style())
        self._reset_btn.pack(side="left")

        # ── Status ────────────────────────────────────────────────
        self._status_lbl = ctk.CTkLabel(
            self, text="", font=SMALL_FONT, text_color=TEXT_DIM, anchor="w")
        self._status_lbl.grid(row=row, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))

        # Load saved config on init
        self._load_config()

    # ── Helpers ────────────────────────────────────────────────────

    def _add_dropdown(
        self, parent: ctk.CTkFrame, row: int, label: str,
        values: list[str], var: ctk.StringVar,
    ) -> int:
        ctk.CTkLabel(parent, text=label, **label_style(dim=True)).grid(
            row=row, column=0, sticky="w", padx=PADDING, pady=PADDING_SM)
        ctk.CTkOptionMenu(
            parent, variable=var, values=values, width=160, **dropdown_style(),
        ).grid(row=row, column=1, sticky="w", padx=(0, PADDING), pady=PADDING_SM)
        return row + 1

    def _browse_dir(self) -> None:
        d = filedialog.askdirectory(initialdir=self._dir_entry.get())
        if d:
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, d)

    def _on_workers_changed(self, val: float) -> None:
        self._workers_lbl.configure(text=str(int(val)))

    # ── Config persistence ─────────────────────────────────────────

    def _get_config_dict(self) -> dict:
        return {
            "quality": self._quality_var.get(),
            "format": self._format_var.get(),
            "output_dir": self._dir_entry.get().strip(),
            "parallel_workers": self._workers_var.get(),
            "audio_format": self._audio_fmt_var.get(),
            "audio_bitrate": self._audio_br_var.get(),
            "subtitle_language": self._sub_lang_entry.get().strip() or "en",
            "embed_thumbnail": self._embed_thumb_var.get(),
            "embed_metadata": self._embed_meta_var.get(),
            "sponsorblock": self._sponsorblock_var.get(),
        }

    def _apply_config(self, cfg: dict) -> None:
        if "quality" in cfg:
            self._quality_var.set(cfg["quality"])
        if "format" in cfg:
            self._format_var.set(cfg["format"])
        if "output_dir" in cfg:
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, cfg["output_dir"])
        if "parallel_workers" in cfg:
            self._workers_var.set(cfg["parallel_workers"])
            self._workers_lbl.configure(text=str(cfg["parallel_workers"]))
        if "audio_format" in cfg:
            self._audio_fmt_var.set(cfg["audio_format"])
        if "audio_bitrate" in cfg:
            self._audio_br_var.set(cfg["audio_bitrate"])
        if "subtitle_language" in cfg:
            self._sub_lang_entry.delete(0, "end")
            self._sub_lang_entry.insert(0, cfg["subtitle_language"])
        if "embed_thumbnail" in cfg:
            self._embed_thumb_var.set(cfg["embed_thumbnail"])
        if "embed_metadata" in cfg:
            self._embed_meta_var.set(cfg["embed_metadata"])
        if "sponsorblock" in cfg:
            self._sponsorblock_var.set(cfg["sponsorblock"])

    def _save_settings(self) -> None:
        cfg = self._get_config_dict()
        self._save_btn.configure(state="disabled")
        threading.Thread(target=self._save_worker, args=(cfg,), daemon=True).start()

    def _save_worker(self, cfg: dict) -> None:
        try:
            from core.config import save_config  # type: ignore[import]
            save_config(cfg)
            self._msg_queue.put(("settings_saved", None))
        except Exception as exc:
            self._msg_queue.put(("settings_error", str(exc)))

    def _load_config(self) -> None:
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self) -> None:
        try:
            from core.config import load_config  # type: ignore[import]
            cfg = load_config()
            self._msg_queue.put(("settings_loaded", cfg))
        except Exception:
            pass  # No saved config is fine, use defaults

    def _reset_defaults(self) -> None:
        defaults = {
            "quality": "Best",
            "format": "MP4",
            "output_dir": str(Path.home() / "Downloads"),
            "parallel_workers": DEFAULT_PARALLEL_WORKERS,
            "audio_format": "MP3",
            "audio_bitrate": "192k",
            "subtitle_language": "en",
            "embed_thumbnail": True,
            "embed_metadata": True,
            "sponsorblock": False,
        }
        self._apply_config(defaults)
        self._status_lbl.configure(text="Reset to defaults.", text_color=SUCCESS)

    # ── Queue message handler ──────────────────────────────────────

    def handle_message(self, tag: str, data) -> None:
        if tag == "settings_saved":
            self._save_btn.configure(state="normal")
            self._status_lbl.configure(text="Settings saved.", text_color=SUCCESS)

        elif tag == "settings_loaded":
            if data:
                self._apply_config(data)

        elif tag == "settings_error":
            self._save_btn.configure(state="normal")
            self._status_lbl.configure(text=f"Error: {data}", text_color=ERROR)
