import tkinter as tk
from tkinter import messagebox
import threading
import time
import keyboard

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Clicker")
        self.label = tk.Label(root, text="Wciśnij F6 by rozpocząć")
        self.label.pack(pady=20)
        self.running = False
        self.thread = None

    def start_stop(self, event):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.type_h)
            self.thread.start()
        else:
            self.running = False
            if self.thread is not None:
                self.thread.join()

    def type_h(self):
        while self.running:
            for _ in range(10):
                if not self.running:
                    break
                keyboard.write('h')
                time.sleep(2)
            if not self.running:
                break
            keyboard.write('\b' * 10)

def main():
    root = tk.Tk()
    app = App(root)
    keyboard.on_press_key("F6", app.start_stop)
    root.mainloop()

if __name__ == "__main__":
    main()

