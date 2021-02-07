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
