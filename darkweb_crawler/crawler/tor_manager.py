import time
import random
import socket
from stem import Signal
from stem.control import Controller

class TorManager:
    """Manages Tor circuit rotation for enhanced anonymity"""
    
    def __init__(self, password=None, control_port=9051, check_port=9050):
        self.password = password
        self.control_port = control_port
        self.check_port = check_port
    
    def rotate_circuit(self):
        """Rotate to a new Tor circuit (new IP)"""
        try:
            # Check if Tor service is running
            if not self.is_tor_running():
                print("⚠️ Tor doesn't appear to be running. Please start Tor service first.")
                return False
                
            # Try to connect to control port
            with Controller.from_port(port=self.control_port) as controller:
                if self.password:
                    controller.authenticate(password=self.password)
                else:
                    # Try no-auth connection
                    try:
                        controller.authenticate()
                    except Exception:
                        print("⚠️ Failed to authenticate with Tor Controller. If using password auth, provide it in TorManager initialization.")
                        return False
                
                # Send NEWNYM signal to rotate circuit
                print("🔄 Rotating Tor circuit to get a new identity...")
                controller.signal(Signal.NEWNYM)
                
                # Add slight delay to allow circuit to establish
                time.sleep(random.uniform(2.0, 5.0))
                print("✅ Tor circuit rotated successfully!")
                return True
                
        except ConnectionRefusedError:
            print("⚠️ Connection to Tor control port refused. Is Tor running with ControlPort enabled?")
            print("👉 Make sure your torrc file has: ControlPort 9051")
            return False
        except Exception as e:
            print(f"⚠️ Circuit rotation failed: {str(e)}")
            return False
    
    def is_tor_running(self):
        """Check if Tor SOCKS proxy is running on the expected port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', self.check_port))
            sock.close()
            return result == 0
        except:
            return False 