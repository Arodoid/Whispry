import tkinter as tk
from threading import Thread

def show_popup(text):
    def popup():
        root = tk.Tk()
        root.title("AI Assistant Response")
        root.geometry("300x100")
        tk.Label(root, text=text, wraplength=280, padx=10, pady=10).pack()

        quit_button = tk.Button(root, text="Quit", command=root.destroy)
        quit_button.pack(pady=10)

        root.mainloop()

    thread = Thread(target=popup)
    thread.daemon = True
    thread.start()