import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS
import database as db


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, player, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.player = player
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True, padx=0)

        ctk.CTkLabel(
            scroll, text="Настройки",
            font=("Segoe UI", 26, "bold"), text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=24, pady=(24, 20))

        self._section(scroll, "Воспроизведение")

        speed_row = self._row(scroll, "Скорость по умолчанию")
        speed_var = tk.StringVar(value=f"{db.get_setting('playback_speed', 1.0)}×")
        ctk.CTkOptionMenu(
            speed_row, values=["0.75×", "1.0×", "1.25×", "1.5×"],
            variable=speed_var, width=100, height=30,
            fg_color=COLORS["bg_secondary"], button_color=COLORS["bg_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_secondary"], font=("Segoe UI", 12),
            command=lambda v: db.set_setting("playback_speed", float(v.replace("×", ""))),
        ).pack(side="right")

        self._section(scroll, "Интерфейс")
        theme_row = self._row(scroll, "Тёмная тема")
        ctk.CTkSwitch(
            theme_row, text="", width=40,
            fg_color=COLORS["bg_active"], progress_color=COLORS["accent"],
            command=lambda: None,
        ).pack(side="right")

        self._section(scroll, "О приложении")
        ctk.CTkLabel(
            scroll, text="Music Minimal — минималистичный музыкальный плеер\nна основе VK Музыки",
            font=("Segoe UI", 12), text_color=COLORS["text_muted"],
            justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            scroll, text="Версия 1.0.0",
            font=("Segoe UI", 11), text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=24, pady=(0, 24))

    def _section(self, parent, title: str):
        ctk.CTkLabel(
            parent, text=title,
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(16, 4))
        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=24, pady=(0, 8))

    def _row(self, parent, label: str) -> ctk.CTkFrame:
        row = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        row.pack(fill="x", padx=24, pady=2)
        row.pack_propagate(False)
        ctk.CTkLabel(
            row, text=label, font=("Segoe UI", 13),
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(side="left")
        return row
