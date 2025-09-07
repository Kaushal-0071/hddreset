# certificate_generator.py
import json
import hashlib
import base64
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import sys

# NEW: Helper function to find bundled files
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not bundled, the base path is the directory of this script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def create_certificate(drive_info, wipe_method, wipe_status):
    """Generates and signs a wipe certificate in JSON and PDF format."""
    # ... (This function does not need to change) ...
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    cert_data = {
        "reportID": f"WIPE-{drive_info.get('serial', 'NOSERIAL')}-{int(datetime.utcnow().timestamp())}",
        "timestamp": timestamp,
        "driveInfo": {
            "model": drive_info.get('model'),
            "serial": drive_info.get('serial'),
            "size": drive_info.get('size'),
            "path": drive_info.get('path')
        },
        "wipeDetails": {
            "method": wipe_method,
            "standard": "NIST SP 800-88 Rev. 1",
            "status": "Success" if wipe_status[0] else "Failure",
            "details": wipe_status[1]
        }
    }

    cert_json = json.dumps(cert_data, indent=4).encode('utf-8')
    signature = _sign_data(cert_json)
    cert_data['signature'] = signature

    # In the bootable environment, save to a known location if possible (like a mounted USB)
    # For now, we save to the current directory, which will be in RAM.
    filename_base = cert_data['reportID']
    json_path = f"{filename_base}.json"
    pdf_path = f"{filename_base}.pdf"

    with open(json_path, 'w') as f:
        json.dump(cert_data, f, indent=4)

    _create_pdf_report(cert_data, pdf_path)
    
    return json_path, pdf_path


def _sign_data(data):
    """Signs data with the private key and returns a base64 signature."""
    # MODIFIED: Use the helper function to find the key
    private_key_path = resource_path("private_key.pem")

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def _create_pdf_report(cert_data, output_path):
    """Creates a simple PDF report from the certificate data."""
    # ... (This function does not need to change) ...
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    c.drawString(72, height - 72, "Secure Data Erasure Certificate")
    c.line(72, height - 80, width - 72, height - 80)
    
    y_pos = height - 120
    for key, value in cert_data.items():
        if key == 'signature': continue
        if isinstance(value, dict):
            c.drawString(90, y_pos, f"{key}:")
            y_pos -= 20
            for sub_key, sub_value in value.items():
                c.drawString(108, y_pos, f"{sub_key}: {sub_value}")
                y_pos -= 15
        else:
            c.drawString(90, y_pos, f"{key}: {value}")
            y_pos -= 20
            
    c.save()