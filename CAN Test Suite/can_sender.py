import time
import can

bus = can.interface.Bus(bustype='vector', channel='0', bitrate=500000)

def send_scenario(scenario, response_store):
    start_time = time.time()
    for frame in scenario:
        wait_time = frame['timestamp'] - (time.time() - start_time)
        if wait_time > 0:
            time.sleep(wait_time)

        msg = can.Message(arbitration_id=frame['id'], data=frame['data'], is_extended_id=False)
        try:
            bus.send(msg)
            print(f"[TX] Sent: ID=0x{msg.arbitration_id:X}, Data={msg.data.hex()}")
        except can.CanError:
            print("Send failed")
