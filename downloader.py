import os
import re
import threading
import requests
from pathlib import Path

DOWNLOADS_DIR = Path(__file__).parent / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:100]


def download_track(track: dict, on_progress=None, on_done=None, on_error=None):
    def _worker():
        url = track.get("url")
        if not url:
            if on_error:
                on_error("Нет ссылки на трек")
            return
        artist = _safe_filename(track.get("artist", "Unknown"))
        title = _safe_filename(track.get("title", "Unknown"))
        filename = f"{artist} - {title}.mp3"
        dest = DOWNLOADS_DIR / filename
        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if on_progress and total > 0:
                            on_progress(downloaded / total)
            if on_done:
                on_done(str(dest))
        except Exception as e:
            if dest.exists():
                dest.unlink()
            if on_error:
                on_error(str(e))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
