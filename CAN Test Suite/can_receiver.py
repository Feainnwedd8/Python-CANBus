import can
import time

bus = can.interface.Bus(bustype='vector', channel='0', bitrate=500000)

def start_receiver(response_store, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        msg = bus.recv(1.0)
        if msg:
            print(f"[RX] Received: ID=0x{msg.arbitration_id:X}, Data={msg.data.hex()}")
            response_store.append(msg)
