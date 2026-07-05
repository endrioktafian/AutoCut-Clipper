#!/bin/bash
# =========================================================
# SETUP GITHUB PUSH - AutoCut Termux
# Script untuk prepare dan push ke GitHub
# =========================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}     🚀 GITHUB PUSH SETUP - AutoCut Termux            ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}[!] Git not found. Installing...${NC}"
    apt-get update && apt-get install -y git
fi

# Step 2: Initialize git repo
echo -e "${BLUE}[*] Initializing git repository...${NC}"
cd /root/autocut-termux

if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}[✓] Git initialized${NC}"
else
    echo -e "${YELLOW}[!] Git already initialized${NC}"
fi

# Step 3: Create .gitignore
echo -e "${BLUE}[*] Creating .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# AutoCut
output/
temp/
logs/
*.db
*.sqlite
*.sqlite3

# License & Secrets
.autocut_license
*.key
*.pem
.env
config.local.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Test files
test_*.py
*_test.py
EOF
echo -e "${GREEN}[✓] .gitignore created${NC}"

# Step 4: Copy GitHub-specific files
echo -e "${BLUE}[*] Preparing GitHub-specific files...${NC}"

# Copy README_GITHUB.md to README.md (for GitHub version)
cp README_GITHUB.md README.md
echo -e "${GREEN}[✓] README.md updated (GitHub version)${NC}"

# Create LICENSE file (proprietary)
cat > LICENSE << 'EOF'
# PROPRIETARY LICENSE

Copyright (c) 2026 AutoCut Termux. All rights reserved.

## TERMS OF USE

This software is proprietary and protected by copyright law.

### Personal Use License
- 1 license = 1 device
- Valid for 1 year from activation
- Non-transferable
- No redistribution allowed

### Commercial Use
- Contact for enterprise licensing
- Multi-device discounts available

### Prohibited Activities
- Reverse engineering
- Decompilation
- Redistribution
- Reselling without authorization
- Sharing license keys

### Trial License
- 7-day free trial
- Full feature access
- Must purchase for continued use

### Violations
Violations will result in license termination and potential legal action.

## CONTACT

For licensing inquiries:
- Email: support@yourdomain.com
- Website: https://yourdomain.com

## NO WARRANTY

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
EOF
echo -e "${GREEN}[✓] LICENSE file created${NC}"

# Step 5: Update config.json (remove sensitive data)
echo -e "${BLUE}[*] Sanitizing config.json...${NC}"
cat > config.json << 'EOF'
{
  "output_dir": "./output",
  "temp_dir": "./temp",
  "default_preset": "default",
  "fast_cut": true,
  "auto_cleanup": true,
  "max_temp_files": 10,
  "telegram_bot_token": "",
  "telegram_chat_id": "",
  "notify_on_complete": false,
  "license_mode": "public"
}
EOF
echo -e "${GREEN}[✓] config.json sanitized${NC}"

# Step 6: Git add & commit
echo -e "${BLUE}[*] Adding files to git...${NC}"
git add .
echo -e "${GREEN}[✓] Files added${NC}"

echo -e "${BLUE}[*] Creating initial commit...${NC}"
git commit -m "Initial commit: AutoCut Termux v1.0.0 (GitHub Version with License)

Features:
- AI-powered video clipper (parse Gemini/Claude output)
- Multi-platform download (YouTube, TikTok, Instagram)
- Auto-cut with FFmpeg
- Queue system (SQLite)
- Preset system (JSON)
- License protection (device-bound, 7-day trial, 1-year full)

Files:
- autocut_github.py: Main CLI with license check
- license_manager.py: License validation (offline)
- license_server.py: Flask API server (optional)
- parser.py: FSM-based AI parser
- downloader.py: yt-dlp wrapper
- cutter.py: FFmpeg wrapper
- queue_manager.py: SQLite queue

License: Proprietary (see LICENSE file)
Trial: 7 days gratis
Full: Rp 99.000 / tahun"
echo -e "${GREEN}[✓] Commit created${NC}"

# Step 7: Get GitHub repo URL from user
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 GITHUB REPO URL${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Masukkan GitHub repository URL:"
echo "  Format: https://github.com/YOUR_USERNAME/autocut-termux.git"
echo ""
echo -e "${YELLOW}Catatan:${NC}"
echo "  - Buat repo dulu di GitHub (public atau private)"
echo "  - JANGAN centang 'Add README' (biar clean)"
echo "  - Copy URL dari halaman repo"
echo ""
read -p "GitHub URL: " GITHUB_URL

if [ -z "$GITHUB_URL" ]; then
    echo -e "${RED}❌ URL kosong! Aborting.${NC}"
    exit 1
fi

echo -e "${BLUE}[*] Connecting to GitHub remote...${NC}"

# Remove existing remote if any
git remote remove origin 2>/dev/null || true

# Add remote
git remote add origin "$GITHUB_URL"
echo -e "${GREEN}[✓] Remote added: $GITHUB_URL${NC}"

# Step 8: Push to GitHub
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🚀 PUSH TO GITHUB${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Ready to push to:${NC} $GITHUB_URL"
echo ""
echo "First time push akan minta GitHub credentials:"
echo "  - Username: GitHub username lo"
echo "  - Password: PERSONAL ACCESS TOKEN (bukan password biasa)"
echo ""
echo "Cara dapetin PAT:"
echo "  1. Buka https://github.com/settings/tokens"
echo "  2. Generate new token (classic)"
echo "  3. Centang 'repo' scope"
echo "  4. Copy token (simpen baik-baik, cuma muncul sekali)"
echo ""
read -p "Press Enter to continue..."

# Rename branch to main
git branch -M main 2>/dev/null || true

# Push
echo -e "${BLUE}[*] Pushing to GitHub...${NC}"
git push -u origin main

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}     ✅ PUSH SUCCESSFUL!                               ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Repo URL: ${GREEN}$GITHUB_URL${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Buka repo di browser"
    echo "  2. Verify semua file ter-upload"
    echo "  3. Update README dengan link website/payment lo"
    echo "  4. Share ke publik!"
    echo ""
else
    echo -e "${RED}❌ Push failed!${NC}"
    echo ""
    echo "Kemungkinan penyebab:"
    echo "  - GitHub credentials salah"
    echo "  - Repo URL invalid"
    echo "  - Network issue"
    echo ""
    echo "Coba lagi dengan:"
    echo "  git push -u origin main"
    echo ""
    exit 1
fi

echo -e "${BLUE}[*] Done!${NC}"