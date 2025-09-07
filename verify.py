# verify_certificate.py
import json
import base64
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

def verify_certificate(json_path, public_key_path):
    """
    Verifies the digital signature of a JSON wipe certificate.

    :param json_path: Path to the generated JSON certificate file.
    :param public_key_path: Path to the public key used for verification.
    :return: True if valid, False otherwise.
    """
    print(f"🔑 Verifying '{json_path}' using '{public_key_path}'...")

    try:
        # 1. Load the public key
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        # 2. Load the JSON certificate data
        with open(json_path, 'r') as f:
            data = json.load(f)

        # 3. Separate the signature from the rest of the data.
        # The signature must be verified against the original message.
        if 'signature' not in data:
            print("❌ ERROR: No 'signature' field found in the JSON file.")
            return False
            
        signature_b64 = data.pop('signature')
        signature = base64.b64decode(signature_b64)

        # 4. Re-create the original message that was signed.
        # It must be in the EXACT same format (indentation, encoding).
        original_message = json.dumps(data, indent=4).encode('utf-8')

        # 5. Perform the verification
        public_key.verify(
            signature,
            original_message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        print("\n✅ SUCCESS: Signature is valid!")
        print("   The certificate is authentic and has not been tampered with.")
        return True

    except FileNotFoundError as e:
        print(f"❌ ERROR: File not found - {e}")
        return False
    except InvalidSignature:
        print("\n❌ FAILED: Invalid Signature!")
        print("   The certificate is NOT authentic or has been TAMPERED with.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 verify_certificate.py <path_to_certificate.json> <path_to_public_key.pem>")
        sys.exit(1)

    cert_file = sys.argv[1]
    key_file = sys.argv[2]
    verify_certificate(cert_file, key_file)