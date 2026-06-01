import os
import json
import base64
import threading
from pathlib import Path
from cryptography.fernet import Fernet

CONFIG_PATH = Path(__file__).parent / "config.json"
KEY_PATH = Path(__file__).parent / "data" / ".key"


def _get_or_create_key() -> bytes:
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes()
    key = Fernet.generate_key()
    KEY_PATH.write_bytes(key)
    return key


def _encrypt(text: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.encrypt(text.encode()).decode()


def _decrypt(token: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.decrypt(token.encode()).decode()


def save_credentials(login: str, password: str):
    data = {
        "login": _encrypt(login),
        "password": _encrypt(password),
    }
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_credentials():
    if not CONFIG_PATH.exists():
        return None, None
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        login = _decrypt(data["login"])
        password = _decrypt(data["password"])
        return login, password
    except Exception:
        return None, None


def clear_credentials():
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()


class VKClient:
    def __init__(self):
        self.vk = None
        self.logged_in = False
        self._lock = threading.Lock()

    def login(self, login: str, password: str) -> tuple[bool, str]:
        try:
            import vk_audio
            vk = vk_audio.VkAudio(login=login, password=password)
            with self._lock:
                self.vk = vk
                self.logged_in = True
            return True, ""
        except Exception as e:
            err = str(e)
            return False, err

    def logout(self):
        with self._lock:
            self.vk = None
            self.logged_in = False
        clear_credentials()

    def _ensure_logged_in(self):
        if not self.logged_in or self.vk is None:
            raise RuntimeError("Not logged in")

    def _audio_to_dict(self, audio) -> dict:
        thumb = None
        try:
            if hasattr(audio, "thumb") and audio.thumb:
                thumb = audio.thumb
        except Exception:
            pass
        return {
            "id": str(getattr(audio, "id", "") or ""),
            "title": getattr(audio, "title", "Unknown") or "Unknown",
            "artist": getattr(audio, "artist", "Unknown") or "Unknown",
            "duration": int(getattr(audio, "duration", 0) or 0),
            "cover_url": thumb,
            "url": getattr(audio, "url", None),
        }

    def get_my_music(self, count: int = 100) -> list[dict]:
        self._ensure_logged_in()
        try:
            tracks = []
            for audio in self.vk.load(owner_id=None):
                tracks.append(self._audio_to_dict(audio))
                if len(tracks) >= count:
                    break
            return tracks
        except Exception as e:
            print(f"[VKClient] get_my_music error: {e}")
            return []

    def search(self, query: str, count: int = 50) -> list[dict]:
        self._ensure_logged_in()
        try:
            tracks = []
            for audio in self.vk.search(query):
                tracks.append(self._audio_to_dict(audio))
                if len(tracks) >= count:
                    break
            return tracks
        except Exception as e:
            print(f"[VKClient] search error: {e}")
            return []

    def get_artist_tracks(self, artist_id: str, count: int = 50) -> list[dict]:
        self._ensure_logged_in()
        try:
            tracks = []
            for audio in self.vk.load_artist(artist_id):
                tracks.append(self._audio_to_dict(audio))
                if len(tracks) >= count:
                    break
            return tracks
        except Exception as e:
            print(f"[VKClient] get_artist_tracks error: {e}")
            return []

    def get_recommendations(self, count: int = 50) -> list[dict]:
        self._ensure_logged_in()
        try:
            tracks = []
            for audio in self.vk.search("популярное 2024"):
                tracks.append(self._audio_to_dict(audio))
                if len(tracks) >= count:
                    break
            return tracks
        except Exception as e:
            print(f"[VKClient] get_recommendations error: {e}")
            return []

    def get_trending(self, count: int = 30) -> list[dict]:
        self._ensure_logged_in()
        try:
            tracks = []
            for audio in self.vk.search("хиты 2024"):
                tracks.append(self._audio_to_dict(audio))
                if len(tracks) >= count:
                    break
            return tracks
        except Exception as e:
            print(f"[VKClient] get_trending error: {e}")
            return []


vk_client = VKClient()
