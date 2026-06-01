import io
import time
import random
import threading
import requests
from pathlib import Path

try:
    import pygame
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
    pygame.mixer.init()
    PYGAME_OK = True
except Exception as e:
    print(f"[Player] pygame init error: {e}")
    PYGAME_OK = False

STARTUP_SOUND = Path(__file__).parent / "assets" / "sounds" / "startup.mp3"

REPEAT_NONE = "none"
REPEAT_ONE = "one"
REPEAT_ALL = "all"


class Player:
    def __init__(self):
        self._queue: list[dict] = []
        self._index: int = -1
        self._current: dict | None = None
        self._playing = False
        self._paused = False
        self._shuffle = False
        self._repeat = REPEAT_NONE
        self._speed = 1.0
        self._volume = 0.8
        self._position = 0.0
        self._duration = 0
        self._lock = threading.Lock()
        self._progress_thread: threading.Thread | None = None
        self._stop_progress = threading.Event()
        self._on_track_change: list = []
        self._on_progress: list = []
        self._on_state_change: list = []
        self._on_track_end: list = []
        self._shuffle_history: list[int] = []

        if PYGAME_OK:
            pygame.mixer.music.set_volume(self._volume)

    def on_track_change(self, cb):
        self._on_track_change.append(cb)

    def on_progress(self, cb):
        self._on_progress.append(cb)

    def on_state_change(self, cb):
        self._on_state_change.append(cb)

    def on_track_end(self, cb):
        self._on_track_end.append(cb)

    def _emit(self, callbacks, *args):
        for cb in callbacks:
            try:
                cb(*args)
            except Exception as e:
                print(f"[Player] callback error: {e}")

    def play_startup_sound(self):
        if not PYGAME_OK:
            return
        if STARTUP_SOUND.exists():
            try:
                pygame.mixer.Sound(str(STARTUP_SOUND)).play()
            except Exception as e:
                print(f"[Player] startup sound error: {e}")

    def set_queue(self, tracks: list[dict], start_index: int = 0):
        with self._lock:
            self._queue = list(tracks)
            self._index = start_index
            self._shuffle_history = []
        self._play_current()

    def play_track(self, track: dict, queue: list[dict] | None = None):
        if queue is not None:
            with self._lock:
                self._queue = list(queue)
                try:
                    self._index = self._queue.index(track)
                except ValueError:
                    self._queue.insert(0, track)
                    self._index = 0
                self._shuffle_history = []
        else:
            with self._lock:
                if track not in self._queue:
                    self._queue.insert(self._index + 1, track)
                self._index = self._queue.index(track)
        self._play_current()

    def _play_current(self):
        with self._lock:
            if not self._queue or self._index < 0 or self._index >= len(self._queue):
                return
            track = self._queue[self._index]
        self._load_and_play(track)

    def _load_and_play(self, track: dict):
        url = track.get("url")
        if not url:
            self._emit(self._on_state_change, "error", "Трек недоступен")
            return

        self._stop_progress_thread()
        self._current = track
        self._position = 0.0
        self._duration = track.get("duration", 0)
        self._emit(self._on_track_change, track)

        def _worker():
            try:
                if not PYGAME_OK:
                    self._emit(self._on_state_change, "error", "pygame недоступен")
                    return
                resp = requests.get(url, stream=True, timeout=15)
                resp.raise_for_status()
                audio_data = io.BytesIO(resp.content)
                pygame.mixer.music.load(audio_data)
                pygame.mixer.music.set_volume(self._volume)
                pygame.mixer.music.play()
                self._playing = True
                self._paused = False
                self._emit(self._on_state_change, "playing", track)
                self._start_progress_thread()
            except Exception as e:
                print(f"[Player] load error: {e}")
                self._emit(self._on_state_change, "error", str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _start_progress_thread(self):
        self._stop_progress.clear()
        self._progress_thread = threading.Thread(target=self._progress_loop, daemon=True)
        self._progress_thread.start()

    def _stop_progress_thread(self):
        self._stop_progress.set()
        if self._progress_thread and self._progress_thread.is_alive():
            self._progress_thread.join(timeout=1)
        self._progress_thread = None

    def _progress_loop(self):
        last_pos = -1
        while not self._stop_progress.is_set():
            time.sleep(0.5)
            if not PYGAME_OK:
                break
            if self._playing and not self._paused:
                try:
                    ms = pygame.mixer.music.get_pos()
                    if ms < 0:
                        self._on_end()
                        break
                    self._position = ms / 1000.0
                    if abs(self._position - last_pos) >= 0.4:
                        last_pos = self._position
                        self._emit(self._on_progress, self._position, self._duration)
                except Exception:
                    break

    def _on_end(self):
        self._playing = False
        self._emit(self._on_track_end, self._current)
        if self._repeat == REPEAT_ONE:
            self._play_current()
        elif self._repeat == REPEAT_ALL:
            self.next()
        else:
            self.next(auto=True)

    def play_pause(self):
        if not PYGAME_OK:
            return
        if self._playing and not self._paused:
            pygame.mixer.music.pause()
            self._paused = True
            self._playing = False
            self._emit(self._on_state_change, "paused", self._current)
        elif self._paused:
            pygame.mixer.music.unpause()
            self._paused = False
            self._playing = True
            self._emit(self._on_state_change, "playing", self._current)
        elif self._current:
            self._play_current()

    def next(self, auto: bool = False):
        with self._lock:
            if not self._queue:
                return
            if self._shuffle:
                idx = random.randint(0, len(self._queue) - 1)
                self._index = idx
            else:
                self._index = (self._index + 1) % len(self._queue)
                if self._index == 0 and auto and self._repeat == REPEAT_NONE:
                    self._playing = False
                    self._emit(self._on_state_change, "stopped", None)
                    return
        self._play_current()

    def prev(self):
        if self._position > 3:
            self.seek(0)
            return
        with self._lock:
            if not self._queue:
                return
            self._index = max(0, self._index - 1)
        self._play_current()

    def seek(self, seconds: float):
        if not PYGAME_OK:
            return
        try:
            pygame.mixer.music.rewind()
            pygame.mixer.music.set_pos(seconds)
            self._position = seconds
            self._emit(self._on_progress, self._position, self._duration)
        except Exception as e:
            print(f"[Player] seek error: {e}")

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        if PYGAME_OK:
            pygame.mixer.music.set_volume(self._volume)

    def set_speed(self, speed: float):
        self._speed = speed

    def toggle_shuffle(self):
        self._shuffle = not self._shuffle
        return self._shuffle

    def set_repeat(self, mode: str):
        if mode in (REPEAT_NONE, REPEAT_ONE, REPEAT_ALL):
            self._repeat = mode
        return self._repeat

    def cycle_repeat(self):
        modes = [REPEAT_NONE, REPEAT_ALL, REPEAT_ONE]
        idx = modes.index(self._repeat)
        self._repeat = modes[(idx + 1) % len(modes)]
        return self._repeat

    def add_to_queue(self, track: dict):
        with self._lock:
            self._queue.append(track)

    def remove_from_queue(self, index: int):
        with self._lock:
            if 0 <= index < len(self._queue):
                self._queue.pop(index)
                if index < self._index:
                    self._index -= 1

    def clear_queue(self):
        with self._lock:
            self._queue = []
            self._index = -1

    def get_queue(self) -> list[dict]:
        with self._lock:
            return list(self._queue)

    @property
    def current_track(self) -> dict | None:
        return self._current

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @property
    def repeat(self) -> str:
        return self._repeat

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def position(self) -> float:
        return self._position

    @property
    def duration(self) -> int:
        return self._duration


player = Player()
