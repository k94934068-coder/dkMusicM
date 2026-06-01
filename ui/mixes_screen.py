import threading
import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS
from ui.track_list import TrackListView
import database as db

MIX_QUERIES = [
    ("Русские хиты", "русские хиты 2024"),
    ("Для работы", "music for work focus"),
    ("Вечеринка", "вечеринка хиты"),
    ("Меланхолия", "меланхолия грустные"),
    ("Классика русского рока", "русский рок классика"),
    ("Lo-fi Chill", "lofi chill beats"),
    ("Поп хиты", "поп хиты 2024"),
    ("Рэп и хип-хоп", "рэп хип хоп 2024"),
]


class MixCard(ctk.CTkFrame):
    def __init__(self, parent, name: str, query: str, on_play, **kwargs):
        super().__init__(
            parent,
            width=200, height=100,
            fg_color=COLORS["card_bg"],
            corner_radius=12,
            **kwargs,
        )
        self.pack_propagate(False)
        self.name = name
        self.query = query
        self.on_play = on_play
        self._build()
        self._bind_hover()

    def _build(self):
        ctk.CTkLabel(
            self, text="◈",
            font=("Segoe UI", 28), text_color=COLORS["accent"],
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            self, text=self.name,
            font=("Segoe UI", 12, "bold"), text_color=COLORS["text_primary"],
            wraplength=170,
        ).pack(pady=(0, 4))

        ctk.CTkButton(
            self, text="Слушать", height=28, corner_radius=6,
            fg_color=COLORS["bg_active"], hover_color=COLORS["accent"],
            text_color=COLORS["text_secondary"], font=("Segoe UI", 11),
            command=lambda: self.on_play(self.query),
        ).pack(pady=(0, 12))

    def _bind_hover(self):
        def enter(e):
            self.configure(fg_color=COLORS["card_hover"])
        def leave(e):
            self.configure(fg_color=COLORS["card_bg"])
        self.bind("<Enter>", enter)
        self.bind("<Leave>", leave)


class MixesScreen(ctk.CTkFrame):
    def __init__(self, parent, vk_client, player, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.vk_client = vk_client
        self.player = player
        self._current_tracks: list[dict] = []
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        ctk.CTkLabel(
            scroll, text="Миксы",
            font=("Segoe UI", 26, "bold"), text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            scroll, text="Персональные подборки треков",
            font=("Segoe UI", 13), text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=24, pady=(0, 20))

        grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        grid_frame.pack(fill="x", padx=24, pady=(0, 24))

        for i, (name, query) in enumerate(MIX_QUERIES):
            card = MixCard(grid_frame, name, query, on_play=self._on_mix_click)
            card.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")

        for col in range(4):
            grid_frame.columnconfigure(col, weight=1)

        sep = ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=24, pady=(0, 16))

        self._mix_label = ctk.CTkLabel(
            scroll, text="",
            font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"],
        )
        self._mix_label.pack(anchor="w", padx=24, pady=(0, 8))

        self._list_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self._list_container.pack(fill="x", padx=0, pady=(0, 24))

    def _on_mix_click(self, query: str):
        mix_name = next((n for n, q in MIX_QUERIES if q == query), query)
        self._mix_label.configure(text=f"Сейчас: {mix_name}")
        for w in self._list_container.winfo_children():
            w.destroy()
        loading = ctk.CTkLabel(
            self._list_container, text="Загрузка микса…",
            font=("Segoe UI", 12), text_color=COLORS["text_muted"],
        )
        loading.pack(pady=16, padx=24)

        def _worker():
            tracks = self.vk_client.search(query, count=30)
            self._current_tracks = tracks
            self.after(0, lambda: self._render_mix(tracks))

        threading.Thread(target=_worker, daemon=True).start()

    def _render_mix(self, tracks: list[dict]):
        for w in self._list_container.winfo_children():
            w.destroy()
        if not tracks:
            ctk.CTkLabel(
                self._list_container, text="Треки не найдены",
                font=("Segoe UI", 12), text_color=COLORS["text_muted"],
            ).pack(pady=16, padx=24)
            return
        TrackListView(
            self._list_container, tracks, on_play=self._play,
        ).pack(fill="x")

    def _play(self, track: dict):
        self.player.play_track(track, queue=self._current_tracks)
        db.add_to_history(track)
