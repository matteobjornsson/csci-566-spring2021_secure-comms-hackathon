#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    request = b'GET:/some/secret/resource'
    s.sendall(request)
    data = s.recv(1024)

print('Sent', repr(request))
print('Received', repr(data))
