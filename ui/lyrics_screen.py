import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS

SAMPLE_LINES = [
    "Текст песни недоступен.",
    "",
    "VK Музыка не предоставляет тексты",
    "через данный API.",
    "",
    "Попробуйте найти текст песни",
    "на сайте genius.com",
]


class LyricsWindow(ctk.CTkToplevel):
    def __init__(self, parent, track: dict, player, **kwargs):
        super().__init__(parent, **kwargs)
        self.track = track
        self.player = player
        self._lines = SAMPLE_LINES
        self._current_line = 0

        self.title(f"Текст — {track.get('title', '')} · {track.get('artist', '')}")
        self.geometry("560x700")
        self.configure(fg_color=COLORS["bg"])
        self.resizable(True, True)
        self.grab_set()

        self._build()
        self._update_loop()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=f"{self.track.get('title', '—')}",
            font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"],
        ).pack(side="left", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            header,
            text=f"{self.track.get('artist', '—')}",
            font=("Segoe UI", 12), text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 20), pady=(16, 4))

        ctk.CTkButton(
            header, text="✕", width=30, height=30,
            fg_color="transparent", hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"], font=("Segoe UI", 14),
            command=self.destroy,
        ).pack(side="right", padx=12, pady=12)

        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x")

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._line_labels: list[ctk.CTkLabel] = []
        for i, line in enumerate(self._lines):
            lbl = ctk.CTkLabel(
                self._scroll,
                text=line if line else " ",
                font=("Segoe UI", 15 if i == 0 else 14),
                text_color=COLORS["text_muted"],
                wraplength=480,
                justify="center",
                anchor="center",
            )
            lbl.pack(pady=4, padx=24, anchor="center")
            self._line_labels.append(lbl)

        self._highlight(0)

    def _highlight(self, idx: int):
        for i, lbl in enumerate(self._line_labels):
            if i == idx and self._lines[i]:
                lbl.configure(
                    text_color=COLORS["text_primary"],
                    font=("Segoe UI", 17, "bold"),
                )
            elif i < idx:
                lbl.configure(
                    text_color=COLORS["text_muted"],
                    font=("Segoe UI", 13),
                )
            else:
                lbl.configure(
                    text_color="#444444",
                    font=("Segoe UI", 13),
                )

    def _update_loop(self):
        if not self.winfo_exists():
            return
        try:
            pos = self.player.position
            dur = self.player.duration
            if dur > 0 and self._lines:
                frac = pos / dur
                line_idx = int(frac * len(self._lines))
                line_idx = max(0, min(line_idx, len(self._lines) - 1))
                if line_idx != self._current_line:
                    self._current_line = line_idx
                    self._highlight(line_idx)
        except Exception:
            pass
        self.after(1000, self._update_loop)
