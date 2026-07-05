# 🎬 AUTOCUT TERMUX

**AI-Powered Video Clipper untuk Termux - No License, No Expiry, Full Access**

Automatically cut viral clips from videos using AI analysis. Download from YouTube/TikTok/Instagram, parse AI output (Gemini/Claude/ChatGPT), and auto-cut into shareable clips.

---

## ✨ Features

- 📥 **Multi-platform Download** - YouTube, TikTok, Instagram, Twitter, Facebook
- 🤖 **AI Parser** - Parse output dari Gemini, Claude, ChatGPT dengan FSM parser
- ✂️ **Auto-Cut** - Cut video berdasarkan timestamp dari AI
- 📊 **Queue System** - Batch processing dengan SQLite queue (resume capability)
- 🎨 **Preset System** - Custom presets untuk consistent style (zoom, fps, effects)
- 📱 **Termux Native** - Jalan di Android tanpa PC
- 🔓 **Open Source** - No license, no expiry, no activation

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
git clone https://github.com/YOUR_USERNAME/autocut-termux.git
cd autocut-termux

# Run
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
```

### Main Menu

```
╔═══════════════════════════════════════════════════════════╗
║     🎬 AUTOCUT TERMUX v1.0.0 - Viral Clip Generator     ║
║     No License • No Expiry • Full Access                  ║
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
  7. ℹ️  About / Help
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
├── autocut.py              # Main CLI
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
| License | Closed (.deb check) | **None (open)** |
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

**MIT License** - Free to use, modify, distribute. No warranty.

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

- **GitHub Issues**: [Create issue](https://github.com/YOUR_USERNAME/autocut-termux/issues)
- **Documentation**: See `README.md`
- **Version**: 1.0.0