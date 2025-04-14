import can
import tkinter as tk
from tkinter import filedialog

def read_blf_file(file_path):
    # Odczytanie pliku BLF
    messages = []
    with can.BLFReader(file_path) as log:
        for msg in log:
            messages.append(msg)
    return messages

def replay_can_messages(messages, channel):
    # Ustawienie interfejsu CAN
    bus = can.interface.Bus(channel=channel, interface='vector')

    for message in messages:
        # Odtwarzanie wiadomości CAN
        msg = can.Message(arbitration_id=message.arbitration_id,
                          data=message.data,
                          is_extended_id=message.is_extended_id)
        bus.send(msg)
        # Wyświetlanie wiadomości z timestampem
        print(f"Wysłano: Timestamp: {message.timestamp}, ID: {msg.arbitration_id}, Data: {msg.data.hex()}")

def select_blf_file():
    # Otwórz okno dialogowe do wyboru pliku
    root = tk.Tk()
    root.withdraw()  # Ukryj główne okno
    file_path = filedialog.askopenfilename(title="Wybierz plik BLF", filetypes=[("BLF files", "*.blf")])
    return file_path

if __name__ == "__main__":
    can_channel = '0'  # Użyj numeru kanału jako stringa, np. '0' dla pierwszego kanału

    # Wybór pliku BLF
    blf_file_path = select_blf_file()
    if blf_file_path:
        # Odczytanie pliku BLF
        messages = read_blf_file(blf_file_path)

        # Odtwarzanie wiadomości CAN
        replay_can_messages(messages, can_channel)
    else:
        print("Nie wybrano pliku BLF.")