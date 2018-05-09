import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def validate_google_billing_purchase(public_base64_key: str, signed_data: str, signature: str) -> bool:
    public_key = serialization.load_der_public_key(
            base64.b64decode(public_base64_key), backend=default_backend()
        )
    # note the signature is base64 encoded
    signature = base64.b64decode(signature.encode())
    # as per https://developer.android.com/google/play/billing/billing_reference.html
    # the signature uses "the RSASSA-PKCS1-v1_5 scheme"
    try:
        public_key.verify(signature, signed_data.encode(), padding.PKCS1v15(), hashes.SHA1())
        return True
    except InvalidSignature:
        return False
