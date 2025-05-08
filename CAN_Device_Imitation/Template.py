import can
import threading
import time
from collections import namedtuple
import tkinter as tk
from tkinter import messagebox

# Example Signal definition within a CAN frame
Signal = namedtuple('Signal', ['name', 'start_bit', 'length', 'is_signed', 'factor', 'offset'])

# Example Frame definition
class FrameDefinition:
    def __init__(self, frame_id, signals):
        self.frame_id = frame_id  # Extended ID
        self.signals = signals    # List of Signal objects

# Hardcoded example of frames and signals (normally from .dbc)
DEVICE_DEFINITIONS = {
    0x18FF50E5: FrameDefinition(
        frame_id=0x18FF50E5,
        signals=[
            Signal('EngineSpeed', start_bit=0, length=16, is_signed=False, factor=0.125, offset=0),
            Signal('VehicleSpeed', start_bit=16, length=8, is_signed=False, factor=1, offset=0),
        ]
    ),
    0x18FF51E5: FrameDefinition(
        frame_id=0x18FF51E5,
        signals=[
            Signal('FuelLevel', start_bit=0, length=8, is_signed=False, factor=0.4, offset=0),
        ]
    ),
}

def extract_signal(data_bytes, signal):
    raw = 0
    for i in range(len(data_bytes)):
        raw |= data_bytes[i] << (8 * i)

    mask = (1 << signal.length) - 1
    raw_value = (raw >> signal.start_bit) & mask

    if signal.is_signed:
        sign_bit = 1 << (signal.length - 1)
        if raw_value & sign_bit:
            raw_value -= (1 << signal.length)

    value = raw_value * signal.factor + signal.offset
    return value

class DeviceSimulator:
    def __init__(self, channel='PCAN_USBBUS1', bitrate=500000):
        self.bus = can.interface.Bus(
            bustype='pcan',
            channel=channel,
            bitrate=bitrate
        )
        self.running = False
        self.error_flags = [False] * 10  # List to hold error flags for TEST1 to TEST10
        self.input_values = [0] * 10  # List to hold input values

    def start(self):
        self.running = True
        self.listener_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.listener_thread.start()
        print("CAN Device Simulator started...")

    def stop(self):
        self.running = False
        self.listener_thread.join()
        self.bus.shutdown()
        print("CAN Device Simulator stopped.")

    def receive_loop(self):
        while self.running:
            msg = self.bus.recv(timeout=1)
            if msg is None:
                continue
            if msg.is_extended_id:
                self.handle_message(msg)

    def handle_message(self, msg):
        frame_def = DEVICE_DEFINITIONS.get(msg.arbitration_id, None)
        if frame_def is None:
            print(f"Received unknown frame ID {hex(msg.arbitration_id)} - ignoring")
            return

        signals_data = {}
        for signal in frame_def.signals:
            try:
                value = extract_signal(msg.data, signal)
                signals_data[signal.name] = value
            except Exception as e:
                print(f"Error extracting signal {signal.name}: {e}")
                continue

        print(f"Received frame ID {hex(msg.arbitration_id)} with signals: {signals_data}")

        output_frames = self.process_message(msg.arbitration_id, signals_data)

        for out_msg in output_frames:
            self.send_message(out_msg)

    def process_message(self, frame_id, signals_data):
        messages_to_send = []

        if frame_id == 0x18FF50E5:
            engine_speed = signals_data.get('EngineSpeed', 0)
            vehicle_speed = signals_data.get('VehicleSpeed', 0)
            print(f"Processing EngineSpeed={engine_speed}, VehicleSpeed={vehicle_speed}")

            if engine_speed > 1000:
                fuel_level_raw = int((50 / 0.4))
                data = bytearray(8)
                data[0] = fuel_level_raw & 0xFF

                msg = can.Message(
                    arbitration_id=0x18FF51E5,
                    data=data,
                    is_extended_id=True
                )
                messages_to_send.append(msg)

        return messages_to_send

    def send_message(self, msg):
        try:
            self.bus.send(msg)
            print(f"Sent frame ID {hex(msg.arbitration_id)} data {msg.data.hex()}")
        except can.CanError as e:
            print(f"Failed to send message: {e}")

    def trigger_error(self, error_index):
        self.error_flags[error_index] = True
        print(f"Error TEST{error_index + 1} triggered.")

    def set_input_value(self, index, value):
        self.input_values[index] = value
        print(f"Input value for field {index + 1} set to {value}.")

class GUI:
    def __init__(self, simulator):
        self.simulator = simulator
        self.root = tk.Tk()
        self.root.title("CAN Simulator GUI")

        self.create_error_buttons()
        self.create_input_fields()

    def create_error_buttons(self):
        for i in range(10):
            button = tk.Button(self.root, text=f"TEST{i + 1}", command=lambda i=i: self.simulator.trigger_error(i))
            button.pack(pady=5)

    def create_input_fields(self):
        self.input_entries = []
        for i in range(10):
            entry = tk.Entry(self.root)
            entry.pack(pady=5)
            self.input_entries.append(entry)

            button = tk.Button(self.root, text=f"Set Value {i + 1}", command=lambda i=i: self.set_value(i))
            button.pack(pady=5)

    def set_value(self, index):
        try:
            value = int(self.input_entries[index].get())
            self.simulator.set_input_value(index, value)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer.")

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    simulator = DeviceSimulator(channel='PCAN_USBBUS1', bitrate=500000)
    gui = GUI(simulator)
    try:
        simulator.start()
        print("Press Ctrl+C to stop the simulator")
        gui.run()
    except KeyboardInterrupt:
        print("Stopping simulator...")
        simulator.stop()
