import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from can_input import CANReader
from anomaly_engine import AnomalyEngine
import os

class CANAnomalyDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN AI Anomaly Detector")

        self.anomaly_engine = AnomalyEngine()
        self.can_readers = []
        self.running = False

        self.mode = tk.StringVar(value="interface")
        self.file_paths = []
        self.interface = tk.StringVar(value="vector")
        self.channel = tk.StringVar(value="0")
        self.bitrate = tk.StringVar(value="500000")
        self.threshold = tk.DoubleVar(value=0.1)

        self.build_gui()

    def build_gui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Tryb wejścia:").grid(row=0, column=0, sticky="e")
        ttk.Radiobutton(frame, text="CAN Interfejs", variable=self.mode, value="interface").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(frame, text="Pliki logów", variable=self.mode, value="file").grid(row=0, column=2, sticky="w")

        self.files_label = ttk.Label(frame, text="Nie wybrano plików")
        self.files_label.grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Button(frame, text="Wybierz pliki", command=self.choose_files).grid(row=1, column=2)

        ttk.Label(frame, text="Interfejs:").grid(row=2, column=0, sticky="e")
        ttk.Entry(frame, textvariable=self.interface).grid(row=2, column=1, sticky="w")
        ttk.Label(frame, text="Kanał:").grid(row=3, column=0, sticky="e")
        ttk.Entry(frame, textvariable=self.channel).grid(row=3, column=1, sticky="w")
        ttk.Label(frame, text="Bitrate:").grid(row=4, column=0, sticky="e")
        ttk.Entry(frame, textvariable=self.bitrate).grid(row=4, column=1, sticky="w")

        ttk.Button(frame, text="Uczenie normalnych ramek", command=self.learn_normal).grid(row=5, column=0, pady=10)
        ttk.Button(frame, text="Start detekcji", command=self.start_detection).grid(row=5, column=1, pady=10)
        ttk.Button(frame, text="Stop", command=self.stop).grid(row=5, column=2, pady=10)

        ttk.Label(frame, text="Próg AI (MSE):").grid(row=6, column=0, sticky="e")
        ttk.Entry(frame, textvariable=self.threshold, width=10).grid(row=6, column=1, sticky="w")

        ttk.Button(frame, text="Zapisz model", command=self.save_model).grid(row=7, column=0, pady=5)
        ttk.Button(frame, text="Wczytaj model", command=self.load_model).grid(row=7, column=1, pady=5)

        columns = ("timestamp", "id", "dlc", "data", "ai", "loss", "heur")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=100 if col not in ["data", "heur"] else 200)
        self.tree.grid(row=8, column=0, padx=10, pady=10, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=8, column=1, sticky="ns")

    def choose_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Log files", "*.blf *.asc")])
        if files:
            self.file_paths = list(files)
            self.files_label.config(text=f"Wybrano {len(files)} plików")

    def prepare_readers(self):
        self.can_readers = []
        if self.mode.get() == "interface":
            self.can_readers.append(CANReader(
                source="interface",
                interface=self.interface.get(),
                channel=self.channel.get(),
                bitrate=int(self.bitrate.get())
            ))
        else:
            for path in self.file_paths:
                self.can_readers.append(CANReader(
                    source="file",
                    filepath=path
                ))

    def learn_normal(self):
        self.prepare_readers()
        self.running = True
        self.tree.delete(*self.tree.get_children())
        self.anomaly_engine.ai.threshold = self.threshold.get()
        threading.Thread(target=self._learn_thread).start()

    def start_detection(self):
        self.prepare_readers()
        self.running = True
        self.tree.delete(*self.tree.get_children())
        self.anomaly_engine.ai.threshold = self.threshold.get()
        threading.Thread(target=self._detect_thread).start()

    def stop(self):
        self.running = False

    def save_model(self):
        path = filedialog.asksaveasfilename(defaultextension=".pth", filetypes=[("Model files", "*.pth")])
        if path:
            self.anomaly_engine.ai.save_model(path)
            messagebox.showinfo("Zapisano", f"Model zapisany do {path}")

    def load_model(self):
        path = filedialog.askopenfilename(filetypes=[("Model files", "*.pth")])
        if path:
            self.anomaly_engine.ai.load_model(path)
            self.threshold.set(self.anomaly_engine.ai.threshold)
            messagebox.showinfo("Załadowano", f"Model załadowany z {path}")

    def _learn_thread(self):
        messages = []
        for reader in self.can_readers:
            for msg in reader.read():
                if not self.running:
                    break
                messages.append(msg)
                self.root.after(0, self.display_frame, msg, False, 0.0, [])
        self.anomaly_engine.train_ai(messages)

    def _detect_thread(self):
        for reader in self.can_readers:
            for msg in reader.read():
                if not self.running:
                    break
                result = self.anomaly_engine.evaluate(msg, return_loss=True)
                self.root.after(0, self.display_frame, msg, result["ai"], result.get("loss", 0.0), result["heur"])

    def display_frame(self, msg, ai_anomaly, loss, heuristics):
        self.tree.insert("", "end", values=(
            f"{msg.timestamp:.6f}",
            f"{msg.arbitration_id:X}",
            f"{msg.dlc}",
            ' '.join(f"{b:02X}" for b in msg.data),
            "TAK" if ai_anomaly else "",
            f"{loss:.5f}" if ai_anomaly else "",
            "; ".join(heuristics)
        ))
        self.tree.yview_moveto(1.0)
