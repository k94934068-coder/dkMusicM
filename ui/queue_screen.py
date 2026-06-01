import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS
import database as db


def fmt_dur(secs):
    s = int(secs or 0)
    return f"{s // 60}:{s % 60:02d}"


class QueueScreen(ctk.CTkFrame):
    def __init__(self, parent, player, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.player = player
        self._build()
        self._render()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            header, text="Очередь",
            font=("Segoe UI", 26, "bold"), text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Очистить", width=90, height=30,
            fg_color="transparent", hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"], font=("Segoe UI", 12),
            border_width=1, border_color=COLORS["border"],
            corner_radius=6, command=self._clear_queue,
        ).pack(side="right")

        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _render(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        queue = self.player.get_queue()
        current = self.player.current_track
        current_id = str(current.get("id", "")) if current else None

        if not queue:
            ctk.CTkLabel(
                self._list_frame, text="Очередь пуста",
                font=("Segoe UI", 14), text_color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        for i, track in enumerate(queue):
            tid = str(track.get("id", ""))
            is_current = tid == current_id

            row = ctk.CTkFrame(
                self._list_frame,
                fg_color=COLORS["bg_active"] if is_current else "transparent",
                corner_radius=6, height=50,
            )
            row.pack(fill="x", pady=2, padx=4)
            row.pack_propagate(False)

            if is_current:
                ctk.CTkLabel(
                    row, text="▶", font=("Segoe UI", 12),
                    text_color=COLORS["accent"], width=20,
                ).pack(side="left", padx=(10, 4))
            else:
                ctk.CTkLabel(
                    row, text=str(i + 1), font=("Segoe UI", 11),
                    text_color=COLORS["text_muted"], width=20,
                ).pack(side="left", padx=(10, 4))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=4, pady=6)

            title = track.get("title", "Unknown")
            artist = track.get("artist", "Unknown")
            ctk.CTkLabel(
                info, text=title[:45] + ("…" if len(title) > 45 else ""),
                font=("Segoe UI", 12, "bold" if is_current else "normal"),
                text_color=COLORS["accent"] if is_current else COLORS["text_primary"],
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info, text=artist[:35],
                font=("Segoe UI", 11), text_color=COLORS["text_secondary"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                row, text=fmt_dur(track.get("duration", 0)),
                font=("Segoe UI", 11), text_color=COLORS["text_muted"], width=40,
            ).pack(side="right", padx=(0, 8))

            if not is_current:
                del_btn = ctk.CTkButton(
                    row, text="✕", width=24, height=24,
                    fg_color="transparent", hover_color="#2A1010",
                    text_color=COLORS["text_muted"], font=("Segoe UI", 11),
                    command=lambda idx=i: self._remove(idx),
                )
                del_btn.pack(side="right", padx=4)

    def _remove(self, index: int):
        self.player.remove_from_queue(index)
        self._render()

    def _clear_queue(self):
        self.player.clear_queue()
        self._render()

    def refresh(self):
        self._render()
