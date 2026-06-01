import io
import time
import threading
import tkinter as tk
import customtkinter as ctk
import requests
from PIL import Image, ImageTk
from ui.theme import COLORS, FONTS, PLAYER_HEIGHT, COVER_SIZE
import database as db
from downloader import download_track


def fmt_time(secs: float) -> str:
    s = int(secs)
    return f"{s // 60}:{s % 60:02d}"


class NowPlayingBar(ctk.CTkFrame):
    def __init__(self, parent, player, on_lyrics, **kwargs):
        super().__init__(
            parent,
            height=PLAYER_HEIGHT,
            fg_color=COLORS["player_bg"],
            corner_radius=0,
            **kwargs,
        )
        self.player = player
        self.on_lyrics = on_lyrics
        self._cover_img = None
        self._current_track = None
        self._dragging = False
        self._dl_after = None
        self.pack_propagate(False)
        self._build()
        self._bind_player()

    def _build(self):
        top_sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        top_sep.pack(fill="x")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=8)
        main.columnconfigure(0, weight=1, minsize=240)
        main.columnconfigure(1, weight=2)
        main.columnconfigure(2, weight=1, minsize=260)
        main.rowconfigure(0, weight=1)

        self._build_left(main)
        self._build_center(main)
        self._build_right(main)

    def _build_left(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsw")

        self._cover_label = ctk.CTkLabel(frame, text="", width=COVER_SIZE, height=COVER_SIZE)
        self._cover_label.configure(corner_radius=6)
        self._cover_label.pack(side="left", padx=(0, 12))

        info = ctk.CTkFrame(frame, fg_color="transparent")
        info.pack(side="left", fill="y")

        self._title_var = tk.StringVar(value="—")
        self._artist_var = tk.StringVar(value="—")

        self._title_label = ctk.CTkLabel(
            info, textvariable=self._title_var,
            font=("Segoe UI", 13, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w", width=160,
        )
        self._title_label.pack(anchor="w")

        self._artist_label = ctk.CTkLabel(
            info, textvariable=self._artist_var,
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
            anchor="w", width=160,
        )
        self._artist_label.pack(anchor="w")

        fav_frame = ctk.CTkFrame(info, fg_color="transparent")
        fav_frame.pack(anchor="w", pady=(2, 0))
        self._fav_btn = ctk.CTkButton(
            fav_frame, text="♡", width=28, height=22,
            fg_color="transparent", hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"], font=("Segoe UI", 14),
            command=self._toggle_favorite,
        )
        self._fav_btn.pack(side="left")

    def _build_center(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=1, sticky="ns")

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(anchor="center")

        btn_cfg = dict(width=36, height=36, fg_color="transparent",
                       hover_color=COLORS["bg_hover"], corner_radius=18)

        self._shuffle_btn = ctk.CTkButton(
            controls, text="⇌", font=("Segoe UI", 16),
            text_color=COLORS["text_muted"], command=self._toggle_shuffle, **btn_cfg
        )
        self._shuffle_btn.pack(side="left", padx=2)

        ctk.CTkButton(
            controls, text="⏮", font=("Segoe UI", 18),
            text_color=COLORS["text_secondary"], command=self.player.prev, **btn_cfg
        ).pack(side="left", padx=2)

        self._play_btn = ctk.CTkButton(
            controls, text="▶", font=("Segoe UI", 20),
            text_color=COLORS["text_primary"],
            width=44, height=44,
            fg_color=COLORS["bg_active"],
            hover_color=COLORS["bg_hover"],
            corner_radius=22,
            command=self.player.play_pause,
        )
        self._play_btn.pack(side="left", padx=6)

        ctk.CTkButton(
            controls, text="⏭", font=("Segoe UI", 18),
            text_color=COLORS["text_secondary"], command=self.player.next, **btn_cfg
        ).pack(side="left", padx=2)

        self._repeat_btn = ctk.CTkButton(
            controls, text="↻", font=("Segoe UI", 16),
            text_color=COLORS["text_muted"], command=self._cycle_repeat, **btn_cfg
        )
        self._repeat_btn.pack(side="left", padx=2)

        prog_frame = ctk.CTkFrame(frame, fg_color="transparent")
        prog_frame.pack(anchor="center", fill="x", pady=(4, 0))

        self._time_var = tk.StringVar(value="0:00")
        ctk.CTkLabel(prog_frame, textvariable=self._time_var,
                     font=("Segoe UI", 10), text_color=COLORS["text_muted"],
                     width=36).pack(side="left")

        self._progress = ctk.CTkSlider(
            prog_frame, from_=0, to=100, height=4,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["progress_fill"],
            button_color=COLORS["text_primary"],
            button_hover_color=COLORS["accent"],
            command=self._on_seek,
        )
        self._progress.set(0)
        self._progress.pack(side="left", fill="x", expand=True, padx=6)
        self._progress.bind("<ButtonPress-1>", lambda e: setattr(self, "_dragging", True))
        self._progress.bind("<ButtonRelease-1>", self._on_seek_release)

        self._dur_var = tk.StringVar(value="0:00")
        ctk.CTkLabel(prog_frame, textvariable=self._dur_var,
                     font=("Segoe UI", 10), text_color=COLORS["text_muted"],
                     width=36).pack(side="left")

    def _build_right(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=2, sticky="nse")

        btn_cfg = dict(width=32, height=32, fg_color="transparent",
                       hover_color=COLORS["bg_hover"], corner_radius=6)

        ctk.CTkButton(
            frame, text="♪", font=("Segoe UI", 16),
            text_color=COLORS["text_muted"],
            command=self._open_lyrics, **btn_cfg
        ).pack(side="left", padx=2)

        self._speed_var = tk.StringVar(value="1.0×")
        speed_btn = ctk.CTkOptionMenu(
            frame,
            values=["0.75×", "1.0×", "1.25×", "1.5×"],
            variable=self._speed_var,
            width=72, height=30,
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["bg_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_secondary"],
            font=("Segoe UI", 11),
            command=self._on_speed_change,
        )
        speed_btn.pack(side="left", padx=4)

        self._dl_btn = ctk.CTkButton(
            frame, text="↓", font=("Segoe UI", 16),
            text_color=COLORS["text_muted"],
            command=self._download, **btn_cfg
        )
        self._dl_btn.pack(side="left", padx=2)

        vol_frame = ctk.CTkFrame(frame, fg_color="transparent")
        vol_frame.pack(side="left", padx=(8, 0))

        ctk.CTkLabel(vol_frame, text="🔊", font=("Segoe UI", 12),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=2)

        self._vol_slider = ctk.CTkSlider(
            vol_frame, from_=0, to=100, width=80, height=4,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["text_muted"],
            button_color=COLORS["text_secondary"],
            button_hover_color=COLORS["text_primary"],
            command=self._on_volume,
        )
        self._vol_slider.set(int(self.player.volume * 100))
        self._vol_slider.pack(side="left")

    def _bind_player(self):
        self.player.on_track_change(self._on_track_change)
        self.player.on_progress(self._on_progress)
        self.player.on_state_change(self._on_state_change)

    def _on_track_change(self, track: dict):
        self._current_track = track
        self.after(0, lambda: self._update_track_ui(track))

    def _update_track_ui(self, track: dict):
        title = track.get("title", "—")
        artist = track.get("artist", "—")
        self._title_var.set(title[:30] + "…" if len(title) > 30 else title)
        self._artist_var.set(artist[:25] + "…" if len(artist) > 25 else artist)
        self._dur_var.set(fmt_time(track.get("duration", 0)))
        self._progress.set(0)
        self._time_var.set("0:00")
        self._dl_btn.configure(text="↓", text_color=COLORS["text_muted"])

        is_fav = db.is_favorite(str(track.get("id", "")))
        self._fav_btn.configure(
            text="♥" if is_fav else "♡",
            text_color=COLORS["accent"] if is_fav else COLORS["text_muted"],
        )

        cover_url = track.get("cover_url")
        if cover_url:
            threading.Thread(target=self._load_cover, args=(cover_url,), daemon=True).start()
        else:
            self._show_default_cover()

    def _load_cover(self, url: str):
        try:
            resp = requests.get(url, timeout=8)
            img = Image.open(io.BytesIO(resp.content)).resize(
                (COVER_SIZE, COVER_SIZE), Image.LANCZOS
            )
            ctk_img = ctk.CTkImage(img, size=(COVER_SIZE, COVER_SIZE))
            self.after(0, lambda: self._cover_label.configure(image=ctk_img, text=""))
            self._cover_img = ctk_img
        except Exception:
            self.after(0, self._show_default_cover)

    def _show_default_cover(self):
        self._cover_label.configure(image=None, text="♫",
                                    font=("Segoe UI", 22), text_color=COLORS["text_muted"])

    def _on_progress(self, pos: float, dur: int):
        if self._dragging:
            return
        self.after(0, lambda: self._update_progress(pos, dur))

    def _update_progress(self, pos: float, dur: int):
        self._time_var.set(fmt_time(pos))
        if dur > 0:
            self._progress.set(pos / dur * 100)

    def _on_state_change(self, state: str, track):
        self.after(0, lambda: self._update_play_btn(state))

    def _update_play_btn(self, state: str):
        if state == "playing":
            self._play_btn.configure(text="⏸")
        elif state in ("paused", "stopped", "error"):
            self._play_btn.configure(text="▶")

    def _on_seek(self, val):
        if self.player.duration > 0:
            self._time_var.set(fmt_time(val / 100 * self.player.duration))

    def _on_seek_release(self, event):
        self._dragging = False
        val = self._progress.get()
        if self.player.duration > 0:
            self.player.seek(val / 100 * self.player.duration)

    def _on_volume(self, val):
        self.player.set_volume(val / 100)

    def _toggle_shuffle(self):
        on = self.player.toggle_shuffle()
        self._shuffle_btn.configure(
            text_color=COLORS["accent"] if on else COLORS["text_muted"]
        )

    def _cycle_repeat(self):
        mode = self.player.cycle_repeat()
        icons = {"none": ("↻", COLORS["text_muted"]),
                 "all": ("↻", COLORS["accent"]),
                 "one": ("↺", COLORS["accent"])}
        icon, color = icons.get(mode, ("↻", COLORS["text_muted"]))
        self._repeat_btn.configure(text=icon, text_color=color)

    def _on_speed_change(self, val: str):
        speed = float(val.replace("×", ""))
        self.player.set_speed(speed)
        db.set_setting("playback_speed", speed)

    def _toggle_favorite(self):
        if not self._current_track:
            return
        tid = str(self._current_track.get("id", ""))
        if db.is_favorite(tid):
            db.remove_from_favorites(tid)
            self._fav_btn.configure(text="♡", text_color=COLORS["text_muted"])
        else:
            db.add_to_favorites(self._current_track)
            self._fav_btn.configure(text="♥", text_color=COLORS["accent"])

    def _open_lyrics(self):
        if self._current_track:
            self.on_lyrics(self._current_track)

    def _download(self):
        if not self._current_track:
            return
        self._dl_btn.configure(text="…", text_color=COLORS["text_muted"])

        def _done(path):
            self.after(0, lambda: self._dl_btn.configure(text="✓", text_color=COLORS["success"]))

        def _err(e):
            self.after(0, lambda: self._dl_btn.configure(text="✗", text_color=COLORS["error"]))

        download_track(self._current_track, on_done=_done, on_error=_err)
