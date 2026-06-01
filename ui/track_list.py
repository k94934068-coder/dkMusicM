import io
import threading
import tkinter as tk
import customtkinter as ctk
import requests
from PIL import Image
from ui.theme import COLORS
import database as db


def fmt_dur(secs):
    s = int(secs or 0)
    return f"{s // 60}:{s % 60:02d}"


class TrackRow(ctk.CTkFrame):
    def __init__(self, parent, track: dict, index: int,
                 on_play, on_context=None, active=False, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_active"] if active else "transparent",
            corner_radius=6,
            height=52,
            **kwargs,
        )
        self.pack_propagate(False)
        self.track = track
        self.index = index
        self.on_play = on_play
        self.on_context = on_context
        self._cover_img = None
        self._active = active
        self._build()
        self._bind_hover()

    def _build(self):
        self.columnconfigure(2, weight=1)
        self.grid_propagate(False)

        num_lbl = ctk.CTkLabel(
            self, text=str(self.index + 1),
            font=("Segoe UI", 11), text_color=COLORS["text_muted"], width=28
        )
        num_lbl.grid(row=0, column=0, padx=(10, 4), pady=8)

        self._cover_label = ctk.CTkLabel(self, text="♫", width=36, height=36,
                                         font=("Segoe UI", 16),
                                         text_color=COLORS["text_muted"],
                                         corner_radius=4)
        self._cover_label.grid(row=0, column=1, padx=(0, 10))

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=2, sticky="ew", padx=(0, 8))

        title = self.track.get("title", "Unknown")
        artist = self.track.get("artist", "Unknown")

        ctk.CTkLabel(
            info, text=title[:48] + ("…" if len(title) > 48 else ""),
            font=("Segoe UI", 12, "bold" if self._active else "normal"),
            text_color=COLORS["accent"] if self._active else COLORS["text_primary"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=artist[:40] + ("…" if len(artist) > 40 else ""),
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(anchor="w")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=3, padx=(0, 12))

        is_fav = db.is_favorite(str(self.track.get("id", "")))
        self._fav_btn = ctk.CTkButton(
            right, text="♥" if is_fav else "♡", width=26, height=26,
            fg_color="transparent", hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent"] if is_fav else COLORS["text_muted"],
            font=("Segoe UI", 13), command=self._toggle_fav
        )
        self._fav_btn.pack(side="left", padx=2)

        ctk.CTkLabel(
            right, text=fmt_dur(self.track.get("duration", 0)),
            font=("Segoe UI", 11), text_color=COLORS["text_muted"], width=40
        ).pack(side="left")

        cover_url = self.track.get("cover_url")
        if cover_url:
            threading.Thread(target=self._load_cover, args=(cover_url,), daemon=True).start()

        self.bind("<Button-1>", lambda e: self.on_play(self.track))
        for w in self.winfo_children():
            w.bind("<Button-1>", lambda e: self.on_play(self.track))

    def _load_cover(self, url: str):
        try:
            resp = requests.get(url, timeout=6)
            img = Image.open(io.BytesIO(resp.content)).resize((36, 36), Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, size=(36, 36))
            self._cover_img = ctk_img
            self.after(0, lambda: self._cover_label.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def _toggle_fav(self):
        tid = str(self.track.get("id", ""))
        if db.is_favorite(tid):
            db.remove_from_favorites(tid)
            self._fav_btn.configure(text="♡", text_color=COLORS["text_muted"])
        else:
            db.add_to_favorites(self.track)
            self._fav_btn.configure(text="♥", text_color=COLORS["accent"])

    def _bind_hover(self):
        def enter(e):
            if not self._active:
                self.configure(fg_color=COLORS["bg_hover"])
        def leave(e):
            if not self._active:
                self.configure(fg_color="transparent")
        self.bind("<Enter>", enter)
        self.bind("<Leave>", leave)


class TrackListView(ctk.CTkScrollableFrame):
    def __init__(self, parent, tracks: list[dict], on_play, active_id=None, **kwargs):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            **kwargs,
        )
        self.tracks = tracks
        self.on_play = on_play
        self.active_id = str(active_id) if active_id else None
        self._render()

    def _render(self):
        for w in self.winfo_children():
            w.destroy()
        for i, track in enumerate(self.tracks):
            tid = str(track.get("id", ""))
            active = tid == self.active_id
            row = TrackRow(self, track, i, on_play=self.on_play, active=active)
            row.pack(fill="x", pady=1, padx=4)

    def refresh(self, tracks: list[dict], active_id=None):
        self.tracks = tracks
        self.active_id = str(active_id) if active_id else None
        self._render()
