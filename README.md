# Read this before using.
This is only for Educational Purpose.
# Software Requirements:
Python3.6+ 
It wouldn't work on lower versions of Python.
# This reverse shell has following functions:
1. Remotely access to command prompt of target system.
2. Download files from target system (Note: Not working for media files i.e MP4).
3. Taking screenshot of target system's desktop using pillow library at agent end.
4. Taking webcam photo using OpenCV module.
5. Streaming webcam of target system and sending stream to Server through second socket (Note: press 'q' to quit the stream and streaming window).
6. Persistent (Would run automatically when after system reboot or shutdown).
transferring media files can be done by implementing same function as used in transferring webcam stream to server using OpenCV module, because this is not a big project but it can be extended from anyone, you can contribute in it because it is an open source.
# The Module Requirements:
# Agent Side:
socket, os, sys, subprocess, cv2, PIL(ImageGrab), struct, pickle
# Server Side:
socket, sys, random, string, cv2, os, pickle, struct
# Usage of functions:
1. Download a file: download filename
2. Take screenshot: screenshot
3. Take cam selfie: campic
4. Stream webcam: webcam
5. Manipulate target system directories using cd command.
6. Close the connection and exit the agent: terminate
7. CMD commands can be used to manipulate target system.
# How make persistent
1. First copy the code of persistent.py and paste inside the agent.py (Note: paste right after imports of agent.py).
2. Convert agent.py into windows executable file.
3. Now execute it on target system.
4. Best of Luck :)
