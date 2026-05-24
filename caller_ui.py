import customtkinter as ctk
import keyboard
import requests
import json
import os
import threading
import config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SETTINGS_FILE = "caller_settings.json"
SERVER_URL = config.api
APP_NAME = "BotCaller"

# ── Автозапуск (реестр Windows) ────────────────────────────────────────────
def _autostart_path():
    """Путь к текущему exe или py-скрипту."""
    import sys
    return sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)

def is_autostart_enabled():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def set_autostart(enable: bool):
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{_autostart_path()}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        return False

DEFAULT_SETTINGS = {
    "hotkey": "ctrl+space",
    "user": "Sergey",
    "message": "подойди ко мне",
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                DEFAULT_SETTINGS.update(s)
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def _make_tray_icon():
    """Загружает иконку или рисует запасную."""
    try:
        from PIL import Image
        return Image.open("wheelchair.png")
    except Exception:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (64, 64), color=(26, 26, 46))
        ImageDraw.Draw(img).text((14, 18), "BC", fill=(124, 156, 255))
        return img

class CallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.recording = False
        self.pressed_keys = set()
        self._tray_icon = None

        self.title("Bot-Caller — Настройки")
        self.geometry("480x560")
        self.resizable(False, False)

        self._build_ui()
        self._register_hotkey()

        # ── Сразу уходим в трей при старте ─────────────────────────────────
        self.withdraw()
        self._start_tray()

    # ── Трей ────────────────────────────────────────────────────────────────
    def _start_tray(self):
        import pystray
        menu = pystray.Menu(
            pystray.MenuItem("Настройки", self._restore_from_tray, default=True),
            pystray.MenuItem("📢  Позвать", self._hotkey_triggered),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._quit_from_tray),
        )
        self._tray_icon = pystray.Icon("Bot-Caller", _make_tray_icon(), "Bot-Caller", menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _restore_from_tray(self, icon=None, item=None):
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.after(0, self.deiconify)

    def _minimize_to_tray(self):
        self.withdraw()
        self._start_tray()

    def _quit_from_tray(self, icon=None, item=None):
        if self._tray_icon:
            self._tray_icon.stop()
            self._tray_icon = None
        self.after(0, self.on_close)

    # ── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = {"padx": 24, "pady": 8}

        header = ctk.CTkFrame(self, fg_color=("#1a1a2e", "#1a1a2e"), corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="⚡  Bot-Caller",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#7c9cff"
        ).pack(pady=18)

        self._section(self, "Горячая клавиша")

        hk_row = ctk.CTkFrame(self, fg_color="transparent")
        hk_row.pack(fill="x", **pad)

        self.hotkey_display = ctk.CTkEntry(
            hk_row,
            placeholder_text="Нажмите «Записать»...",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, state="readonly"
        )
        self.hotkey_display.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.hotkey_display.configure(state="normal")
        self.hotkey_display.insert(0, self.settings["hotkey"])
        self.hotkey_display.configure(state="readonly")

        self.record_btn = ctk.CTkButton(
            hk_row, text="Записать", width=100, height=40,
            command=self._toggle_record
        )
        self.record_btn.pack(side="left")

        self.hk_status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12),
            text_color=("#888", "#888")
        )
        self.hk_status.pack(**pad)

        self._section(self, "Имя пользователя")
        self.user_entry = ctk.CTkEntry(self, height=40, font=ctk.CTkFont(size=14))
        self.user_entry.pack(fill="x", **pad)
        self.user_entry.insert(0, self.settings["user"])

        self._section(self, "Текст вызова")
        self.msg_entry = ctk.CTkEntry(self, height=40, font=ctk.CTkFont(size=14))
        self.msg_entry.pack(fill="x", **pad)
        self.msg_entry.insert(0, self.settings["message"])

        ctk.CTkFrame(self, height=1, fg_color=("#333", "#333")).pack(
            fill="x", padx=24, pady=(16, 0)
        )

        # ── Автозапуск ──────────────────────────────────────────────────────
        self._section(self, "Система")
        autostart_row = ctk.CTkFrame(self, fg_color="transparent")
        autostart_row.pack(fill="x", padx=24, pady=(4, 0))

        self.autostart_var = ctk.BooleanVar(value=is_autostart_enabled())
        ctk.CTkCheckBox(
            autostart_row,
            text="Запускать при старте Windows",
            variable=self.autostart_var,
            font=ctk.CTkFont(size=13),
            command=self._toggle_autostart
        ).pack(side="left")

        self.autostart_status = ctk.CTkLabel(
            autostart_row, text="", font=ctk.CTkFont(size=11), text_color="#888"
        )
        self.autostart_status.pack(side="left", padx=10)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=16)

        self.call_btn = ctk.CTkButton(
            btn_row, text="📢  Позвать сейчас", height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3a5ccc", hover_color="#2e4aaa",
            command=self._send_call
        )
        self.call_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="💾  Сохранить", height=44,
            font=ctk.CTkFont(size=14),
            fg_color=("#2d2d2d", "#2d2d2d"), hover_color=("#444", "#444"),
            command=self._save
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            self, text="🔽  В системный лоток", height=40,
            font=ctk.CTkFont(size=14),
            fg_color=("#2d2d2d", "#2d2d2d"), hover_color=("#444", "#444"),
            command=self._minimize_to_tray
        ).pack(fill="x", padx=24, pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            self, text="Готов к работе",
            font=ctk.CTkFont(size=12),
            text_color=("#666", "#888")
        )
        self.status_label.pack(pady=(0, 12))

    def _section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#7c9cff", "#7c9cff")
        ).pack(anchor="w", padx=24, pady=(12, 0))

    # ── Горячая клавиша ──────────────────────────────────────────────────────
    def _toggle_record(self):
        if not self.recording:
            self.recording = True
            self.pressed_keys = set()
            self.record_btn.configure(text="⏹ Стоп", fg_color="#cc3a3a", hover_color="#aa2e2e")
            self.hk_status.configure(text="Нажмите нужную комбинацию клавиш...", text_color="#f0a040")
            self.hotkey_display.configure(state="normal")
            self.hotkey_display.delete(0, "end")
            self.hotkey_display.configure(state="readonly")
            keyboard.hook(self._on_key_event)
        else:
            self._stop_record()

    def _on_key_event(self, event):
        if not self.recording:
            return
        if event.event_type == keyboard.KEY_DOWN:
            self.pressed_keys.add(event.name.lower())
            combo = "+".join(sorted(self.pressed_keys))
            self.hotkey_display.configure(state="normal")
            self.hotkey_display.delete(0, "end")
            self.hotkey_display.insert(0, combo)
            self.hotkey_display.configure(state="readonly")

    def _stop_record(self):
        self.recording = False
        keyboard.unhook_all()
        self.record_btn.configure(text="Записать", fg_color=("#1f538d", "#1f538d"), hover_color=("#14375e", "#14375e"))
        combo = self.hotkey_display.get()
        if combo:
            self.settings["hotkey"] = combo
            self.hk_status.configure(text=f"Установлено: {combo}", text_color="#5cb85c")
            self._register_hotkey()
        else:
            self.hk_status.configure(text="Не записано", text_color="#cc3a3a")

    def _register_hotkey(self):
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(self.settings["hotkey"], self._hotkey_triggered)
        except Exception as e:
            self._set_status(f"Ошибка хоткея: {e}", error=True)

    def _hotkey_triggered(self, icon=None, item=None):
        self.after(0, self._send_call)

    # ── Отправка ─────────────────────────────────────────────────────────────
    def _send_call(self):
        user = self.user_entry.get().strip() or self.settings["user"]
        msg  = self.msg_entry.get().strip()  or self.settings["message"]
        self.call_btn.configure(state="disabled", text="⏳  Отправка...")
        threading.Thread(target=self._do_send, args=(user, msg), daemon=True).start()

    def _do_send(self, user, msg):
        try:
            r = requests.post(SERVER_URL + "/api/call", json={"user": user, "message": msg}, timeout=8)
            r.raise_for_status()
            self.after(0, lambda: self._set_status("✓  Вызов отправлен!", ok=True))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Ошибка: {e}", error=True))
        finally:
            self.after(0, lambda: self.call_btn.configure(state="normal", text="📢  Позвать сейчас"))

    def _toggle_autostart(self):
        ok = set_autostart(self.autostart_var.get())
        if ok:
            label = "включён" if self.autostart_var.get() else "отключён"
            self.autostart_status.configure(text=f"✓ {label}", text_color="#5cb85c")
        else:
            self.autostart_status.configure(text="Ошибка доступа к реестру", text_color="#cc3a3a")
            self.autostart_var.set(not self.autostart_var.get())  # откатываем чекбокс
        self.after(2500, lambda: self.autostart_status.configure(text=""))

    def _save(self):
        self.settings["user"]    = self.user_entry.get().strip()
        self.settings["message"] = self.msg_entry.get().strip()
        save_settings(self.settings)
        self._set_status("✓  Настройки сохранены", ok=True)
        self._register_hotkey()

    def _set_status(self, text, ok=False, error=False):
        color = "#5cb85c" if ok else ("#cc3a3a" if error else ("#888", "#888"))
        self.status_label.configure(text=text, text_color=color)

    def on_close(self):
        keyboard.unhook_all()
        self.destroy()


if __name__ == "__main__":
    app = CallerApp()
    app.protocol("WM_DELETE_WINDOW", app._minimize_to_tray)  # крестик → трей, не закрыть
    app.mainloop()