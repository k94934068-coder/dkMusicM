"""
Генератор стартового звука для Music Minimal.
Создаёт короткий мягкий тон (~1.5 сек) и сохраняет как assets/sounds/startup.mp3

Запуск: python generate_startup_sound.py
Требует: pip install numpy pygame
"""
import wave
import struct
import math
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "assets" / "sounds"
OUTPUT_WAV = OUTPUT_DIR / "startup.wav"
OUTPUT_MP3 = OUTPUT_DIR / "startup.mp3"


def generate_startup_wav():
    sample_rate = 44100
    duration = 1.5
    n_samples = int(sample_rate * duration)

    freqs = [440.0, 554.4, 659.3]

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 2.5)
        fade_in = min(1.0, t * 20)
        s = 0.0
        for f in freqs:
            s += math.sin(2 * math.pi * f * t)
        s /= len(freqs)
        val = int(s * envelope * fade_in * 16000)
        val = max(-32768, min(32767, val))
        samples.append(val)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT_WAV), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))

    print(f"WAV создан: {OUTPUT_WAV}")

    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(OUTPUT_WAV), str(OUTPUT_MP3)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"MP3 создан: {OUTPUT_MP3}")
            OUTPUT_WAV.unlink()
        else:
            print("ffmpeg не найден. Используем WAV. Переименуйте startup.wav в startup.mp3 вручную или установите ffmpeg.")
    except FileNotFoundError:
        print("ffmpeg не установлен. WAV-файл остаётся как startup.wav.")
        print("Переименуйте его в startup.mp3 или установите ffmpeg и повторите.")


if __name__ == "__main__":
    generate_startup_wav()
