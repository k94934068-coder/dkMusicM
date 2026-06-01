import threading
import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS
from ui.track_list import TrackListView
import database as db


class LibraryScreen(ctk.CTkFrame):
    def __init__(self, parent, vk_client, player, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.vk_client = vk_client
        self.player = player
        self._tab = "my"
        self._tracks: list[dict] = []
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 12))

        ctk.CTkLabel(
            header, text="Библиотека",
            font=("Segoe UI", 26, "bold"), text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(0, 12))

        tabs_row = ctk.CTkFrame(header, fg_color="transparent")
        tabs_row.pack(anchor="w")

        self._tab_btns = {}
        tabs = [("my", "Моя музыка"), ("favorites", "Избранное"), ("history", "История")]
        for key, label in tabs:
            btn = ctk.CTkButton(
                tabs_row, text=label, width=120, height=32,
                font=("Segoe UI", 12),
                fg_color=COLORS["bg_active"] if key == self._tab else "transparent",
                hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_primary"] if key == self._tab else COLORS["text_secondary"],
                corner_radius=8,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left", padx=2)
            self._tab_btns[key] = btn

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True)

        self._load_tab(self._tab)

    def _switch_tab(self, key: str):
        self._tab = key
        for k, btn in self._tab_btns.items():
            btn.configure(
                fg_color=COLORS["bg_active"] if k == key else "transparent",
                text_color=COLORS["text_primary"] if k == key else COLORS["text_secondary"],
            )
        self._load_tab(key)

    def _load_tab(self, key: str):
        for w in self._content.winfo_children():
            w.destroy()

        spinner = ctk.CTkLabel(
            self._content, text="Загрузка…",
            font=("Segoe UI", 13), text_color=COLORS["text_muted"],
        )
        spinner.pack(pady=32)

        def _worker():
            if key == "my":
                tracks = self.vk_client.get_my_music(count=100)
            elif key == "favorites":
                tracks = db.get_favorites()
            elif key == "history":
                tracks = db.get_history()
            else:
                tracks = []
            self.after(0, lambda: self._render(tracks))

        threading.Thread(target=_worker, daemon=True).start()

    def _render(self, tracks: list[dict]):
        for w in self._content.winfo_children():
            w.destroy()
        self._tracks = tracks

        if not tracks:
            ctk.CTkLabel(
                self._content, text="Треков пока нет",
                font=("Segoe UI", 14), text_color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        active_id = self.player.current_track.get("id") if self.player.current_track else None
        TrackListView(
            self._content, tracks, on_play=self._play,
            active_id=active_id,
        ).pack(fill="both", expand=True)

    def _play(self, track: dict):
        self.player.play_track(track, queue=self._tracks)
        db.add_to_history(track)

    def refresh(self):
        self._load_tab(self._tab)
