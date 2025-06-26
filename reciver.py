import requests
import time
import widget

def get_server_data():
    server = "https://bot-caller-nine.vercel.app/"
    try:
        response = requests.get(server)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def main_loop():
    while True:
        data = get_server_data()
        if data:
            last_caller = data.get("Last Caller")
            message = data.get("Message", "").strip().lower()

            if last_caller == "Sergey" and message == "подойди ко мне":
                widget.show()
        time.sleep(10)


# Tray
import pystray
from PIL import Image

img = Image.open("wheelchair.png")

def on_exit():
    icon.stop()

icon = pystray.Icon("Neural", img, menu=pystray.Menu(
        pystray.MenuItem("выход", on_exit)
    ))

icon.run()

# if __name__ == '__main__':
#     main_loop()
main_loop()