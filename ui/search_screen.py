import threading
import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS
from ui.track_list import TrackListView
import database as db


class SearchScreen(ctk.CTkFrame):
    def __init__(self, parent, vk_client, player, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.vk_client = vk_client
        self.player = player
        self._results: list[dict] = []
        self._search_after = None
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 16))

        ctk.CTkLabel(
            header, text="Поиск",
            font=("Segoe UI", 26, "bold"), text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        search_row = ctk.CTkFrame(header, fg_color=COLORS["bg_secondary"], corner_radius=12)
        search_row.pack(fill="x")

        ctk.CTkLabel(
            search_row, text="⌕", font=("Segoe UI", 18),
            text_color=COLORS["text_muted"], width=36,
        ).pack(side="left", padx=(12, 0))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_type)

        entry = ctk.CTkEntry(
            search_row,
            textvariable=self._search_var,
            placeholder_text="Треки, исполнители, альбомы…",
            font=("Segoe UI", 14),
            fg_color="transparent",
            border_width=0,
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            height=44,
        )
        entry.pack(side="left", fill="x", expand=True, padx=8)
        entry.bind("<Return>", lambda e: self._do_search())

        self._clear_btn = ctk.CTkButton(
            search_row, text="✕", width=30, height=30,
            fg_color="transparent", hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"], font=("Segoe UI", 13),
            command=self._clear,
        )
        self._clear_btn.pack(side="right", padx=8)

        self._results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._results_frame.pack(fill="both", expand=True)

        self._status_label = ctk.CTkLabel(
            self._results_frame,
            text="Начните вводить запрос",
            font=("Segoe UI", 14), text_color=COLORS["text_muted"],
        )
        self._status_label.pack(pady=40)

        self._list_frame: TrackListView | None = None

    def _on_type(self, *_):
        if self._search_after:
            self.after_cancel(self._search_after)
        query = self._search_var.get().strip()
        if len(query) >= 2:
            self._search_after = self.after(500, self._do_search)
        elif not query:
            self._show_status("Начните вводить запрос")

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query:
            return
        self._show_status(f"Поиск «{query}»…")

        def _worker():
            results = self.vk_client.search(query, count=50)
            self.after(0, lambda: self._show_results(results, query))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_results(self, results: list[dict], query: str):
        self._results = results
        for w in self._results_frame.winfo_children():
            w.destroy()
        self._list_frame = None

        if not results:
            ctk.CTkLabel(
                self._results_frame,
                text=f"По запросу «{query}» ничего не найдено",
                font=("Segoe UI", 14), text_color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        header = ctk.CTkFrame(self._results_frame, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(12, 8))
        ctk.CTkLabel(
            header,
            text=f"Результаты ({len(results)} треков)",
            font=("Segoe UI", 13), text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        self._list_frame = TrackListView(
            self._results_frame, results, on_play=self._play,
        )
        self._list_frame.pack(fill="both", expand=True, padx=0)

    def _show_status(self, text: str):
        for w in self._results_frame.winfo_children():
            w.destroy()
        self._status_label = ctk.CTkLabel(
            self._results_frame, text=text,
            font=("Segoe UI", 14), text_color=COLORS["text_muted"],
        )
        self._status_label.pack(pady=40)

    def _clear(self):
        self._search_var.set("")
        self._show_status("Начните вводить запрос")

    def _play(self, track: dict):
        self.player.play_track(track, queue=self._results)
        db.add_to_history(track)

    def focus_search(self):
        self._search_var.set("")
        self.after(100, lambda: self.focus())
