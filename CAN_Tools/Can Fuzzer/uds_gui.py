import can
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import time
from uds_fuzzer import fuzz_uds_single_frame, fuzz_random_frames

def receive_frames(bus, writer, stop_event, display_callback):
    while not stop_event.is_set():
        msg = bus.recv(timeout=0.1)
        if msg is not None:
            writer.write(msg)
            display_callback(msg)

def start_fuzzer(mode, duration, interval, id_min, id_max, tx_channel, rx_channel, display_widget, extended):
    try:
        tx_bus = can.interface.Bus(interface='vector', channel=tx_channel, bitrate=500000)
        rx_bus = can.interface.Bus(interface='vector', channel=rx_channel, bitrate=500000)

        with can.BLFWriter("tx_log.blf") as tx_writer, can.BLFWriter("rx_log.blf") as rx_writer:
            stop_event = threading.Event()

            def update_display(msg):
                try:
                    msg_str = f"ID=0x{msg.arbitration_id:X} DLC={msg.dlc} Data={msg.data.hex(' ')}"
                    display_widget.insert(tk.END, msg_str + '\n')
                    display_widget.see(tk.END)
                except Exception:
                    pass

            recv_thread = threading.Thread(
                target=receive_frames,
                args=(rx_bus, rx_writer, stop_event, update_display)
            )

            if mode == "UDS Fuzzing":
                fuzz_thread = threading.Thread(
                    target=fuzz_uds_single_frame,
                    args=(tx_bus, tx_writer, stop_event, id_min, id_max, interval)
                )
            else:
                fuzz_thread = threading.Thread(
                    target=fuzz_random_frames,
                    args=(tx_bus, tx_writer, id_min, id_max, duration, interval, extended, stop_event)
                )

            recv_thread.start()
            fuzz_thread.start()
            fuzz_thread.join()
            stop_event.set()
            recv_thread.join()

            messagebox.showinfo("Zakończono", f"{mode} zakończony. Logi zapisane do tx_log.blf i rx_log.blf.")

    except Exception as e:
        messagebox.showerror("Błąd", str(e))

def create_gui():
    def on_start():
        try:
            duration = int(duration_entry.get())
            interval = int(interval_entry.get())
            id_min = int(id_min_entry.get(), 16)
            id_max = int(id_max_entry.get(), 16)
            tx_channel = int(tx_channel_var.get())
            rx_channel = int(rx_channel_var.get())
            mode = mode_var.get()
            extended = extended_var.get()

            if id_min > id_max:
                raise ValueError("Minimalne ID większe niż maksymalne")
            if tx_channel == rx_channel:
                raise ValueError("Kanały TX i RX muszą być różne")

            start_fuzzer(mode, duration, interval, id_min, id_max, tx_channel, rx_channel, live_output, extended)

        except ValueError as e:
            messagebox.showerror("Błąd", str(e))

    root = tk.Tk()
    root.title("CAN Fuzzer (Random + UDS)")

    mode_var = tk.StringVar()
    mode_combo = ttk.Combobox(root, textvariable=mode_var, values=["Random Fuzzing", "UDS Fuzzing"], state="readonly")
    mode_combo.current(0)
    mode_combo.grid(row=0, column=0, columnspan=2, pady=5)

    ttk.Label(root, text="Czas trwania [s]:").grid(row=1, column=0, sticky="e")
    duration_entry = ttk.Entry(root)
    duration_entry.insert(0, "60")
    duration_entry.grid(row=1, column=1)

    ttk.Label(root, text="Interwał [ms]:").grid(row=2, column=0, sticky="e")
    interval_entry = ttk.Entry(root)
    interval_entry.insert(0, "10")
    interval_entry.grid(row=2, column=1)

    ttk.Label(root, text="Minimalne ID (hex):").grid(row=3, column=0, sticky="e")
    id_min_entry = ttk.Entry(root)
    id_min_entry.insert(0, "0x100")
    id_min_entry.grid(row=3, column=1)

    ttk.Label(root, text="Maksymalne ID (hex):").grid(row=4, column=0, sticky="e")
    id_max_entry = ttk.Entry(root)
    id_max_entry.insert(0, "0x7FF")
    id_max_entry.grid(row=4, column=1)

    extended_var = tk.BooleanVar()
    extended_check = ttk.Checkbutton(root, text="Użyj Extended ID (29-bit)", variable=extended_var)
    extended_check.grid(row=5, column=0, columnspan=2)

    ttk.Label(root, text="Kanał TX:").grid(row=6, column=0, sticky="e")
    tx_channel_var = tk.StringVar()
    tx_combo = ttk.Combobox(root, textvariable=tx_channel_var, values=["0", "1"], state="readonly")
    tx_combo.current(0)
    tx_combo.grid(row=6, column=1)

    ttk.Label(root, text="Kanał RX:").grid(row=7, column=0, sticky="e")
    rx_channel_var = tk.StringVar()
    rx_combo = ttk.Combobox(root, textvariable=rx_channel_var, values=["0", "1"], state="readonly")
    rx_combo.current(1)
    rx_combo.grid(row=7, column=1)

    start_button = ttk.Button(root, text="Start Fuzzowania", command=on_start)
    start_button.grid(row=8, column=0, columnspan=2, pady=10)

    ttk.Label(root, text="Podgląd odebranych ramek:").grid(row=9, column=0, columnspan=2)
    live_output = tk.Text(root, height=15, width=60)
    live_output.grid(row=10, column=0, columnspan=2, padx=5, pady=5)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
