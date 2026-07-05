# 🎬 AUTOCUT TERMUX

**AI-Powered Video Clipper untuk Termux - License Required**

Automatically cut viral clips from videos using AI analysis. Download from YouTube/TikTok/Instagram, parse AI output (Gemini/Claude/ChatGPT), and auto-cut into shareable clips.

---

## ⚠️ LICENSE REQUIREMENT

**Versi ini memerlukan license key untuk berjalan.**

| License Type | Duration | Price |
|--------------|----------|-------|
| **TRIAL** | 7 hari | GRATIS |
| **FULL** | 1 tahun | Rp 99.000 |

### Cara Activate License

1. **Trial (Gratis 7 hari)**:
   - Jalankan `python autocut.py`
   - Pilih opsi `2. Gunakan trial gratis`
   - Trial key akan di-generate otomatis
   - Valid untuk 7 hari

2. **Full License**:
   - Beli di: **[LINK WEBSITE LO]** *(coming soon)*
   - Lo bakal dapet license key
   - Jalankan `python autocut.py`
   - Pilih opsi `1. Masukkan license key`
   - Paste key yang lo dapet

3. **Check License Status**:
   ```bash
   python license_manager.py status
   ```

---

## ✨ Features

- 📥 **Multi-platform Download** - YouTube, TikTok, Instagram, Twitter, Facebook
- 🤖 **AI Parser** - Parse output dari Gemini, Claude, ChatGPT dengan FSM parser
- ✂️ **Auto-Cut** - Cut video berdasarkan timestamp dari AI
- 📊 **Queue System** - Batch processing dengan SQLite queue (resume capability)
- 🎨 **Preset System** - Custom presets untuk consistent style (zoom, fps, effects)
- 📱 **Termux Native** - Jalan di Android tanpa PC
- 🔐 **License Protected** - 1 license = 1 device (trial 7 hari tersedia)

---

## 📦 Installation

### One-Command Install

```bash
pkg update -y && pkg install wget -y && wget -O install.sh https://raw.githubusercontent.com/YOUR_REPO/main/install.sh && bash install.sh
```

### Manual Install

```bash
# Install dependencies
pkg update -y
pkg install python ffmpeg git wget curl

# Install Python packages
pip install yt-dlp

# Clone repository
git clone https://github.com/endrioktafian/AutoCut-Clipper.git
cd autocut-termux

# Run (akan minta license activation)
python autocut.py
```

---

## 🚀 Usage

### Quick Start

```bash
# After installation, restart Termux then:
autocut

# Or run directly:
cd ~/autocut-termux && python autocut.py

# First run akan meminta license activation
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

KLIP [2]:
...
```

### Example AI Output

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
Judul: Cara Trading Crypto Pemula

KLIP [1]:
00:00 - 00:30 | Intro yang menarik
Hook: "Tahu gak sih 90% trader crypto rugi di tahun pertama?"
Caption: #trading #crypto #bitcoin #tutorial

KLIP [2]:
01:15 - 02:00 | Tips penting memilih exchange
Hook: "3 exchange ini paling aman untuk pemula!"
Caption: Pilih exchange yang sudah teregulasi Bappebti

KLIP [3]:
03:45 - 04:30 | Cara setting stop loss
Hook: "Stop loss wrong = auto cuan!"
```

---

## 🎨 Presets

Preset tersedia di `presets/` folder:

| Preset | Description |
|--------|-------------|
| `default` | Fast cut, no effects |
| `viral_style` | Zoom 1.15x, brightness +, contrast +, for TikTok/Reels |
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
├── autocut.py              # Main CLI (WITH LICENSE CHECK)
├── license_manager.py      # License validation & activation
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

## 🔧 Architecture

Adopted from **Intisari AutoCut** pattern dengan improvement:

| Component | Intisari | AutoCut Termux |
|-----------|----------|----------------|
| Parser | JavaScript (Chrome Extension) | Python (FSM Parser) |
| Downloader | PC Backend (.deb) | yt-dlp (native) |
| Cutter | FFmpeg (PC) | FFmpeg (Termux) |
| Queue | WebSocket + Polling | SQLite (local) |
| License | Closed (.deb check) | **License-activated** |
| Platform | PC + Chrome | **Termux only** |

### FSM Parser States

```
IDLE → META → HOOKS → SEO → TIMESTAMP → HALT
```

Parser extract:
- URL video
- Title
- Clips (start, end, title, hook, caption)
- Viral score & reason

---

## 🛠️ Development

### Run Tests

```bash
# Test parser
python parser.py

# Test downloader
python downloader.py

# Test cutter
python cutter.py

# Test queue manager
python queue_manager.py
```

### Add New Features

1. **New preset**: Tambah file JSON di `presets/`
2. **New downloader**: Extend `VideoDownloader` class
3. **New effects**: Extend `VideoCutter._apply_preset_to_cmd()`
4. **New parser pattern**: Add regex di `AIParser.__init__()`

---

## 📝 License

**Commercial License - Personal Use Only**

- 1 license = 1 device
- Trial 7 hari tersedia (gratis)
- Full license valid 1 tahun

See [LICENSE](LICENSE) file for details.

---

## 💳 Pricing

| Plan | Price | Duration | Features |
|------|-------|----------|----------|
| **TRIAL** | FREE | 7 days | All features, 1 device |
| **FULL** | Rp 99.000 | 1 year | All features, 1 device, priority support |

**Contact**: [DM for purchase](https://t.me/YOUR_USERNAME)

---

## 🙏 Credits

- **Inspired by**: Intisari AutoCut (intisariapps.com)
- **Parser**: FSM pattern adopted from `gemini_parser.js`
- **Queue**: Wide-Pipe protocol concept from Intisari
- **Tools**: yt-dlp, FFmpeg, SQLite

---

## ⚠️ Disclaimer

This tool is for **personal/educational use only**. Respect copyright and terms of service of video platforms. The authors are not responsible for misuse.

---

## 📞 Support

- **GitHub Issues**: [Create issue](https://github.com/endrioktafian/AutoCut-Clipper/issues)
- **Documentation**: See `README.md`
- **Version**: 1.0.0-GITHUB