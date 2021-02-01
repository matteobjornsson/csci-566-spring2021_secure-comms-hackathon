# CSCI 566: Secure Communications Hackathon

## Environment

The virtual machine used for the direct communications hackathon is recommended. No further setup should be needed in the VM.

Otherwise, a Python 3 environment with the `pyca/cryptography` library installed is required. Please refer to [https://cryptography.io/en/latest/installation.html](https://cryptography.io/en/latest/installation.html).

## Overview

The recommended crypto library for this hackathon is the `pyca/cryptography` library [https://cryptography.io/en/latest/](https://cryptography.io/en/latest/).


In increasing order of complexity:

- Encrypt the resource returned by the server using a preshared, symmetric key and Fernet
	- [A good Fernet example snippet](https://docs.python-guide.org/scenarios/crypto/#example)
- Encrypt the full exchange (request and response) using a preshared, symmetric key
- Exchange a shared key for symmetric encryption, using asymmetric primitives

Following is a *one-sided* (both sides need the others' public key, to derive the shared key!) example of performing X25519-based, asymmetric key-exchange and then using PBKDF2 (with HMAC) key derivation to generate a base64 shared key for use with the Fernet symmetric algorithm.

Key Exchange:
https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x25519.html#exchange-algorithm

Key Derivation:
https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions.html#pbkdf2

```python
from os import urandom
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Generate a private key for use in the exchange.
private_key = X25519PrivateKey.generate()

# In a real handshake the peer_public_key will be received from the
# other party. For this example we'll generate another private key and
# get a public key from that. Note that in a DH handshake both peers
# must agree on a common set of parameters.
peer_public_key = X25519PrivateKey.generate().public_key()

shared_key = private_key.exchange(peer_public_key)

# Perform key derivation, to produce a derived, shared key usable
# with another algorithm (in this case, Fernet).
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=urandom(16),iterations=100000,)
derived_shared_key = base64.urlsafe_b64encode(kdf.derive(shared_key))
```

Much more involved things you could implement:

- Perform symmetric encryption using raw primitives from the Python cryptography "hazmat" layer
	- AES in CBC mode is recommended (Fernet is based on AES 128 in CBC mode)
	- This is much more involved and will require some additional background reading!
	- [https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption.html](https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption.html)
- Authenticate the server to the client (or the client to the server!) using asymmetric encryption and preshared public keys
	- You could go even further and generate "self-signed" X.509 certificates (which are used by protocols like TLS to serve, for example, HTTPS services)
	- [https://cryptography.io/en/latest/x509/index.html](https://cryptography.io/en/latest/x509/index.html)

## Client/Server Overview

The provided client and server communicate (initially, insecurely) over TCP. The server listens on TCP port 65432 bound to `127.0.0.1`.

The server runs in two simple loops.
First, it loops awaiting a connection.
When connected, it loops receiving, parsing and returning messages.
Upon disconnect, it resumes awaiting a connection.

The server parses the payload of received messages looking for a "request" in the trivial format `<REQUEST TYPE>:<REQUEST PARAMETER(s)>` (for example, `GET:/some/resource`). In the case of a "GET" request (the only thing implemented), a hardcoded "resource" is returned in the format `OK:<REQUESTED RESOURCE>:<RESOURCE CONTENT>` (for example, `OK:/requested/resource:ResourceContent`). In the case of an error (unparseable request, unimplemented request type, etc.) the string `ERROR` is returned.

The server continues accepting messages from a connected client until the session is terminated, at which point it resumes listening for a new connection. The server is purely synchronous and therefore handles only one connection at a time.

## Client/Server Usage

Run `server.py` (i.e., `python3 server.py`). The server will begin awaiting a connection.

Run `client.py`. The client will connect to the server, send a message, print the response, and terminate. The server will then await a new connection.
