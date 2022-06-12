from dataclasses import dataclass
from flask import Flask, request
import json
import ecdsa
import base64

from errors import *
from state import State
from utils import verify_signed_message


# Constants
PRECISION = 6
MAX_SUPPLY = 1_000_000_000_000
GENESIS_BALANCES = {
    "faucet": 1_000_000,
}

# Create state
state = State(max_supply=MAX_SUPPLY, precision=PRECISION)
for address, balance in GENESIS_BALANCES.items():
    state.mint(address, balance)

app = Flask(__name__)


def get_balance(payload: dict) -> dict:
    """ Returns the balance of an address """
    # Decompose payload
    try:
        address = payload['address']
    except KeyError:
        return {"success": False, "error": "Address is required"}

    try:
        balance = state.get_balance(address)
    except AddressDoesNotExist:
        balance = None
    return json.dumps({"success": True, "balance": balance})


def transfer(sender: str, payload: dict) -> dict:
    """ Transfers tokens from one address to another """

    # Decompose payload
    try:
        recipient = payload['to']
        amount = payload['amount']
    except:
        return {"success": False, "error": "Missing recipient or amount"}

    # Transfer tokens
    try:
        state.transfer(sender, recipient, amount)
        return json.dumps({"success": True})
    except AddressDoesNotExist:
        return json.dumps({"success": False, "error": "From address does not exist"})
    except BalanceNotEnough:
        return json.dumps({"success": False, "error": "Balance not enough"})


def faucet(sender: str, payload: dict) -> dict:
    """ Faucet tokens to an address """

    # Decompose payload
    try:
        amount = payload['amount']
    except KeyError:
        return {"success": False, "error": "Amount is required"}

    # Transfer tokens
    try:
        state.transfer("faucet", sender, amount)
        return json.dumps({"success": True})
    except MaxSupplyExceeded:
        return json.dumps({"success": False, "error": "Max supply exceeded"})


@app.route("/query", methods=["POST"])
def query():
    """ Query endpoint - doesn't require authentication """
    payload = request.get_json()

    # Decompose payload
    try:
        route = payload['route']
    except KeyError:
        return json.dumps({"success": False, "error": "Route is required"})

    # Route to correct function
    if route == "balance":
        return get_balance(payload)
    else:
        return json.dumps({"success": False, "error": "Route does not exist"})


@app.route('/tx', methods=['POST'])
def tx():
    """ 
    Process a transaction - requires authentication 

    A transaction is a signed message with the following structure:
    ```json
    {
        "header": {
            "public_key": <public key>,
            "sequence_nb": int,
        },
        "payload": {
            "route": str,
            <custom fields>
        },
        "signature": <signature>
    }
    ```

    """
    json_data = request.get_json()

    # Decompose the message
    try:
        header = json_data['header']
        payload = json_data['payload']
        signature = json_data['signature']
    except KeyError:
        return json.dumps({"success": False, "error": "Missing header, payload or signature"})

    # Decompose the header
    try:
        sender = header['public_key']
        sequence_nb = header['sequence_nb']
    except KeyError:
        return json.dumps({"success": False, "error": "Missing public_key, sequence_nb or route"})

    # Verify that the sequence number is correct
    try:
        expected_sequence_nb = state.get_sequence_nb(sender)
    except AddressDoesNotExist:
        expected_sequence_nb = 0
    if sequence_nb != expected_sequence_nb:
        return json.dumps({"success": False, "error": "Sequence number is incorrect, should be {}".format(expected_sequence_nb)})

    # Verify signature
    try:
        verify_signed_message(header, payload, signature)
    except ecdsa.BadSignatureError:
        return json.dumps({"success": False, "error": "Bad signature"})
    except KeyError:
        return json.dumps({"success": False, "error": "Missing public key or sequence number"})

    # At this point, the authenticity of the message is verified

    # Extract the route from the payload
    try:
        route = payload['route']
    except KeyError:
        return json.dumps({"success": False, "error": "Missing route"})

    # Route the payload
    if route == "faucet":
        return faucet(sender, payload)
    elif route == "transfer":
        return transfer(sender, payload)
    else:
        return json.dumps({"success": False, "error": "Unknown route"})
