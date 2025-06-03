import can
import os

class CANReader:
    def __init__(self, source, interface=None, channel=None, bitrate=None, filepath=None):
        self.source = source
        self.reader = None
        self.bus = None

        if source == "interface":
            self.bus = can.interface.Bus(
                interface=interface,
                channel=channel,
                bitrate=bitrate
            )
        elif source == "file":
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".blf":
                self.reader = can.BLFReader(filepath)
            elif ext == ".asc":
                self.reader = can.ASCReader(filepath)
            else:
                raise ValueError("Nieobsługiwany format pliku logu.")
        else:
            raise ValueError("Nieznane źródło: podaj 'interface' lub 'file'")

    def read(self):
        if self.source == "interface":
            for msg in self.bus:
                yield msg
        else:
            for msg in self.reader:
                yield msg
