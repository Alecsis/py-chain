import json
import ecdsa
import requests
import base64
from utils import create_signed_message

# Generate a private key
private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)

# Get the public key
public_key = private_key.get_verifying_key()
address = public_key.to_string().hex()

# Crytographic nonce to prevent from replay attacks
sequence_nb = 0

# Node address
node_address = "http://127.0.0.1:5000"

# Transfer 10 from faucet to me
faucet_message = {
    "route": "faucet",
    "amount": 10
}

# Create a signed message
signed_message = create_signed_message(
    faucet_message, private_key, public_key, sequence_nb)

# Send the message to the node
res = requests.post(f"{node_address}/tx", json=signed_message)
print(res.text)
if res.json()["success"]:
    print("Faucet success")
    sequence_nb += 1

# Get the balance of me
balance_message = {
    "route": "balance",
    "address": address,
}

# Send the message to the node
res = requests.post(f"{node_address}/query", json=balance_message)
print(res.text)
