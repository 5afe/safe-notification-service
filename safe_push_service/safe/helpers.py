import base64

from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def validate_google_billing_purchase(public_base64_key: str, signed_data: str, signature: str) -> bool:
    public_key = RSA.importKey(base64.standard_b64decode(public_base64_key))
    verifier = PKCS1_v1_5.new(public_key)
    data_hash = SHA.new(signed_data.encode())
    decoded_signature = base64.b64decode(signature)
    return verifier.verify(data_hash, decoded_signature)
