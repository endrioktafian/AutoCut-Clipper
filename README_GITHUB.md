# 🎬 AUTOCUT TERMUX

**AI-Powered Video Clipper untuk Termux - Auto-cut viral clips dari YouTube/TikTok/Instagram**

---

## ⚠️ LICENSE REQUIREMENT (GitHub Version)

**Versi ini memerlukan license key untuk berjalan.**

| License Type | Duration | Price |
|--------------|----------|-------|
| **TRIAL** | 7 hari | GRATIS |
| **FULL** | 1 tahun | Rp 99.000 |

### Cara Activate License

1. **Trial (Gratis 7 hari)**:
   - Jalankan `python autocut_github.py`
   - Pilih opsi `2. Gunakan trial gratis`
   - Trial key akan di-generate otomatis
   - Valid untuk 7 hari

2. **Full License**:
   - Beli di: **[LINK WEBSITE LO]**
   - Lo bakal dapet license key via email
   - Jalankan `python autocut_github.py`
   - Pilih opsi `1. Masukkan license key`
   - Paste key dari email

3. **Check License Status**:
   ```bash
   python license_manager.py status
   ```

---

## ✨ Features

- 📥 **Multi-platform Download** - YouTube, TikTok, Instagram, Twitter, Facebook
- 🤖 **AI Parser** - Parse output dari Gemini, Claude, ChatGPT
- ✂️ **Auto-Cut** - Cut video berdasarkan timestamp dari AI
- 📊 **Queue System** - Batch processing dengan SQLite queue
- 🎨 **Preset System** - Custom presets untuk consistent style
- 📱 **Termux Native** - Jalan di Android tanpa PC
- 🔐 **License Protected** - 1 license = 1 device

---

## 📦 Installation

### Termux (Android)

```bash
# Install dependencies
pkg update -y
pkg install python ffmpeg git wget curl

# Install Python packages
pip install yt-dlp flask

# Clone repository
git clone https://github.com/YOUR_USERNAME/autocut-termux.git
cd autocut-termux

# Run (akan minta license)
python autocut_github.py
```

### One-Command Install

```bash
curl -sL https://raw.githubusercontent.com/YOUR_USERNAME/autocut-termux/main/install.sh | bash
```

---

## 🚀 Usage

### First Run (License Activation)

```bash
python autocut_github.py

# Output:
╔═══════════════════════════════════════════════════════════╗
║     🔐 LICENSE REQUIRED                                   ║
╠═══════════════════════════════════════════════════════════╣
║  1. Masukkan license key (activate)                       ║
║  2. Gunakan trial gratis 7 hari                           ║
║  3. Exit                                                  ║
╚═══════════════════════════════════════════════════════════╝

Pilih opsi [1-3]:
```

### Main Menu

```
╔═══════════════════════════════════════════════════════════╗
║     🎬 AUTOCUT TERMUX v1.0.0-GITHUB                       ║
║     ⚠️  LICENSE REQUIRED - GitHub Version                 ║
╚═══════════════════════════════════════════════════════════╝

────────────────────────────────────────────────────────────
📋 MAIN MENU
────────────────────────────────────────────────────────────
  1. 📥 Download & Cut (URL + AI Output)
  2. ✂️  Cut Local Video (Paste AI Output)
  3. 📊 View Queue Stats
  4. 📋 Process Pending Queue
  5. 🗑️  Clear Completed Videos
  6. ⚙️  Settings
  7. 🔐 License Status
  8. ℹ️  About / Help
  0. 🚪 Exit
────────────────────────────────────────────────────────────
```

---

## 📋 AI Prompt Template

Gunakan prompt ini di Gemini/Claude untuk hasil optimal:

```
Analyze this video and identify viral clip segments (3-5 clips, 30-60 detik each).

For each clip, provide:
- Timestamp (format: MM:SS - MM:SS)
- Title/hook (catchy title)
- Why it's viral (reason)
- Suggested caption/SEO

Format output seperti ini:

KLIP [1]:
00:00 - 00:30 | Judul yang menarik
Hook: "Tahu gak sih..."
Caption: #viral #trending #fyp
Alasan Viral: Kontroversial/relatable/educational
```

---

## 🔐 License System

### How It Works

1. **Device Binding**: Setiap license key terikat ke 1 device (SHA256 hash)
2. **Trial Period**: 7 hari gratis dari first activation
3. **Full License**: Valid 365 hari
4. **Offline Validation**: No internet required setelah activation
5. **Encrypted Storage**: License disimpan encrypted di `~/.autocut_license`

### Generate License Key (Admin)

Untuk generate license key buat customer:

```bash
python license_manager.py generate customer@email.com full
```

Output:
```
🔑 Generated License Key:
   ABCD-EFGH-IJKL-MNOP-cus

   Type: full
   Email: customer@email.com

   ⚠️  Simpan key ini dan berikan ke customer!
```

### License Commands

```bash
# Check status
python license_manager.py status

# Activate key
python license_manager.py activate XXXX-XXXX-XXXX-XXXX-xxx

# Generate trial key
python license_manager.py generate trial@email.com trial

# Generate full key
python license_manager.py generate customer@email.com full

# Deactivate
python license_manager.py deactivate

# Show device ID
python license_manager.py device-id
```

---

## 🎨 Presets

Preset tersedia di `presets/` folder:

| Preset | Description |
|--------|-------------|
| `default` | Fast cut, no effects |
| `viral_style` | Zoom 1.15x, brightness +, contrast + |
| `minimal` | Just cut, fastest processing |

### Custom Preset

Edit atau buat preset baru di `presets/`:

```json
{
  "zoom": true,
  "zoom_factor": 1.15,
  "caption": false,
  "fps": 30,
  "brightness": 0.05,
  "contrast": 1.1,
  "fast_cut": false,
  "description": "My custom preset"
}
```

---

## 📁 Project Structure

```
autocut-termux/
├── autocut_github.py       # Main CLI (WITH LICENSE)
├── license_manager.py      # License validation
├── license_server.py       # Flask API server (optional)
├── parser.py               # AI output parser (FSM)
├── downloader.py           # yt-dlp wrapper
├── cutter.py               # FFmpeg wrapper
├── queue_manager.py        # SQLite queue
├── config.json             # Global config
├── presets/
│   ├── default.json
│   ├── viral_style.json
│   └── minimal.json
├── output/                 # Hasil cut
├── temp/                   # Download cache
├── logs/                   # Log files
└── install.sh              # Auto installer
```

---

## 🛠️ License Server (Optional)

Untuk online validation (multi-device sync, revoke, etc.):

```bash
# Install Flask
pip install flask

# Run license server
python license_server.py --host 0.0.0.0 --port 5000
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/license/generate` | POST | Generate new license key |
| `/api/v1/license/validate` | POST | Validate license key (online) |
| `/api/v1/health` | GET | Health check |
| `/api/v1/licenses` | GET | List all licenses (admin) |

### Example: Generate License via API

```bash
curl -X POST http://localhost:5000/api/v1/license/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "customer@email.com", "type": "full"}'
```

Response:
```json
{
  "success": true,
  "license_key": "ABCD-EFGH-IJKL-MNOP-cus",
  "email": "customer@email.com",
  "type": "full"
}
```

---

## ⚠️ Disclaimer

This tool is for **personal/educational use only**. Respect copyright and terms of service of video platforms. The authors are not responsible for misuse.

---

## 💳 Pricing

| Plan | Price | Duration | Features |
|------|-------|----------|----------|
| **TRIAL** | FREE | 7 days | All features, 1 device |
| **FULL** | Rp 99.000 | 1 year | All features, 1 device, priority support |
| **LIFETIME** | Rp 299.000 | Forever | All features, 3 devices, lifetime updates |

**Buy Now**: [LINK WEBSITE LO]

**Contact**: support@yourdomain.com

---

## 📞 Support

- **Documentation**: README.md (this file)
- **Email**: support@yourdomain.com
- **Telegram**: @yourusername
- **GitHub Issues**: [Create issue](https://github.com/YOUR_USERNAME/autocut-termux/issues)

---

## 📝 Changelog

### v1.0.0 (2026-07-05)
- Initial release
- FSM parser dengan fallback
- yt-dlp integration
- FFmpeg batch cut
- SQLite queue system
- License system (trial + full)
- 3 default presets

---

## 🙏 Credits

- **Inspired by**: Intisari AutoCut (intisariapps.com)
- **Parser**: FSM pattern adopted from `gemini_parser.js`
- **Queue**: Wide-Pipe protocol concept from Intisari
- **Tools**: yt-dlp, FFmpeg, SQLite

---

## 🔒 License

**Commercial License Required**

This software is proprietary. Unauthorized copying, distribution, or use is strictly prohibited.

See [LICENSE](LICENSE) file for details.

**Personal Use**: 1 license = 1 device
**Commercial Use**: Contact for enterprise licensing