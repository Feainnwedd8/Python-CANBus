import tkinter as tk
from tkinter import ttk, simpledialog

# Przykładowe definicje ramek i sygnałów z informacjami jak w pliku DBC
FRAME_DEFINITIONS = {
    "0x100": {
        "signals": {
            "Speed": {
                "start_bit": 0,
                "length": 16,
                "factor": 1.0,
                "offset": 0.0
            },
            "RPM": {
                "start_bit": 16,
                "length": 16,
                "factor": 0.25,
                "offset": 0.0
            }
        }
    },
    "0x200": {
        "signals": {
            "Temperature": {
                "start_bit": 0,
                "length": 8,
                "factor": 1.0,
                "offset": -40.0
            },
            "Pressure": {
                "start_bit": 8,
                "length": 8,
                "factor": 0.5,
                "offset": 0.0
            }
        }
    }
}

class TestCaseRow:
    def __init__(self, master, index, update_callback):
        self.index = index
        self.update_callback = update_callback
        self.frame = ttk.Frame(master)

        self.id_var = tk.StringVar()
        self.id_combo = ttk.Combobox(self.frame, textvariable=self.id_var, values=list(FRAME_DEFINITIONS.keys()), width=10)
        self.id_combo.grid(row=0, column=0, padx=5)
        self.id_combo.bind("<<ComboboxSelected>>", self.update_signals)

        self.signal_var = tk.StringVar()
        self.signal_combo = ttk.Combobox(self.frame, textvariable=self.signal_var, width=20)
        self.signal_combo.grid(row=0, column=1, padx=5)
        self.signal_combo.bind("<<ComboboxSelected>>", self.prompt_value_and_encode)

        self.data_var = tk.StringVar()
        self.data_entry = ttk.Entry(self.frame, textvariable=self.data_var, width=20)
        self.data_entry.grid(row=0, column=2, padx=5)

        self.expected_id_var = tk.StringVar()
        self.expected_id_combo = ttk.Combobox(self.frame, textvariable=self.expected_id_var, values=list(FRAME_DEFINITIONS.keys()), width=10)
        self.expected_id_combo.grid(row=0, column=3, padx=5)
        self.expected_id_combo.bind("<<ComboboxSelected>>", self.update_expected_signals)

        self.expected_signal_var = tk.StringVar()
        self.expected_signal_combo = ttk.Combobox(self.frame, textvariable=self.expected_signal_var, width=20)
        self.expected_signal_combo.grid(row=0, column=4, padx=5)
        self.expected_signal_combo.bind("<<ComboboxSelected>>", self.prompt_expected_value_and_encode)

        self.expected_data_var = tk.StringVar()
        self.expected_data_entry = ttk.Entry(self.frame, textvariable=self.expected_data_var, width=20)
        self.expected_data_entry.grid(row=0, column=5, padx=5)

        self.frame.pack(pady=2, fill="x")

    def update_signals(self, event):
        frame_id = self.id_var.get()
        signals = FRAME_DEFINITIONS.get(frame_id, {}).get("signals", {})
        self.signal_combo["values"] = list(signals.keys())
        self.signal_combo.set("")
        self.data_var.set("")

    def update_expected_signals(self, event):
        frame_id = self.expected_id_var.get()
        signals = FRAME_DEFINITIONS.get(frame_id, {}).get("signals", {})
        self.expected_signal_combo["values"] = list(signals.keys())
        self.expected_signal_combo.set("")
        self.expected_data_var.set("")

    def prompt_value_and_encode(self, event):
        frame_id = self.id_var.get()
        signal_name = self.signal_var.get()
        value_str = simpledialog.askstring("Wartość sygnału", f"Podaj wartość (dec lub 0xHEX) dla {signal_name}:")
        if value_str:
            self.data_var.set(self.encode_signal_to_data(frame_id, signal_name, value_str))

    def prompt_expected_value_and_encode(self, event):
        frame_id = self.expected_id_var.get()
        signal_name = self.expected_signal_var.get()
        value_str = simpledialog.askstring("Oczekiwana wartość sygnału", f"Podaj wartość (dec lub 0xHEX) dla {signal_name}:")
        if value_str:
            self.expected_data_var.set(self.encode_signal_to_data(frame_id, signal_name, value_str))

    def encode_signal_to_data(self, frame_id, signal_name, value_str):
        try:
            signal = FRAME_DEFINITIONS[frame_id]["signals"][signal_name]
            factor = signal["factor"]
            offset = signal["offset"]
            length = signal["length"]
            start_bit = signal["start_bit"]

            if value_str.lower().startswith("0x"):
                physical = int(value_str, 16)
            else:
                physical = float(value_str)

            raw = int((physical - offset) / factor)
            data = [0] * 8

            for i in range(length):
                bit_val = (raw >> i) & 1
                absolute_bit = start_bit + i
                byte_index = absolute_bit // 8
                bit_index = absolute_bit % 8
                data[byte_index] |= bit_val << bit_index

            return ''.join(f'{b:02X}' for b in data)
        except Exception as e:
            print(f"Błąd kodowania: {e}")
            return ""

    def get_data(self):
        return {
            "id": self.id_var.get(),
            "data": self.data_var.get(),
            "expectedResponseId": self.expected_id_var.get(),
            "expectedResponseData": self.expected_data_var.get()
        }

class CanTestGui:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN Test Case Builder")

        self.test_cases = []

        header = ttk.Label(self.root, text="ID | Signal | Data | Expected ID | Expected Signal | Expected Data", font=("Arial", 10, "bold"))
        header.pack(pady=5)

        self.case_container = ttk.Frame(self.root)
        self.case_container.pack()

        self.add_button = ttk.Button(self.root, text="+ Add Test Case", command=self.add_test_case)
        self.add_button.pack(pady=5)

        self.run_button = ttk.Button(self.root, text="Run Test Suite", command=self.run_tests)
        self.run_button.pack(pady=5)

        self.result_box = tk.Text(self.root, height=10, state="disabled")
        self.result_box.pack(pady=5, fill="both")

        self.add_test_case()

    def add_test_case(self):
        row = TestCaseRow(self.case_container, len(self.test_cases), self.update_test_case)
        self.test_cases.append(row)

    def update_test_case(self, index, field, value):
        self.test_cases[index][field] = value

    def run_tests(self):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", tk.END)
        for i, row in enumerate(self.test_cases):
            data = row.get_data()
            self.result_box.insert(tk.END, f"Test Case {i+1}: {data}\n")
        self.result_box.configure(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = CanTestGui(root)
    root.mainloop()
