#!/usr/bin/env python3
"""
🖥️ LICENSE SERVER - AutoCut Termux
Simple Flask API untuk license validation
Host di VPS lo atau local untuk testing
"""

from flask import Flask, request, jsonify
from datetime import datetime
import hashlib
import hmac
import json
import os

app = Flask(__name__)

# Secret key (SAMA dengan yang di license_manager.py)
SECRET_KEY = "autocut_secret_2026"

# In-memory database (ganti dengan SQLite/PostgreSQL untuk production)
LICENSES_DB = {}

# Endpoint: Generate license key
@app.route("/api/v1/license/generate", methods=["POST"])
def generate_license():
    """
    Generate license key untuk customer
    
    Body:
    {
        "email": "customer@email.com",
        "type": "trial" | "full",
        "days": 7 (optional, untuk custom expiry)
    }
    """
    data = request.json
    
    if not data or "email" not in data:
        return jsonify({"error": "Email required"}), 400
    
    email = data["email"].lower().strip()
    license_type = data.get("type", "trial")
    days = data.get("days")
    
    # Generate payload
    payload = {
        "email": email,
        "device": None,  # Bisa dipake di device manapun
        "created": datetime.now().isoformat(),
        "type": license_type
    }
    
    if days:
        payload["custom_days"] = days
    
    # Sign
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Encode
    import base64
    license_data = {"payload": payload, "signature": signature}
    key_raw = base64.b64encode(json.dumps(license_data).encode()).decode()
    key_clean = key_raw.replace("=", "").upper()
    key_groups = [key_raw[i:i+4] for i in range(0, min(16, len(key_clean)), 4)]
    
    while len(key_groups) < 4:
        key_groups.append("0000")
    
    email_prefix = email[:3].lower()
    license_key = "-".join(key_groups[:4]) + "-" + email_prefix
    
    # Save ke database
    LICENSES_DB[email] = {
        "key": license_key,
        "payload": payload,
        "created": datetime.now().isoformat(),
        "status": "active"
    }
    
    return jsonify({
        "success": True,
        "license_key": license_key,
        "email": email,
        "type": license_type
    })


# Endpoint: Validate license
@app.route("/api/v1/license/validate", methods=["POST"])
def validate_license():
    """
    Validate license key (online check)
    
    Body:
    {
        "key": "XXXX-XXXX-XXXX-XXXX-xxx",
        "device_id": "device-uuid"
    }
    """
    data = request.json
    
    if not data or "key" not in data:
        return jsonify({"error": "License key required"}), 400
    
    license_key = data["key"]
    device_id = data.get("device_id")
    
    # Decode key
    try:
        key_parts = license_key.upper().split("-")
        key_raw = "".join(key_parts[:4])
        
        import base64
        padding = 4 - (len(key_raw) % 4)
        if padding != 4:
            key_raw += "=" * padding
        
        license_json = base64.b64decode(key_raw).decode()
        license_data = json.loads(license_json)
        
        payload = license_data["payload"]
        signature = license_data["signature"]
        
        # Verify signature
        payload_json = json.dumps(payload, sort_keys=True)
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_sig:
            return jsonify({
                "valid": False,
                "error": "Invalid license signature"
            })
        
        # Check expiry
        from datetime import timedelta
        created = datetime.fromisoformat(payload["created"])
        license_type = payload.get("type", "trial")
        
        if license_type == "trial":
            custom_days = payload.get("custom_days", 7)
            expiry = created + timedelta(days=custom_days)
        else:
            expiry = created + timedelta(days=365)
        
        if datetime.now() > expiry:
            return jsonify({
                "valid": False,
                "error": "License expired",
                "expired_at": expiry.isoformat()
            })
        
        # Check device binding (optional)
        if payload.get("device") and device_id:
            if payload["device"] != device_id:
                return jsonify({
                    "valid": False,
                    "error": "License bound to different device"
                })
        
        # Valid!
        return jsonify({
            "valid": True,
            "email": payload["email"],
            "type": license_type,
            "expiry": expiry.isoformat(),
            "days_remaining": (expiry - datetime.now()).days
        })
        
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 500


# Endpoint: Check server health
@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "licenses_count": len(LICENSES_DB)
    })


# Endpoint: List all licenses (admin only - add auth untuk production)
@app.route("/api/v1/licenses", methods=["GET"])
def list_licenses():
    return jsonify({
        "licenses": [
            {
                "email": email,
                "key": data["key"],
                "type": data["payload"]["type"],
                "created": data["created"],
                "status": data["status"]
            }
            for email, data in LICENSES_DB.items()
        ]
    })


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoCut License Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║     🖥️  AUTOCUT LICENSE SERVER                            ║
║     Flask API untuk license validation                    ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    print(f"\n📡 Server running on http://{args.host}:{args.port}")
    print("\nEndpoints:")
    print("  POST /api/v1/license/generate  - Generate new license key")
    print("  POST /api/v1/license/validate  - Validate license key")
    print("  GET  /api/v1/health            - Health check")
    print("  GET  /api/v1/licenses          - List all licenses (admin)")
    print("\n⚠️  Press Ctrl+C to stop\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)