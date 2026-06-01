import customtkinter as ctk
from ui.theme import COLORS, FONTS, SIDEBAR_WIDTH


NAV_ITEMS = [
    ("home", "⌂", "Главная"),
    ("search", "⌕", "Поиск"),
    ("library", "♫", "Библиотека"),
    ("mixes", "◈", "Миксы"),
    ("queue", "≡", "Очередь"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate, on_logout, **kwargs):
        super().__init__(
            parent,
            width=SIDEBAR_WIDTH,
            fg_color=COLORS["sidebar_bg"],
            corner_radius=0,
            **kwargs,
        )
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self._active = "home"
        self._buttons: dict[str, ctk.CTkButton] = {}
        self.pack_propagate(False)
        self._build()

    def _build(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=72)
        logo_frame.pack(fill="x", padx=20, pady=(20, 8))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame,
            text="Music",
            font=("Segoe UI", 19, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).pack(side="left", padx=(0, 0))

        ctk.CTkLabel(
            logo_frame,
            text=" Minimal",
            font=("Segoe UI", 19),
            text_color=COLORS["text_muted"],
            anchor="w",
        ).pack(side="left")

        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=16, pady=(0, 12))

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)

        for key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}   {label}",
                font=("Segoe UI", 13),
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_secondary"],
                anchor="w",
                command=lambda k=key: self._on_click(k),
            )
            btn.pack(fill="x", pady=2)
            self._buttons[key] = btn

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=8, pady=12)

        sep2 = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"])
        sep2.pack(side="bottom", fill="x", padx=16, pady=(0, 4))

        ctk.CTkButton(
            bottom_frame,
            text="  ⚙   Настройки",
            font=("Segoe UI", 12),
            height=38,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_muted"],
            anchor="w",
            command=lambda: self._on_click("settings"),
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            bottom_frame,
            text="  ↩   Выйти",
            font=("Segoe UI", 12),
            height=38,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#2A1010",
            text_color=COLORS["text_muted"],
            anchor="w",
            command=self.on_logout,
        ).pack(fill="x", pady=2)

        self._set_active("home")

    def _on_click(self, key: str):
        self._set_active(key)
        self.on_navigate(key)

    def _set_active(self, key: str):
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["bg_active"],
                    text_color=COLORS["text_primary"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                )
        self._active = key

    def set_active(self, key: str):
        self._set_active(key)
