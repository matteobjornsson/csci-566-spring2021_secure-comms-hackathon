#!/usr/bin/env python3

import socket
from cryptography.fernet import Fernet
shared_key = b'5GH5XrQMLnAf5g6SU01pY9fgXYRt02Yi6e7C4Hoprj8='
cipher_suite = Fernet(shared_key)
# cipher_text = cipher_suite.encrypt(b"A really secret message. Not for prying eyes.")
# plain_text = cipher_suite.decrypt(cipher_text)


HOST = '127.0.0.1'
PORT = 65432

# GET -> SUCCESS/FAILURE format scheme
# 
# GET format:
# 'GET:/some/resource/path'
#
# Successful response format:
# 'OK:/the/request/resource/path:ArbitraryResourceData'
#
# Error response format:
# 'ERROR'



# Requests are expected to be of the format 'TYPE:PARAMS'
# Locates the first separator (':') occurrence, then splits and return the TYPE and PARAMS as a tuple
def parseRequest(data):
    separator = data.find(b':')
    requestType = data[:separator]
    requestData = data[separator+1:]
    return (requestType, requestData)



# Some function that ostensibly returns some specific resource
# This could be the contents of a file, the results of a database query, etc.
# For the sake of this example, it's a hardcoded string
def getResource(resource):
    return b'Some secret something that probably shouldn\'t be sent in plaintext.'



# NB: The with statement is used here to provide implicit cleanup of the socket
#     And, later, of connections
# Create an AF_INET (IPv4) SOCK_STREAM (TCP) socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

    # Set the SO_REUSEADDR socket option.
    # This ensures we can reuse the address/port combo if this socket is not properly closed
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((HOST, PORT))
    sock.listen()


    while True: # Connection accept() loop
        print('Awaiting connection...')

        # We accept and handle connections synchronously, and without threading,
        # for the sake of example simplicity.
        connection, address = sock.accept()

        with connection: # 'with' for implicit cleanup
            print('Connected by', address)


            while True: # recv() loop (clients may request multiple resources)
                data = connection.recv(1024)

                if not data:
                    print('Disconnected from ', address)
                    break # Break out of recv() loop, and return to accept() loop

                print('\tGOT\t\t' + repr(data))

                decrypted_data = cipher_suite.decrypt(data)

                print('\tGOT decrypted\t' + repr(decrypted_data))


                # Pass the raw request through a parser (hint hint, great spot for decryption)
                (requestType, requestData) = parseRequest(decrypted_data)


                # If this is a "GET" request, get the resource and return the result
                if requestType == b'GET':
                    resource = getResource(requestData) # (hint hint, great spot for encryption)

                    # Construct response as 'OK:/requested/resource:ContentOfRequestedResource'
                    response = b'OK' + b':' + requestData + b':' + resource
                    encrypted_response = cipher_suite.encrypt(response)

                    print('\tSENT \t\t' + repr(response))
                    print('\tSENT encrypted\t' + repr(encrypted_response))

                    # NB: We don't explicitly encode('utf8') here, because we're already using byte strings
                    connection.sendall(encrypted_response)


                # If we couldn't interpret this as a GET request, return an ERROR
                else:
                    connection.sendall(b'ERROR')
