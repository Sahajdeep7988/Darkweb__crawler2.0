from stem import Signal
from stem.control import Controller
import time

class TorManager:
    def __init__(self, control_port=9051):
        self.control_port = control_port
        
    def rotate_circuit(self):
        """Rotate Tor circuit for new identity"""
        try:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                time.sleep(5)  # Wait for new circuit
            return True
        except Exception as e:
            print(f"⚠️ Circuit rotation failed: {e}")
            return False 