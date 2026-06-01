# Music Minimal

Минималистичный музыкальный плеер для Windows на основе VK Музыки.

## Стек

- Python 3.11+
- customtkinter — современный тёмный GUI
- pygame — воспроизведение аудио
- vk_audio — доступ к VK Музыке
- SQLite — локальные данные (история, избранное, плейлисты)
- cryptography — шифрование логина/пароля
- Pillow — обложки треков
- PyInstaller — сборка в .exe

## Установка зависимостей

```bash
pip install -r requirements.txt
```

> `vk_audio` устанавливается напрямую с GitHub — нужен git.

## Запуск из исходников

```bash
python desktop_main.py
```

## Сборка Windows .exe

Стандартный вариант (рекомендуется):

```bash
pyinstaller music_minimal.spec
```

Или вручную:

```bash
pyinstaller --onefile --noconsole \
  --add-data "assets;assets" \
  --add-data "ui;ui" \
  --hidden-import customtkinter \
  --hidden-import PIL._tkinter_finder \
  --hidden-import pygame \
  --hidden-import vk_audio \
  --hidden-import cryptography \
  --hidden-import colorthief \
  --name "MusicMinimal" \
  desktop_main.py
```

Готовый файл появится в папке `dist/MusicMinimal.exe`.

> **Пользователю ничего устанавливать не нужно** — все зависимости внутри .exe.

## Структура проекта

```
music-minimal/
  desktop_main.py       # Точка входа, главное окно
  player.py             # Аудиоплеер (pygame)
  vk_client.py          # VK Audio API
  database.py           # SQLite: история, избранное, плейлисты
  downloader.py         # Скачивание треков
  ui/
    theme.py            # Цвета, шрифты, константы
    sidebar.py          # Левая навигационная панель
    now_playing.py      # Нижняя панель Now Playing
    login_screen.py     # Экран входа через VK
    home_screen.py      # Главная — моя музыка и тренды
    search_screen.py    # Поиск треков
    library_screen.py   # Библиотека: моя музыка, избранное, история
    mixes_screen.py     # Миксы и подборки
    queue_screen.py     # Очередь воспроизведения
    lyrics_screen.py    # Текст песни / караоке
    settings_screen.py  # Настройки
    track_list.py       # Переиспользуемый список треков
  assets/
    sounds/
      startup.mp3       # Звук запуска (замените своим)
    covers/             # Кэш обложек
  downloads/            # Скачанные треки
  data/
    music_minimal.db    # База данных SQLite (создаётся автоматически)
    .key                # Ключ шифрования (создаётся автоматически)
  config.json           # Зашифрованные учётные данные
  requirements.txt
  music_minimal.spec    # Конфиг PyInstaller
  README.md
```

## Функции

- **Вход через VK** — логин/пароль с шифрованием и авто-входом
- **Моя музыка** — треки из аккаунта VK
- **Поиск** — треки, исполнители с задержкой ввода
- **Миксы** — 8 тематических подборок (хиты, рок, рэп, lofi…)
- **Очередь** — текущая очередь с удалением треков
- **Избранное** — лайки с сохранением в SQLite
- **История** — последние 50 треков
- **Скачивание** — MP3 в папку downloads/
- **Текст песни** — экран с подсветкой строк по времени
- **Скорость** — 0.75×, 1.0×, 1.25×, 1.5×
- **Перемотка** — слайдер прогресса
- **Громкость** — регулятор
- **Повтор** — нет / всё / один трек
- **Перемешать** — случайный порядок

## Авторизация

Поддерживается авторизация через логин и пароль VK.
При первом входе данные шифруются и сохраняются в `config.json`.
При следующем запуске — автоматический вход.

## Добавление звука запуска

Положите `startup.mp3` в `assets/sounds/` длиной 1–2 секунды.
Если файл отсутствует — приложение запустится без звука.
