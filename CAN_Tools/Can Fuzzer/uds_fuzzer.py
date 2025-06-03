import can
import random
import time

def fuzz_uds_single_frame(bus, writer, stop_event, id_min, id_max, interval_ms):
    while not stop_event.is_set():
        sid = random.randint(0x00, 0xFF)
        payload_len = random.randint(0, 6)
        payload = [random.randint(0x00, 0xFF) for _ in range(payload_len)]
        data = [sid] + payload
        can_id = random.randint(id_min, id_max)

        msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
        try:
            bus.send(msg)
            writer.write(msg)
        except can.CanError:
            continue

        time.sleep(interval_ms / 1000.0)

def fuzz_random_frames(bus, writer, id_min, id_max, duration_sec, interval_ms, extended, stop_event):
    end_time = time.time() + duration_sec
    while time.time() < end_time and not stop_event.is_set():
        can_id = random.randint(id_min, id_max)
        dlc = random.randint(0, 8)
        data = [random.randint(0x00, 0xFF) for _ in range(dlc)]
        msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=extended)
        try:
            bus.send(msg)
            writer.write(msg)
        except can.CanError:
            continue
        time.sleep(interval_ms / 1000.0)