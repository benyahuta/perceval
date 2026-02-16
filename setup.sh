#!/bin/bash
# OpenClaw Duke - Setup & Deployment Script
# Run this on your AWS Ubuntu server

set -e

echo "=========================================="
echo "  OpenClaw Duke - Setup Script"
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Install system dependencies
echo ""
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-venv python3-pip

# Step 2: Create virtual environment
echo ""
echo "[2/6] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 3: Install Python packages
echo ""
echo "[3/6] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Create .env if it doesn't exist
echo ""
echo "[4/6] Checking configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ⚠️  Created .env from template. You MUST edit it with your API keys!"
    echo "  Run: nano .env"
else
    echo "  ✓ .env already exists"
fi

# Step 5: Create data directory
echo ""
echo "[5/6] Setting up data directory..."
mkdir -p data

# Step 6: Install systemd service
echo ""
echo "[6/6] Installing systemd service..."

# Update the service file with the actual path
sed -i "s|/home/ubuntu/openclaw-duke|$SCRIPT_DIR|g" openclaw-duke.service
sed -i "s|User=ubuntu|User=$(whoami)|g" openclaw-duke.service

sudo cp openclaw-duke.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit your .env file:"
echo "     nano $SCRIPT_DIR/.env"
echo ""
echo "  2. Set up your Telegram bot:"
echo "     a) Message @BotFather on Telegram"
echo "     b) Create a new bot: /newbot"
echo "     c) Copy the bot token to .env"
echo "     d) Message your new bot (say anything)"
echo "     e) Run: source venv/bin/activate && python notifiers/telegram_notifier.py"
echo "     f) Copy the chat ID to .env"
echo ""
echo "  3. Test the pipeline:"
echo "     source venv/bin/activate && python main.py --once"
echo ""
echo "  4. Start the service:"
echo "     sudo systemctl enable openclaw-duke"
echo "     sudo systemctl start openclaw-duke"
echo ""
echo "  5. Check status:"
echo "     sudo systemctl status openclaw-duke"
echo "     journalctl -u openclaw-duke -f"
echo ""
