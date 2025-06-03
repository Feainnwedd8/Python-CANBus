import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import can
import time

INTERFACES = ['vector', 'pcan']
DEFAULT_BITRATE = 500000

class CANLoggerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Logger / Replayer")

        self.interface_var = tk.StringVar(value=INTERFACES[0])
        self.channel_var = tk.StringVar(value="0")
        self.bitrate_var = tk.StringVar(value=str(DEFAULT_BITRATE))
        self.file_path = tk.StringVar()
        self.mode_var = tk.StringVar(value="log")
        self.loop_var = tk.BooleanVar(value=False)

        self.bus = None
        self.thread = None
        self.running = False

        self.sort_column = None
        self.sort_reverse = False

        self.build_gui()

    def build_gui(self):
        row = 0

        ttk.Label(self.root, text="Interfejs CAN:").grid(row=row, column=0, sticky="e")
        ttk.Combobox(self.root, textvariable=self.interface_var, values=INTERFACES, state="readonly").grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(self.root, text="Kanał:").grid(row=row, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.channel_var).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(self.root, text="Bitrate:").grid(row=row, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.bitrate_var).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(self.root, text="Plik logu (.blf / .asc):").grid(row=row, column=0, sticky="e")
        ttk.Entry(self.root, textvariable=self.file_path, width=40).grid(row=row, column=1)
        ttk.Button(self.root, text="Wybierz...", command=self.choose_file).grid(row=row, column=2)

        row += 1
        ttk.Label(self.root, text="Tryb:").grid(row=row, column=0, sticky="e")
        ttk.Radiobutton(self.root, text="Logowanie", variable=self.mode_var, value="log").grid(row=row, column=1, sticky="w")
        ttk.Radiobutton(self.root, text="Odtwarzanie", variable=self.mode_var, value="replay").grid(row=row, column=1)

        row += 1
        ttk.Checkbutton(self.root, text="Odtwarzanie w pętli", variable=self.loop_var).grid(row=row, column=1, sticky="w")

        row += 1
        self.start_button = ttk.Button(self.root, text="Start", command=self.start)
        self.start_button.grid(row=row, column=0, pady=10)
        self.stop_button = ttk.Button(self.root, text="Stop", command=self.stop, state="disabled")
        self.stop_button.grid(row=row, column=1, pady=10)

        # --- Treeview ---
        row += 1
        columns = ("timestamp", "can_id", "dlc", "data")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col.upper(), command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100 if col != "data" else 200)

        self.tree.grid(row=row, column=0, columnspan=3, pady=10, padx=5, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=row, column=3, sticky="ns")

        # Rozszerzalność layoutu
        self.root.grid_rowconfigure(row, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def choose_file(self):
        if self.mode_var.get() == "log":
            file = filedialog.asksaveasfilename(defaultextension=".blf", filetypes=[("BLF files", "*.blf"), ("ASC files", "*.asc")])
        else:
            file = filedialog.askopenfilename(filetypes=[("BLF files", "*.blf"), ("ASC files", "*.asc")])
        if file:
            self.file_path.set(file)

    def start(self):
        try:
            bitrate = int(self.bitrate_var.get())
            self.bus = can.interface.Bus(
                interface=self.interface_var.get(),
                channel=self.channel_var.get(),
                bitrate=bitrate
            )
        except Exception as e:
            messagebox.showerror("Błąd połączenia", f"Nie udało się połączyć z magistralą CAN:\n{e}")
            return

        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # wyczyść Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        if self.mode_var.get() == "log":
            self.thread = threading.Thread(target=self.log_messages)
        else:
            self.thread = threading.Thread(target=self.replay_log)
        self.thread.start()

    def stop(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def log_messages(self):
        try:
            ext = os.path.splitext(self.file_path.get())[1].lower()
            if ext == ".blf":
                writer = can.BLFWriter(open(self.file_path.get(), "wb"))
            elif ext == ".asc":
                writer = can.ASCWriter(open(self.file_path.get(), "w"))
            else:
                raise ValueError("Nieobsługiwany format pliku")

            with writer:
                for msg in self.bus:
                    if not self.running:
                        break
                    writer.write(msg)
                    self.root.after(0, self.display_message, msg)
        except Exception as e:
            messagebox.showerror("Błąd logowania", str(e))
        finally:
            self.stop()

    def replay_log(self):
        try:
            ext = os.path.splitext(self.file_path.get())[1].lower()
            if ext == ".blf":
                reader = can.BLFReader(self.file_path.get())
            elif ext == ".asc":
                reader = can.ASCReader(self.file_path.get())
            else:
                raise ValueError("Nieobsługiwany format pliku")

            while self.running:
                for msg in reader:
                    if not self.running:
                        break
                    self.bus.send(msg)
                    time.sleep(0.001)
                if not self.loop_var.get():
                    break
        except Exception as e:
            messagebox.showerror("Błąd odtwarzania", str(e))
        finally:
            self.stop()

    def display_message(self, msg):
        self.tree.insert("", "end", values=(
            f"{msg.timestamp:.6f}",
            f"{msg.arbitration_id:X}",
            f"{msg.dlc}",
            ' '.join(f"{b:02X}" for b in msg.data)
        ))
        self.tree.yview_moveto(1.0)

    def sort_by_column(self, col):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

        if col == self.sort_column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = col

        try:
            if col in ["timestamp", "dlc"]:
                data.sort(key=lambda t: float(t[0]), reverse=self.sort_reverse)
            elif col == "can_id":
                data.sort(key=lambda t: int(t[0], 16), reverse=self.sort_reverse)
            else:
                data.sort(key=lambda t: t[0], reverse=self.sort_reverse)
        except Exception:
            data.sort(reverse=self.sort_reverse)

        for index, (val, k) in enumerate(data):
            self.tree.move(k, '', index)

# Start aplikacji
if __name__ == "__main__":
    root = tk.Tk()
    app = CANLoggerGUI(root)
    root.mainloop()
