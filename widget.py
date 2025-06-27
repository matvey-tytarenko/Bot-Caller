import CTkMessagebox
import customtkinter
import sys
import threading
from playsound import playsound as ps


def notification():
    ps("notification.mp3")

def show():
    # Starting in background
    threading.Thread(target=notification, daemon=True).start()

    app = customtkinter.CTk()
    msg = CTkMessagebox.CTkMessagebox(title="Оповещение", message= "Серому шо та нада!", icon= "info", option_1="Иду")
    
    if msg.get() == "Иду":
        return

    app.withdraw()
    app.mainloop()