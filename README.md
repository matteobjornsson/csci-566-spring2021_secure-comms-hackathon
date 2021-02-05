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

Following is an example of performing X25519-based, asymmetric key-exchange and then using PBKDF2 (with HMAC) key derivation to generate a base64 shared key for use with the Fernet symmetric algorithm.

Key Exchange:
https://cryptography.io/en/latest/hazmat/primitives/asymmetric/x25519.html#exchange-algorithm

Key Derivation:
https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions.html#pbkdf2

```python
from os import urandom
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey,X25519PublicKey
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# NOTE: PBKDF2HMAC backend is optional on newer cryptography library versions (e.g., 3.3.1), but
# required on older versions (e.g., 2.8).
from cryptography.hazmat.backends import default_backend

# Peers generate their respective private keys
private_key_peer1 = X25519PrivateKey.generate()
private_key_peer2 = X25519PrivateKey.generate()

# Each peer encodes their public key in a format that's easily exchanged (raw bytes, in this case)
public_key_peer1 = private_key_peer1.public_key().public_bytes(encoding = serialization.Encoding.Raw, format = serialization.PublicFormat.Raw)
public_key_peer2 = private_key_peer2.public_key().public_bytes(encoding = serialization.Encoding.Raw, format = serialization.PublicFormat.Raw)

# For the purpose of key derivation, a shared salt is required
# The salt is not inherently sensitive, and can be transmitted alongside the public key
salt = urandom(16)

# Somehow, the peers exchange their private keys, and establish a salt, such that each peer now has:
#   - Their respective private key
#   - The other peer's public key
#   - The salt

# The peers now independently calculate the shared X25519 key
shared_key_peer1 = private_key_peer1.exchange(X25519PublicKey.from_public_bytes(public_key_peer2))
shared_key_peer2 = private_key_peer2.exchange(X25519PublicKey.from_public_bytes(public_key_peer1))

# Finally, using their shared keys and salt, they perform key derivation.
# This produces a derived, shared key usable with another algorithm (in this case, Fernet).
# NOTE: The parameters of the key derivation function MUST be known to both peers. These parameters may be exchanged/agreed.
kdf_peer1 = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
kdf_peer2 = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
derived_shared_key_peer1 = base64.urlsafe_b64encode(kdf_peer1.derive(shared_key_peer1))
derived_shared_key_peer2 = base64.urlsafe_b64encode(kdf_peer2.derive(shared_key_peer2))

# The resulting keys (from the above KDF) are of an appropriate length and encoding for direct use with Fernet ('cryptography.fernet' library).
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
