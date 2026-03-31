# PTV-Tracker-APP Documentation

## Overview
PTV-Tracker-APP is a **Telegram bot only** application for tracking Victorian public transport (PTV) services. No website or web interface.

## Architecture

### Core Components
- **Telegram Bot**: Python bot running on Raspberry Pi using polling mode
- **PTV API Integration**: Fetches real-time transport data
- **Tracking System**: Core functionality for monitoring departures and routes

### Technology Stack
- **Backend**: Python 3.7+ with python-telegram-bot library
- **Hosting**: Raspberry Pi (home server) via polling mode
- **APIs**: Telegram Bot API, PTV Timetable API
- **Version Control**: Git/GitHub

## Features

### Telegram Bot Support
- **Polling Mode**: Bot checks Telegram servers every few seconds (no webhook needed)
- **Command Processing**: Handle /start, /status, /help, and custom commands
- **PTV API Integration**: Real-time departures, routes, and service updates
- **Secure**: API keys never leave the Raspberry Pi

## Development Guidelines

### Project Structure
```
PTV-Tracker-APP/
├── AI/                # AI-specific documentation
│   ├── README.md      # AI instructions entry point
│   ├── AI.md          # AI reading guidelines
│   ├── DOCS.md        # Technical documentation (this file)
│   ├── SPECS.md       # Requirements and specifications
│   ├── SECURITY.md    # Security specifications
│   ├── TELEGRAM.md    # Bot specifications
│   ├── DEBUG.md       # Debugging guide
│   └── LOGS.md        # Activity logs
├── HOSTING.md         # Raspberry Pi hosting guide
├── bot.py             # Main bot script (create this)
├── requirements.txt   # Python dependencies
└── .env               # API keys (never commit)
```

### Code Organization
- Bot code lives in `bot.py` (create this file)
- Configuration via `.env` file (not in git)
- Dependencies managed in `requirements.txt`
- See `HOSTING.md` for Raspberry Pi setup instructions

## Deployment

### Telegram Bot
- Runs on Raspberry Pi at home
- **Polling mode** - no domain, no webhook, no port forwarding needed
- Auto-starts via systemd service
- See `HOSTING.md` for complete setup instructions

### GitHub Repository
- Code storage and version control
- Documentation (AI/ folder)
- No website hosting (GitHub Pages not used)

## Maintenance

### Regular Updates
- Keep Python dependencies current: `pip install -r requirements.txt --upgrade`
- Monitor Telegram API changes (python-telegram-bot updates)
- Update documentation as features evolve
- Review `HOSTS.md` for Pi maintenance tips

### Monitoring
- Track bot performance via `sudo journalctl -u ptv-bot -f`
- Monitor PTV API availability
- Log user interactions and errors (see DEBUG.md)
