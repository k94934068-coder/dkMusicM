"""
Music Minimal — минималистичный музыкальный плеер для Windows.
Точка входа для десктопного приложения.
"""
import sys
import threading
import tkinter as tk
import customtkinter as ctk

import database as db
from player import player
from vk_client import vk_client, save_credentials, load_credentials
from ui.theme import COLORS, SIDEBAR_WIDTH, PLAYER_HEIGHT
from ui.sidebar import Sidebar
from ui.now_playing import NowPlayingBar
from ui.login_screen import LoginScreen
from ui.home_screen import HomeScreen
from ui.search_screen import SearchScreen
from ui.library_screen import LibraryScreen
from ui.mixes_screen import MixesScreen
from ui.queue_screen import QueueScreen
from ui.settings_screen import SettingsScreen
from ui.lyrics_screen import LyricsWindow


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Music Minimal")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg"])
        self._icon()

        db.init_db()

        self._screens: dict[str, ctk.CTkFrame | None] = {}
        self._active_screen = "home"
        self._lyrics_win = None

        self._show_login_if_needed()

    def _icon(self):
        try:
            from pathlib import Path
            ico = Path(__file__).parent / "assets" / "icon.ico"
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    def _show_login_if_needed(self):
        login, password = load_credentials()
        if login and password:
            self._attempt_autologin(login, password)
        else:
            self._show_login()

    def _attempt_autologin(self, login: str, password: str):
        loading = ctk.CTkLabel(
            self, text="Авторизация…",
            font=("Segoe UI", 16), text_color=COLORS["text_muted"],
        )
        loading.place(relx=0.5, rely=0.5, anchor="center")

        def _worker():
            ok, err = vk_client.login(login, password)
            self.after(0, lambda: self._on_autologin(ok, err, loading, login, password))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_autologin(self, ok: bool, err: str, loading_lbl, login: str, password: str):
        loading_lbl.destroy()
        if ok:
            self._build_main()
        else:
            self._show_login()

    def _show_login(self):
        for w in self.winfo_children():
            w.destroy()
        login_screen = LoginScreen(self, on_login=self._handle_login)
        login_screen.pack(fill="both", expand=True)

    def _handle_login(self, login: str, password: str, callback):
        ok, err = vk_client.login(login, password)
        if ok:
            save_credentials(login, password)
            callback(True, "")
            self.after(100, self._build_main)
        else:
            callback(False, err)

    def _build_main(self):
        for w in self.winfo_children():
            w.destroy()
        self._screens.clear()

        self._sidebar = Sidebar(
            self,
            on_navigate=self._navigate,
            on_logout=self._logout,
        )
        self._sidebar.pack(side="left", fill="y")

        right = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        right.pack(side="left", fill="both", expand=True)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self._content_area = ctk.CTkFrame(right, fg_color="transparent", corner_radius=0)
        self._content_area.pack(fill="both", expand=True)

        self._now_playing = NowPlayingBar(
            right, player=player, on_lyrics=self._open_lyrics,
        )
        self._now_playing.pack(fill="x", side="bottom")

        self._navigate("home")
        self._play_startup_sound()

    def _play_startup_sound(self):
        threading.Thread(target=player.play_startup_sound, daemon=True).start()

    def _navigate(self, key: str):
        for w in self._content_area.winfo_children():
            w.pack_forget()

        self._active_screen = key

        if key not in self._screens or self._screens[key] is None:
            self._screens[key] = self._create_screen(key)

        screen = self._screens[key]
        if screen:
            screen.pack(fill="both", expand=True)
            if hasattr(screen, "refresh"):
                if key in ("library", "queue"):
                    screen.refresh()

        self._sidebar.set_active(key)

    def _create_screen(self, key: str) -> ctk.CTkFrame | None:
        common = dict(master=self._content_area)
        if key == "home":
            return HomeScreen(vk_client=vk_client, player=player, **common)
        elif key == "search":
            return SearchScreen(vk_client=vk_client, player=player, **common)
        elif key == "library":
            return LibraryScreen(vk_client=vk_client, player=player, **common)
        elif key == "mixes":
            return MixesScreen(vk_client=vk_client, player=player, **common)
        elif key == "queue":
            return QueueScreen(player=player, **common)
        elif key == "settings":
            return SettingsScreen(player=player, **common)
        return None

    def _open_lyrics(self, track: dict):
        if self._lyrics_win and self._lyrics_win.winfo_exists():
            self._lyrics_win.destroy()
        self._lyrics_win = LyricsWindow(self, track=track, player=player)

    def _logout(self):
        vk_client.logout()
        player.clear_queue()
        self._screens.clear()
        self._show_login()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
