from scenario_loader import load_scenario
from can_sender import send_scenario
from can_receiver import start_receiver
import threading

def main():
    scenario = load_scenario("example_scenario.csv")
    responses = []

    recv_thread = threading.Thread(target=start_receiver, args=(responses,))
    recv_thread.daemon = True
    recv_thread.start()

    send_scenario(scenario, responses)

if __name__ == "__main__":
    main()
