import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "music_minimal.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT NOT NULL,
            title TEXT,
            artist TEXT,
            duration INTEGER,
            cover_url TEXT,
            url TEXT,
            played_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id TEXT NOT NULL UNIQUE,
            title TEXT,
            artist TEXT,
            duration INTEGER,
            cover_url TEXT,
            url TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS local_playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            track_id TEXT NOT NULL,
            title TEXT,
            artist TEXT,
            duration INTEGER,
            cover_url TEXT,
            url TEXT,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (playlist_id) REFERENCES local_playlists(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


def track_to_dict(track):
    if isinstance(track, dict):
        return track
    return {
        "id": getattr(track, "id", ""),
        "title": getattr(track, "title", "Unknown"),
        "artist": getattr(track, "artist", "Unknown"),
        "duration": getattr(track, "duration", 0),
        "cover_url": getattr(track, "thumb", None) or getattr(track, "cover_url", None),
        "url": getattr(track, "url", None),
    }


def add_to_history(track: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO history (track_id, title, artist, duration, cover_url, url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        str(track.get("id", "")),
        track.get("title", ""),
        track.get("artist", ""),
        track.get("duration", 0),
        track.get("cover_url", ""),
        track.get("url", ""),
    ))
    c.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY played_at DESC LIMIT 50)")
    conn.commit()
    conn.close()


def get_history():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY played_at DESC LIMIT 50")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_to_favorites(track: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO favorites (track_id, title, artist, duration, cover_url, url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        str(track.get("id", "")),
        track.get("title", ""),
        track.get("artist", ""),
        track.get("duration", 0),
        track.get("cover_url", ""),
        track.get("url", ""),
    ))
    conn.commit()
    conn.close()


def remove_from_favorites(track_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE track_id = ?", (str(track_id),))
    conn.commit()
    conn.close()


def is_favorite(track_id: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM favorites WHERE track_id = ?", (str(track_id),))
    result = c.fetchone() is not None
    conn.close()
    return result


def get_favorites():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM favorites ORDER BY added_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_setting(key: str, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]
    return default


def set_setting(key: str, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
    conn.commit()
    conn.close()


def create_playlist(name: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO local_playlists (name) VALUES (?)", (name,))
    conn.commit()
    playlist_id = c.lastrowid
    conn.close()
    return playlist_id


def get_playlists():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM local_playlists ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def add_track_to_playlist(playlist_id: int, track: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(position) FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
    row = c.fetchone()
    pos = (row[0] or 0) + 1
    c.execute("""
        INSERT INTO playlist_tracks (playlist_id, track_id, title, artist, duration, cover_url, url, position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        playlist_id,
        str(track.get("id", "")),
        track.get("title", ""),
        track.get("artist", ""),
        track.get("duration", 0),
        track.get("cover_url", ""),
        track.get("url", ""),
        pos,
    ))
    conn.commit()
    conn.close()


def get_playlist_tracks(playlist_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM playlist_tracks WHERE playlist_id = ? ORDER BY position", (playlist_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
