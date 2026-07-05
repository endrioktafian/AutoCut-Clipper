#!/bin/bash
# =========================================================
# AUTOCUT TERMUX - AUTO INSTALLER
# One-command install untuk AutoCut Termux
# No license, no expiry, full access
# =========================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}     🎬 AUTOCUT TERMUX - Auto Installer                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}     No License • No Expiry • Full Access              ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running in Termux
if [ ! -d "$PREFIX" ]; then
    echo -e "${YELLOW}⚠️  Warning: Not running in Termux environment${NC}"
    echo "This script is designed for Termux on Android."
    echo "Continue anyway? [y/n]"
    read -r CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "Aborted."
        exit 1
    fi
fi

# Request storage permission
if [ ! -d "$HOME/storage" ]; then
    echo -e "${YELLOW}[*] Requesting storage permission...${NC}"
    echo -e "${YELLOW}[!] Please ALLOW storage access when prompted${NC}"
    termux-setup-storage 2>/dev/null || true
    sleep 2
fi

# Update packages
echo -e "${BLUE}[*] Updating packages...${NC}"
pkg update -y || pkg upgrade -y

# Install dependencies
echo -e "${BLUE}[*] Installing dependencies...${NC}"
pkg install -y python ffmpeg git wget curl

# Install Python packages
echo -e "${BLUE}[*] Installing Python packages...${NC}"
pip install --upgrade pip
pip install yt-dlp

# Clone or update repository
INSTALL_DIR="$HOME/autocut-termux"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[*] AutoCut already exists. Updating...${NC}"
    cd "$INSTALL_DIR"
    git pull origin main 2>/dev/null || true
else
    echo -e "${BLUE}[*] Cloning AutoCut repository...${NC}"
    # For now, create local copy since no repo yet
    echo "Repository not available yet. Using local setup."
fi

# Create directories if not exist
mkdir -p "$INSTALL_DIR"/{presets,output,temp,logs}

# Setup auto-run alias
echo -e "${BLUE}[*] Setting up auto-run alias...${NC}"

# Backup .bashrc if exists
if [ -f "$HOME/.bashrc" ]; then
    cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
fi

# Add alias if not exists
if ! grep -q "alias autocut=" "$HOME/.bashrc" 2>/dev/null; then
    echo "" >> "$HOME/.bashrc"
    echo "# AutoCut Termux alias" >> "$HOME/.bashrc"
    echo "alias autocut='cd $INSTALL_DIR && python autocut.py'" >> "$HOME/.bashrc"
    echo -e "${GREEN}[✓] Alias added to .bashrc${NC}"
else
    echo -e "${YELLOW}[!] Alias already exists${NC}"
fi

# Create wrapper script
cat > "$INSTALL_DIR/run.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python autocut.py "$@"
EOF
chmod +x "$INSTALL_DIR/run.sh"

# Final setup
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}     ✅ INSTALLATION COMPLETE!                         ${GREEN}║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📁 Installation directory:${NC} $INSTALL_DIR"
echo -e "${BLUE}🎬 To start AutoCut:${NC}"
echo ""
echo -e "  ${GREEN}Option 1:${NC} Restart Termux and type: ${YELLOW}autocut${NC}"
echo -e "  ${GREEN}Option 2:${NC} Run directly: ${YELLOW}cd $INSTALL_DIR && python autocut.py${NC}"
echo -e "  ${GREEN}Option 3:${NC} Run script: ${YELLOW}$INSTALL_DIR/run.sh${NC}"
echo ""
echo -e "${YELLOW}📝 Note:${NC} Run 'source ~/.bashrc' to use alias immediately"
echo ""

# Ask to start now
echo -e "${BLUE}Start AutoCut now? [y/n]${NC}"
read -r START
if [ "$START" = "y" ] || [ "$START" = "Y" ]; then
    cd "$INSTALL_DIR"
    python autocut.py
fi