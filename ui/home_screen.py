import io
import threading
import tkinter as tk
import customtkinter as ctk
import requests
from PIL import Image
from ui.theme import COLORS, CARD_WIDTH, CARD_HEIGHT
from ui.track_list import TrackListView


class HomeScreen(ctk.CTkFrame):
    def __init__(self, parent, vk_client, player, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.vk_client = vk_client
        self.player = player
        self._my_tracks: list[dict] = []
        self._trending: list[dict] = []
        self._build()
        self._load_data()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        self._scroll = scroll

        ctk.CTkLabel(
            scroll, text="Добро пожаловать",
            font=("Segoe UI", 26, "bold"), text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            scroll, text="Ваша музыка и рекомендации",
            font=("Segoe UI", 13), text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=24, pady=(0, 20))

        self._my_section_label = ctk.CTkLabel(
            scroll, text="Моя музыка",
            font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"],
        )
        self._my_section_label.pack(anchor="w", padx=24, pady=(0, 8))

        self._my_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._my_frame.pack(fill="x", padx=24, pady=(0, 24))

        self._loading_my = ctk.CTkLabel(
            self._my_frame, text="Загрузка…",
            font=("Segoe UI", 12), text_color=COLORS["text_muted"],
        )
        self._loading_my.pack(anchor="w")

        ctk.CTkLabel(
            scroll, text="Хиты и тренды",
            font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self._trending_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._trending_frame.pack(fill="x", padx=24, pady=(0, 24))

        self._loading_trend = ctk.CTkLabel(
            self._trending_frame, text="Загрузка…",
            font=("Segoe UI", 12), text_color=COLORS["text_muted"],
        )
        self._loading_trend.pack(anchor="w")

    def _load_data(self):
        def _worker():
            try:
                self._my_tracks = self.vk_client.get_my_music(count=20)
            except Exception:
                self._my_tracks = []
            try:
                self._trending = self.vk_client.get_trending(count=20)
            except Exception:
                self._trending = []
            self.after(0, self._render_data)

        threading.Thread(target=_worker, daemon=True).start()

    def _render_data(self):
        self._loading_my.destroy()
        self._loading_trend.destroy()

        if self._my_tracks:
            TrackListView(
                self._my_frame, self._my_tracks[:10],
                on_play=self._play_track,
            ).pack(fill="x")
        else:
            ctk.CTkLabel(
                self._my_frame, text="Музыка не найдена",
                text_color=COLORS["text_muted"], font=("Segoe UI", 12),
            ).pack(anchor="w")

        if self._trending:
            TrackListView(
                self._trending_frame, self._trending[:10],
                on_play=lambda t: self._play_from(t, self._trending),
            ).pack(fill="x")
        else:
            ctk.CTkLabel(
                self._trending_frame, text="Треки не найдены",
                text_color=COLORS["text_muted"], font=("Segoe UI", 12),
            ).pack(anchor="w")

    def _play_track(self, track: dict):
        self.player.play_track(track, queue=self._my_tracks)
        import database as db
        db.add_to_history(track)

    def _play_from(self, track: dict, queue: list):
        self.player.play_track(track, queue=queue)
        import database as db
        db.add_to_history(track)

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()
        self._load_data()
