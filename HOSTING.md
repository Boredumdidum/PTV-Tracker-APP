# Hosting Guide - PTV-Tracker-APP (Telegram Bot Only)

This guide covers hosting the Telegram bot on your Raspberry Pi using **polling mode** (no web server, no domain, no Cloudflare required).

## Why Polling Mode?

- **No domain needed** - Bot checks Telegram servers for messages
- **No port forwarding** - Outbound connections only (more secure)
- **No HTTPS/TLS setup** - No certificates needed
- **Works behind any router** - No network configuration
- **Simpler deployment** - Just run the Python script

---

## Prerequisites

- Raspberry Pi (3B+ or 4 recommended) with Raspberry Pi OS
- Python 3.7+
- Telegram Bot Token (from @BotFather)
- PTV API credentials (DevID + API Key)
- Stable internet connection

---

## Architecture

```
Raspberry Pi (Your Home)
    ↓
[Bot Script Running 24/7]
    ↓ (outbound HTTPS request every few seconds)
Telegram API (api.telegram.org)
    ↑
[Users send messages]
Telegram App
```

The bot asks Telegram "any new messages?" every few seconds instead of Telegram pushing messages to you.

---

## Step 0: Create Your User Account (Recommended)

Instead of using the default `pi` user, create your own username for better security.

### Create a New User
```bash
# Create new user (replace 'yourname' with your desired username)
sudo adduser yourname

# You'll be prompted to:
# - Set a password
# - Enter full name (optional)
# - Enter room number, work phone, home phone, other (all optional)
# - Confirm information
```

### Add User to Sudo Group
```bash
# Grant sudo privileges
sudo usermod -aG sudo yourname
```

### Switch to New User
```bash
# Switch to your new account
su - yourname

# Verify sudo works
sudo whoami
# Should output: root
```

### Optional: Disable Default 'pi' User (Security)
```bash
# After confirming your new user works with sudo, disable pi user:
sudo passwd -l pi

# Or delete entirely (only if your new user works properly):
sudo deluser pi
```

### Update the Service File (Important!)

When you create your own user, update the systemd service file in Step 6:
- Change `User=pi` to `User=yourname`
- Change all `/home/pi/` paths to `/home/yourname/`

---

## Step 1: Prepare Your Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Create project directory
mkdir -p ~/ptv-bot
cd ~/ptv-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

---

## Step 2: Install Dependencies

```bash
pip install python-telegram-bot requests
```

---

## Step 3: Get the Bot Code

Download `bot.py` from this repository to your Pi:

```bash
# If using git (recommended)
git clone https://github.com/YOUR_USERNAME/PTV-Tracker-APP.git
cd PTV-Tracker-APP

# Copy bot.py to your bot directory
cp bot.py ~/ptv-bot/
cd ~/ptv-bot
```

Or manually copy `bot.py` content to a file:

```bash
nano bot.py
# Paste the contents of bot.py from the repository
# Save: Ctrl+O, Enter, Ctrl+X
```

---

## Step 4: Environment Setup

Create `.env` file:

```bash
cat > ~/ptv-bot/.env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
PTV_DEV_ID=your_ptv_dev_id
PTV_API_KEY=your_ptv_api_key
EOF
```

**Never commit this file to git!**

Add to `.gitignore`:
```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
```

---

## Step 5: Test the Bot

```bash
# Load environment and run
export $(cat .env | xargs)
python3 bot.py
```

You should see:
```
2026-03-31 10:00:00 - telegram.ext.Application - INFO - Application started
2026-03-31 10:00:00 - __main__ - INFO - Starting bot in polling mode...
```

In Telegram, message your bot `/start` - it should respond!

**Stop with Ctrl+C when done testing.**

---

## Step 6: Run as a Service (Auto-start)

Create a systemd service to run the bot 24/7:

```bash
sudo nano /etc/systemd/system/ptv-bot.service
```

Add:

```ini
[Unit]
Description=PTV Tracker Telegram Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ptv-bot
EnvironmentFile=/home/pi/ptv-bot/.env
ExecStart=/home/pi/ptv-bot/venv/bin/python /home/pi/ptv-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable ptv-bot

# Start the service
sudo systemctl start ptv-bot

# Check status
sudo systemctl status ptv-bot
```

---

## Step 7: Monitoring & Logs

### View Bot Logs
```bash
# Real-time logs
sudo journalctl -u ptv-bot -f

# Last 50 entries
sudo journalctl -u ptv-bot -n 50

# Since last boot
sudo journalctl -u ptv-bot --since today
```

### Check if Running
```bash
sudo systemctl is-active ptv-bot
```

### Restart Bot
```bash
sudo systemctl restart ptv-bot
```

### Stop Bot
```bash
sudo systemctl stop ptv-bot
```

---

## Updating the Bot

When you make changes to `bot.py`:

```bash
cd ~/ptv-bot

# Pull updates (if using git)
git pull

# Or edit bot.py directly
nano bot.py

# Restart to apply changes
sudo systemctl restart ptv-bot

# Check for errors
sudo journalctl -u ptv-bot -f
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check `sudo journalctl -u ptv-bot -f` for errors |
| "Unauthorized" error | Verify `TELEGRAM_BOT_TOKEN` is correct |
| PTV API errors | Check DevID and API key; verify signature generation |
| Service won't start | Check `.env` file exists and has correct permissions |
| Bot stops randomly | Check `Restart=always` is set in service file |

---

## Security Notes

- Keep `.env` file private (chmod 600)
- Don't share your bot token
- PTV API key stays on your Pi (never exposed)
- Bot only makes outbound connections (no open ports)

---

## Power Considerations

The Pi must stay powered and connected:
- Use a reliable power supply (official Raspberry Pi PSU recommended)
- Connect via Ethernet if possible (more stable than WiFi)
- Consider a UPS for power outages
- The bot will reconnect automatically after network interruptions
