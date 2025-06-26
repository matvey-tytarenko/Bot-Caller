# Hot keys
import keyboard
import requests
import config

def on_hotkey():
    print("CTRL + Space is pressed!")
    server = "https://bot-caller-nine.vercel.app/"
    try:
        requests.post(server + '/api/call', json={"user": "Sergey", "message": "подойди ко мне"})
        print("Message will sent!")
    except Exception as e:
        print('Error:' + str(e))

keyboard.add_hotkey('CTRL + Space', on_hotkey)




# Tray
import pystray
from PIL import Image

img = Image.open("wheelchair.png")

def on_clicked(icon, item):
    try:
        requests.post(server, json={"user": "Sergey", "message": "подойди ко мне"})
        print("Message will sent!")
    except Exception as e:
        print('Error: {e}')

def on_exit():
    icon.stop()

icon = pystray.Icon("Neural", img, menu=pystray.Menu(
        pystray.MenuItem("позвать матвея", on_clicked),
        pystray.MenuItem("выход", on_exit)
    ))

icon.run()