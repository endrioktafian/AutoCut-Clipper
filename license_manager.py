#!/usr/bin/env python3
"""
🔐 LICENSE MANAGER - AutoCut Termux
Device-bound license validation dengan trial 7 hari
Untuk versi GitHub (public)
"""

import hashlib
import json
import os
import uuid
import base64
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple

class LicenseManager:
    """
    License validation system dengan:
    - Device binding (1 key = 1 device)
    - Trial period 7 hari
    - Encrypted key storage
    - Offline validation (no API needed untuk basic check)
    """
    
    def __init__(self, license_file: str = "~/.autocut_license"):
        self.license_file = Path(license_file).expanduser()
        self.secret_key = "autocut_secret_2026"  # Ganti dengan random string
        
        # License server URL (opsional - untuk online validation)
        self.server_url = os.environ.get("AUTOCUT_LICENSE_SERVER", "")
        
        # Trial period (days)
        self.trial_days = 7
    
    def get_device_id(self) -> str:
        """
        Get unique device ID untuk binding
        Combine multiple hardware identifiers
        """
        # Method 1: UUID (fallback)
        device_uuid = str(uuid.getnode())
        
        # Method 2: Machine ID (Linux)
        machine_id = ""
        if Path("/etc/machine-id").exists():
            machine_id = Path("/etc/machine-id").read_text().strip()
        
        # Method 3: Hostname
        import socket
        hostname = socket.gethostname()
        
        # Combine semua
        combined = f"{device_uuid}:{machine_id}:{hostname}"
        
        # Hash untuk privacy
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def generate_key(self, email: str, device_id: str = None) -> str:
        """
        Generate license key untuk diberikan ke user
        
        Format: XXXX-XXXX-XXXX-XXXX-EMAIL
        dimana XXXX = hash dari email + device_id + secret
        """
        if device_id is None:
            device_id = self.get_device_id()
        
        # Create payload
        payload = {
            "email": email.lower().strip(),
            "device": device_id,
            "created": datetime.now().isoformat(),
            "type": "trial"  # trial atau full
        }
        
        # Sign payload
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Encode ke base64
        license_data = {
            "payload": payload,
            "signature": signature
        }
        
        # Format key (base64, split jadi groups)
        key_raw = base64.b64encode(json.dumps(license_data).encode()).decode()
        key_clean = key_raw.replace("=", "").upper()
        
        # Split jadi format XXXX-XXXX-XXXX-XXXX
        key_groups = [key_clean[i:i+4] for i in range(0, min(16, len(key_clean)), 4)]
        
        # Append email (first 3 chars)
        email_prefix = email[:3].lower().strip()
        
        return "-".join(key_groups) + "-" + email_prefix
    
    def validate_key_format(self, key: str) -> bool:
        """Validate format license key"""
        # Format: XXXX-XXXX-XXXX-XXXX-XXX (email prefix)
        parts = key.split("-")
        
        if len(parts) < 5:
            return False
        
        # Check 4 bagian pertama (harus 4 char alphanumeric)
        for part in parts[:4]:
            if len(part) != 4 or not part.isalnum():
                return False
        
        return True
    
    def activate(self, license_key: str) -> Tuple[bool, str]:
        """
        Activate license key untuk device ini
        
        Returns: (success, message)
        """
        # Validate format
        if not self.validate_key_format(license_key):
            return False, "❌ Invalid license key format"
        
        try:
            # Decode key
            key_parts = license_key.upper().split("-")
            key_raw = "".join(key_parts[:4])  # Ambil 16 char pertama
            
            # Padding untuk base64
            padding = 4 - (len(key_raw) % 4)
            if padding != 4:
                key_raw += "=" * padding
            
            # Decode
            license_json = base64.b64decode(key_raw).decode()
            license_data = json.loads(license_json)
            
            # Verify signature
            payload_json = json.dumps(license_data["payload"], sort_keys=True)
            expected_sig = hmac.new(
                self.secret_key.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if license_data.get("signature") != expected_sig:
                return False, "❌ Invalid license signature"
            
            # Check payload
            payload = license_data["payload"]
            device_id = self.get_device_id()
            
            # Check device binding (jika device specified)
            if payload.get("device") and payload["device"] != device_id:
                return False, "❌ License key terikat ke device lain"
            
            # Check expiry
            created = datetime.fromisoformat(payload["created"])
            license_type = payload.get("type", "trial")
            
            if license_type == "trial":
                expiry = created + timedelta(days=self.trial_days)
            else:  # full license
                expiry = created + timedelta(days=365)  # 1 tahun
            
            if datetime.now() > expiry:
                return False, f"❌ License expired pada {expiry.strftime('%Y-%m-%d')}"
            
            # Save license
            license_info = {
                "key": license_key,
                "payload": payload,
                "activated": datetime.now().isoformat(),
                "device_id": device_id,
                "expiry": expiry.isoformat(),
                "type": license_type
            }
            
            # Save ke file (encrypted simple)
            self._save_license(license_info)
            
            return True, f"✅ License activated! Type: {license_type}, Exp: {expiry.strftime('%Y-%m-%d')}"
            
        except Exception as e:
            return False, f"❌ Activation error: {str(e)}"
    
    def _save_license(self, license_info: Dict):
        """Save license info ke file"""
        # Simple encryption (XOR dengan secret)
        license_json = json.dumps(license_info, indent=2)
        
        # XOR encrypt (simple, bukan crypto-grade)
        secret_bytes = (self.secret_key * (len(license_json) // len(self.secret_key) + 1))[:len(license_json)]
        encrypted = bytes(a ^ b for a, b in zip(license_json.encode(), secret_bytes.encode()))
        
        # Save
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        self.license_file.write_bytes(encrypted)
        self.license_file.chmod(0o600)  # Hanya owner bisa baca
    
    def _load_license(self) -> Optional[Dict]:
        """Load license info dari file"""
        if not self.license_file.exists():
            return None
        
        try:
            # XOR decrypt
            encrypted = self.license_file.read_bytes()
            secret_bytes = (self.secret_key * (len(encrypted) // len(self.secret_key) + 1))[:len(encrypted)]
            decrypted = bytes(a ^ b for a, b in zip(encrypted, secret_bytes.encode()))
            
            return json.loads(decrypted.decode())
        except Exception:
            return None
    
    def check(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Check license status
        
        Returns: (is_valid, message, license_info)
        """
        license_info = self._load_license()
        
        if not license_info:
            return False, "❌ No license found. Please activate first.", None
        
        # Check expiry
        expiry = datetime.fromisoformat(license_info["expiry"])
        
        if datetime.now() > expiry:
            return False, f"❌ License expired pada {expiry.strftime('%Y-%m-%d')}", license_info
        
        # Check device binding
        device_id = self.get_device_id()
        if license_info.get("device_id") != device_id:
            return False, "❌ License tidak cocok dengan device ini", license_info
        
        # Valid
        license_type = license_info.get("type", "trial")
        days_left = (expiry - datetime.now()).days
        
        if license_type == "trial":
            msg = f"✓ Trial license ({days_left} hari lagi)"
        else:
            msg = f"✓ Full license (exp: {expiry.strftime('%Y-%m-%d')})"
        
        return True, msg, license_info
    
    def status(self) -> str:
        """Get human-readable license status"""
        is_valid, message, info = self.check()
        
        if not is_valid:
            return message
        
        status_lines = [
            "╔════════════════════════════════════════╗",
            "║     🔐 AUTOCUT LICENSE STATUS          ║",
            "╠════════════════════════════════════════╣",
            f"║  Status: {'ACTIVE ✓' if is_valid else 'INACTIVE ✗':<26}║",
        ]
        
        if info:
            status_lines.append(f"║  Type: {info.get('type', 'unknown'):<29}║")
            status_lines.append(f"║  Email: {info.get('payload', {}).get('email', 'N/A'):<27}║")
            status_lines.append(f"║  Expires: {info.get('expiry', 'N/A')[:10]:<25}║")
            status_lines.append(f"║  Device: {info.get('device_id', 'N/A')[:20]}...{'':>6}║")
        
        status_lines.append("╚════════════════════════════════════════╝")
        
        return "\n".join(status_lines)
    
    def deactivate(self) -> bool:
        """Deactivate license (delete license file)"""
        if self.license_file.exists():
            self.license_file.unlink()
            return True
        return False
    
    def generate_server_key(self, email: str, license_type: str = "trial", 
                           device_id: str = None, days: int = None) -> str:
        """
        Generate license key (untuk admin/server side)
        
        Ini yang lo pake untuk generate key buat customer
        """
        if device_id is None:
            device_id = "any"  # Bisa dipake di device manapun
        
        payload = {
            "email": email.lower().strip(),
            "device": device_id if device_id != "any" else None,
            "created": datetime.now().isoformat(),
            "type": license_type
        }
        
        if days:
            payload["custom_days"] = days
        
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        license_data = {
            "payload": payload,
            "signature": signature
        }
        
        key_raw = base64.b64encode(json.dumps(license_data).encode()).decode()
        key_clean = key_raw.replace("=", "").upper()
        key_groups = [key_clean[i:i+4] for i in range(0, min(16, len(key_clean)), 4)]
        
        # Pad dengan zeros jika kurang
        while len(key_groups) < 4:
            key_groups.append("0000")
        
        email_prefix = email[:3].lower().strip()
        
        return "-".join(key_groups[:4]) + "-" + email_prefix


# CLI untuk test
if __name__ == "__main__":
    import sys
    
    lm = LicenseManager()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║     🔐 LICENSE MANAGER - AutoCut Termux                   ║
║     Generate, Activate, Validate License Keys             ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) < 2:
        print("""
Usage: python license_manager.py <command> [args]

Commands:
  status              - Check license status
  activate <key>      - Activate license key
  generate <email>    - Generate new license key (for admin)
  deactivate          - Deactivate current license
  device-id           - Show this device ID
""")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        print(lm.status())
    
    elif cmd == "activate" and len(sys.argv) >= 3:
        key = sys.argv[2]
        success, msg = lm.activate(key)
        print(msg)
        sys.exit(0 if success else 1)
    
    elif cmd == "generate" and len(sys.argv) >= 3:
        email = sys.argv[2]
        license_type = sys.argv[3] if len(sys.argv) > 3 else "trial"
        key = lm.generate_server_key(email, license_type)
        print(f"\n🔑 Generated License Key:")
        print(f"   {key}")
        print(f"\n   Type: {license_type}")
        print(f"   Email: {email}")
        print(f"\n   ⚠️  Simpan key ini dan berikan ke customer!")
    
    elif cmd == "deactivate":
        if lm.deactivate():
            print("✅ License deactivated")
        else:
            print("⚠️  No active license found")
    
    elif cmd == "device-id":
        print(f"Device ID: {lm.get_device_id()}")
    
    else:
        print(f"❌ Unknown command or missing args: {cmd}")
        sys.exit(1)