import can
import threading
import time
from collections import namedtuple
from def_CAN_Bus import *
from def_Functions import *


# Globalna zmienna do przechowywania odebranych danych
received_data = {}

def process_can_message(msg):
    """Funkcja przetwarzająca odebraną wiadomość CAN."""
    frame_id = msg.arbitration_id
    data = msg.data

    # Sprawdzenie, czy ramka znajduje się w zdefiniowanych ramach
    if frame_id in DEVICE_DEFINITIONS:
        frame_definition = DEVICE_DEFINITIONS[frame_id]
        decoded_signals = {}

        for signal in frame_definition.signals:
            # Wyciąganie bitów z danych
            start_bit = signal.start_bit
            length = signal.length
            raw_value = int.from_bytes(data, byteorder='big') >> (len(data) * 8 - (start_bit + length)) & ((1 << length) - 1)

            # Przekształcanie wartości zgodnie z czynnikiem i przesunięciem
            if signal.is_signed and raw_value >= (1 << (length - 1)):
                raw_value -= (1 << length)
            decoded_value = raw_value * signal.factor + signal.offset

            decoded_signals[signal.name] = decoded_value

        # Zapisanie odebranych danych do globalnej zmiennej
        received_data[frame_id] = decoded_signals
        print(f"Odebrano dane dla ramki 0x{frame_id:X}: {decoded_signals}")

def listen_can_bus():
    """Funkcja nasłuchująca na magistrali CAN."""
    with can.interface.Bus(channel='test', interface='virtual') as bus:  # Użyj odpowiedniego kanału
        while True:
            msg = bus.recv()  # Odbierz wiadomość
            if msg is not None:
                process_can_message(msg)

if __name__ == "__main__":
    listen_can_bus()
