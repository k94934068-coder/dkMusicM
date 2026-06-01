import threading
import tkinter as tk
import customtkinter as ctk
from ui.theme import COLORS


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_login, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kwargs)
        self.on_login = on_login
        self._logging_in = False
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent", width=380)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center, text="Music",
            font=("Segoe UI", 42, "bold"), text_color=COLORS["text_primary"],
        ).pack()
        ctk.CTkLabel(
            center, text="Minimal",
            font=("Segoe UI", 28), text_color=COLORS["text_muted"],
        ).pack(pady=(0, 40))

        ctk.CTkLabel(
            center, text="Войдите через VK Музыку",
            font=("Segoe UI", 15), text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 24))

        field_cfg = dict(
            width=320, height=48,
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=10,
            font=("Segoe UI", 13),
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
        )

        self._login_var = tk.StringVar()
        login_entry = ctk.CTkEntry(
            center,
            textvariable=self._login_var,
            placeholder_text="Телефон или Email",
            **field_cfg,
        )
        login_entry.pack(pady=4)

        self._pass_var = tk.StringVar()
        pass_entry = ctk.CTkEntry(
            center,
            textvariable=self._pass_var,
            placeholder_text="Пароль",
            show="•",
            **field_cfg,
        )
        pass_entry.pack(pady=4)
        pass_entry.bind("<Return>", lambda e: self._do_login())

        self._error_label = ctk.CTkLabel(
            center, text="",
            font=("Segoe UI", 12), text_color=COLORS["error"],
            wraplength=320,
        )
        self._error_label.pack(pady=(8, 0))

        self._login_btn = ctk.CTkButton(
            center,
            text="Войти через VK",
            width=320, height=48,
            corner_radius=10,
            fg_color="#0077FF",
            hover_color="#0066EE",
            text_color="#FFFFFF",
            font=("Segoe UI", 14, "bold"),
            command=self._do_login,
        )
        self._login_btn.pack(pady=(16, 8))

        ctk.CTkLabel(
            center,
            text="Данные сохраняются в зашифрованном виде\nна вашем устройстве",
            font=("Segoe UI", 10), text_color=COLORS["text_muted"],
            justify="center",
        ).pack(pady=(8, 0))

    def _do_login(self):
        if self._logging_in:
            return
        login = self._login_var.get().strip()
        password = self._pass_var.get().strip()
        if not login or not password:
            self._error_label.configure(text="Введите логин и пароль")
            return
        self._logging_in = True
        self._login_btn.configure(text="Входим…", state="disabled")
        self._error_label.configure(text="")

        def _worker():
            self.on_login(login, password, self._on_result)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_result(self, success: bool, error: str):
        self._logging_in = False
        self.after(0, lambda: self._restore_btn(success, error))

    def _restore_btn(self, success: bool, error: str):
        self._login_btn.configure(text="Войти через VK", state="normal")
        if not success:
            self._error_label.configure(
                text=f"Ошибка входа: {error[:80]}" if error else "Неверный логин или пароль"
            )
