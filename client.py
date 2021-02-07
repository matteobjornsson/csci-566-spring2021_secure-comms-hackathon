#!/usr/bin/env python3

import socket
from cryptography.fernet import Fernet

shared_key = b'5GH5XrQMLnAf5g6SU01pY9fgXYRt02Yi6e7C4Hoprj8='
cipher_suite = Fernet(shared_key)

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    request = b'GET:/some/secret/resource'
    encrypted_request = cipher_suite.encrypt(request)
    s.sendall(encrypted_request)
    data = s.recv(1024)

print('Sent', repr(request))
print('Sent encrypted', repr(encrypted_request))

print('Received', repr(data))
print('Received decrypted', cipher_suite.decrypt(data))
