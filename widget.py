import CTkMessagebox
import customtkinter
import sys

def show():
    app = customtkinter.CTk()

    msg = CTkMessagebox.CTkMessagebox(title="Оповещение", message= "Серому шо та нада!", icon= "info", option_1="Иду")

    if msg.get() == "Иду":
        return


    app.withdraw()
    app.mainloop()