import json
import ecdsa
import base64


def create_signed_message(payload: str, private_key: ecdsa.SigningKey, public_key: ecdsa.VerifyingKey, sequence_nb: int) -> dict:
    """ Creates a message to be signed using the sequence number as nonce"""

    header = {
        "sequence_nb": sequence_nb,
        "public_key": public_key.to_string().hex()
    }

    signature = private_key.sign(
        base64.b64encode(
            json.dumps(header).encode() + ".".encode() + json.dumps(payload).encode())).hex()

    return {
        "header": header,
        "payload": payload,
        "signature": signature
    }


def verify_signed_message(header: dict, payload: dict, signature: str) -> bool:
    """ Verifies a signed message """

    try:
        public_key = ecdsa.VerifyingKey.from_string(
            bytes.fromhex(header['public_key']), curve=ecdsa.SECP256k1)
        public_key.verify(bytes.fromhex(signature),
                          base64.b64encode(json.dumps(header).encode() + ".".encode() + json.dumps(payload).encode()))
    except ecdsa.BadSignatureError:
        return False
    return True


def tests():
    """ Tests """

    # Create keys
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()
    address = public_key.to_string().hex()

    # Nonce
    sequence_nb = 0

    # A common message
    payload = {
        "amount": 10
    }

    # Create a signed message
    signed = create_signed_message(
        payload, private_key, public_key, sequence_nb)

    # Verify the signed message
    assert verify_signed_message(
        signed['header'], signed['payload'], signed['signature']) == True

    print("Tests passed")


if __name__ == "__main__":
    tests()
