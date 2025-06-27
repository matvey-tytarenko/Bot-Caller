import pystray
from PIL import Image
import threading
import requests
import time
import widget  # модуль, который показывает окно
from playsound import playsound as ps

# Загружаем иконку
img = Image.open("wheelchair.png")

# URL сервера
SERVER_URL = "https://bot-caller-nine.vercel.app/"

# Фоновая проверка сервера
def get_server_data():
    try:
        response = requests.get(SERVER_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main_loop():
    print("🔁 Background loop started")
    while True:
        data = get_server_data()
        if data:
            last_caller = data.get("Last Caller")
            message = data.get("Message", "").strip().lower()
            if last_caller == "Sergey" and message == "подойди ко мне":
                print("🔔 Уведомление от Sergey")
                widget.show()
        time.sleep(10)

# Обработчик выхода
def on_exit(icon, item):
    icon.stop()

# Меню
menu = pystray.Menu(
    pystray.MenuItem("выход", on_exit)
)

# Трей-иконка
icon = pystray.Icon("Neural", img, menu=menu)

# 🧵 Запуск фонового потока
threading.Thread(target=main_loop, daemon=True).start()

# ▶️ Запуск интерфейса
icon.run()
