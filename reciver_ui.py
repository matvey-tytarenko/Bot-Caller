import customtkinter as ctk
from PIL import Image
import threading
import requests
import time
import json
import os
import glob
import config

try:
    from playsound import playsound as _playsound
    def play_sound(path):
        threading.Thread(target=_playsound, args=(path,), daemon=True).start()
except ImportError:
    import winsound
    def play_sound(path):
        threading.Thread(
            target=lambda: winsound.PlaySound(path, winsound.SND_FILENAME),
            daemon=True
        ).start()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SETTINGS_FILE = "reciver_settings.json"
SERVER_URL = config.api
APP_NAME = "BotReceiver"

# ── Автозапуск (реестр Windows) ────────────────────────────────────────────
def _autostart_path():
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
    except Exception:
        return False

DEFAULT_SETTINGS = {
    "sound": "notification.mp3",
    "volume": 80,
    "poll_interval": 10,
    "last_caller": "Sergey",
    "trigger_message": "подойди ко мне",
}

BUILTIN_SOUNDS = {
    "🔔  Стандартный": "notification.mp3",
    "🔕  Без звука":   "__none__",
}

def load_settings():
    s = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s.update(json.load(f))
        except Exception:
            pass
    return s

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def find_audio_files():
    exts = ["*.mp3", "*.wav", "*.ogg"]
    found = {}
    for ext in exts:
        for path in glob.glob(ext):
            name = os.path.basename(path)
            found[f"📁  {name}"] = path
    return found

def _make_tray_icon():
    try:
        return Image.open("wheelchair.png")
    except Exception:
        from PIL import ImageDraw
        img = Image.new("RGB", (64, 64), color=(13, 27, 42))
        ImageDraw.Draw(img).text((14, 18), "BR", fill=(92, 184, 255))
        return img

class ReciverApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self._running = True
        self._tray_icon = None
        self._last_seen = None
        self._popup_open = False

        self.title("Bot-Caller — Получатель")
        self.geometry("480x780")
        self.resizable(False, False)

        self._build_ui()
        self._start_listener()

        # ── Сразу уходим в трей при старте ─────────────────────────────────
        self.withdraw()
        self._start_tray()

    # ── Трей ────────────────────────────────────────────────────────────────
    def _start_tray(self):
        import pystray
        menu = pystray.Menu(
            pystray.MenuItem("Настройки", self._restore_from_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._quit_from_tray),
        )
        self._tray_icon = pystray.Icon("Bot-Receiver", _make_tray_icon(), "Bot-Receiver", menu)
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

        header = ctk.CTkFrame(self, fg_color=("#0A3A00", "#0d1b2a"), corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="🔔  Bot-Receiver",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#5cb8ff"
        ).pack(pady=18)

        self._section(self, "Звук уведомления")

        self.sound_map = {}
        self.sound_map.update(BUILTIN_SOUNDS)
        self.sound_map.update(find_audio_files())

        labels = list(self.sound_map.keys())
        current_label = labels[0]
        for lbl, path in self.sound_map.items():
            if path == self.settings["sound"]:
                current_label = lbl
                break

        self.sound_var = ctk.StringVar(value=current_label)
        self.sound_combo = ctk.CTkComboBox(
            self, values=labels, variable=self.sound_var,
            height=40, font=ctk.CTkFont(size=14),
            command=self._on_sound_change
        )
        self.sound_combo.pack(fill="x", **pad)

        preview_row = ctk.CTkFrame(self, fg_color="transparent")
        preview_row.pack(fill="x", padx=24, pady=(0, 4))

        ctk.CTkButton(
            preview_row, text="▶  Прослушать", height=36, width=140,
            fg_color=("#1e3a5f", "#1e3a5f"), hover_color=("#14274a", "#14274a"),
            command=self._preview_sound
        ).pack(side="left")

        self.sound_status = ctk.CTkLabel(
            preview_row, text="",
            font=ctk.CTkFont(size=12), text_color="#888"
        )
        self.sound_status.pack(side="left", padx=12)

        ctk.CTkButton(
            self, text="+ Добавить свой файл .mp3/.wav",
            height=36, font=ctk.CTkFont(size=13),
            fg_color="transparent", border_width=1,
            border_color=("#444", "#444"), hover_color=("#222", "#222"),
            command=self._browse_file
        ).pack(fill="x", padx=24, pady=(0, 4))

        self._section(self, "Интервал проверки сервера")

        interval_row = ctk.CTkFrame(self, fg_color="transparent")
        interval_row.pack(fill="x", padx=24, pady=8)

        self.interval_label = ctk.CTkLabel(
            interval_row,
            text=f"{self.settings['poll_interval']} сек",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=64
        )
        self.interval_label.pack(side="right")

        self.interval_slider = ctk.CTkSlider(
            interval_row, from_=3, to=60, number_of_steps=57,
            command=self._on_interval_change
        )
        self.interval_slider.set(self.settings["poll_interval"])
        self.interval_slider.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self._section(self, "Реагировать на вызов от")
        self.caller_entry = ctk.CTkEntry(self, height=40, font=ctk.CTkFont(size=14))
        self.caller_entry.pack(fill="x", **pad)
        self.caller_entry.insert(0, self.settings["last_caller"])

        self._section(self, "Текст вызова (триггер)")
        self.trigger_entry = ctk.CTkEntry(self, height=40, font=ctk.CTkFont(size=14))
        self.trigger_entry.pack(fill="x", **pad)
        self.trigger_entry.insert(0, self.settings["trigger_message"])

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
        btn_row.pack(fill="x", padx=24, pady=14)

        ctk.CTkButton(
            btn_row, text="🔽  В системный лоток", height=44,
            font=ctk.CTkFont(size=14),
            fg_color=("#2d2d2d", "#2d2d2d"), hover_color=("#444", "#444"),
            command=self._minimize_to_tray
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.listen_btn = ctk.CTkButton(
            btn_row, text="⏸  Слушать", height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1a6b3c", hover_color="#145530",
            command=self._toggle_listen
        )
        self.listen_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="💾  Сохранить", height=44,
            font=ctk.CTkFont(size=14),
            fg_color=("#2d2d2d", "#2d2d2d"), hover_color=("#444", "#444"),
            command=self._save
        ).pack(side="left", fill="x", expand=True)

        self.status_label = ctk.CTkLabel(
            self, text="🟢  Слушаю сервер...",
            font=ctk.CTkFont(size=12), text_color="#5cb85c"
        )
        self.status_label.pack(pady=(0, 12))

    def _section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#5cb8ff", "#5cb8ff")
        ).pack(anchor="w", padx=24, pady=(14, 0))

    # ── Звук ─────────────────────────────────────────────────────────────────
    def _on_sound_change(self, label):
        self.settings["sound"] = self.sound_map.get(label, "notification.mp3")

    def _preview_sound(self):
        label = self.sound_var.get()
        path = self.sound_map.get(label, "")
        if path == "__none__" or not path:
            self.sound_status.configure(text="Звук отключён", text_color="#f0a040")
            return
        if not os.path.exists(path):
            self.sound_status.configure(text="Файл не найден", text_color="#cc3a3a")
            return
        self.sound_status.configure(text="▶ воспроизведение...", text_color="#5cb85c")
        play_sound(path)
        self.after(2000, lambda: self.sound_status.configure(text=""))

    def _browse_file(self):
        try:
            import tkinter.filedialog as fd
            path = fd.askopenfilename(
                filetypes=[("Аудио файлы", "*.mp3 *.wav *.ogg"), ("Все файлы", "*.*")]
            )
            if path:
                name = os.path.basename(path)
                label = f"📁  {name}"
                self.sound_map[label] = path
                self.sound_combo.configure(values=list(self.sound_map.keys()))
                self.sound_combo.set(label)
                self.settings["sound"] = path
        except Exception as e:
            self._set_status(f"Ошибка: {e}", error=True)

    # ── Интервал ──────────────────────────────────────────────────────────────
    def _on_interval_change(self, value):
        v = int(value)
        self.settings["poll_interval"] = v
        self.interval_label.configure(text=f"{v} сек")

    # ── Слушатель сервера ─────────────────────────────────────────────────────
    def _start_listener(self):
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _fetch_current_state(self):
        """Читаем сервер один раз при старте — чтобы не реагировать на старое сообщение."""
        try:
            resp = requests.get(SERVER_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            caller  = data.get("Last Caller", "")
            message = data.get("Message", "").strip().lower()
            self._last_seen = (caller, message)
        except Exception:
            pass  # если сервер недоступен — ничего страшного, начнём с None

    def _listen_loop(self):
        # При первом запуске запоминаем что уже есть на сервере
        self._fetch_current_state()

        while self._running:
            try:
                resp = requests.get(SERVER_URL, timeout=8)
                resp.raise_for_status()
                data = resp.json()
                caller  = data.get("Last Caller", "")
                message = data.get("Message", "").strip().lower()
                trigger = self.trigger_entry.get().strip().lower()
                expected_caller = self.caller_entry.get().strip()
                key = (caller, message)
                if caller == expected_caller and message == trigger and key != self._last_seen:
                    self._last_seen = key
                    self.after(0, self._on_notification)
            except Exception as e:
                self.after(0, lambda err=e: self._set_status(f"Ошибка связи: {err}", error=True))
            for _ in range(self.settings["poll_interval"] * 10):
                if not self._running:
                    return
                time.sleep(0.1)

    def _on_notification(self):
        if self._popup_open:
            return
        sound = self.settings.get("sound", "notification.mp3")
        if sound and sound != "__none__" and os.path.exists(sound):
            play_sound(sound)
        self._set_status("🔔  Получен вызов!", ok=True)
        # Если окно скрыто — сначала показываем, потом попап
        if not self.winfo_viewable():
            self._restore_from_tray()
        self._show_popup()

    def _show_popup(self):
        self._popup_open = True
        popup = ctk.CTkToplevel(self)
        popup.title("Вызов!")
        popup.geometry("300x160")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        popup.grab_set()

        caller = self.caller_entry.get().strip()
        ctk.CTkLabel(
            popup, text="📢  Вас вызывают!",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(24, 8))
        ctk.CTkLabel(
            popup, text=f"Звонит: {caller}",
            font=ctk.CTkFont(size=14), text_color="#888"
        ).pack()

        def on_ok():
            self._popup_open = False
            # _last_seen НЕ сбрасываем — чтобы не среагировать повторно
            # на то же сообщение. Сбросится только когда придёт новый вызов.
            popup.destroy()

        ctk.CTkButton(
            popup, text="Иду!", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1a6b3c", hover_color="#145530",
            command=on_ok
        ).pack(pady=18, padx=40, fill="x")
        popup.protocol("WM_DELETE_WINDOW", on_ok)

    def _toggle_autostart(self):
        ok = set_autostart(self.autostart_var.get())
        if ok:
            label = "включён" if self.autostart_var.get() else "отключён"
            self.autostart_status.configure(text=f"✓ {label}", text_color="#5cb85c")
        else:
            self.autostart_status.configure(text="Ошибка доступа к реестру", text_color="#cc3a3a")
            self.autostart_var.set(not self.autostart_var.get())
        self.after(2500, lambda: self.autostart_status.configure(text=""))

    # ── Пауза ─────────────────────────────────────────────────────────────────
    def _toggle_listen(self):
        self._running = not self._running
        if self._running:
            self.listen_btn.configure(text="⏸  Слушать", fg_color="#1a6b3c", hover_color="#145530")
            self._set_status("🟢  Слушаю сервер...", ok=True)
            self._start_listener()
        else:
            self.listen_btn.configure(text="▶  Возобновить", fg_color="#5c4a1a", hover_color="#3d3112")
            self._set_status("⏸  Прослушивание приостановлено", error=False)

    # ── Сохранение ────────────────────────────────────────────────────────────
    def _save(self):
        self.settings["last_caller"]     = self.caller_entry.get().strip()
        self.settings["trigger_message"] = self.trigger_entry.get().strip()
        save_settings(self.settings)
        self._set_status("✓  Настройки сохранены", ok=True)

    def _set_status(self, text, ok=False, error=False):
        color = "#5cb85c" if ok else ("#cc3a3a" if error else "#888")
        self.status_label.configure(text=text, text_color=color)

    def on_close(self):
        self._running = False
        self.destroy()


if __name__ == "__main__":
    app = ReciverApp()
    app.protocol("WM_DELETE_WINDOW", app._minimize_to_tray)  # крестик → трей, не закрыть
    app.mainloop()