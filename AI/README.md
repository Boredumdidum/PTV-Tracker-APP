# AI Instructions for PTV-Tracker-APP

Before working on this project, **always** read all documentation in this `/AI` folder first.

## Required Reading Order

1. **README.md** (this file) - Overview and navigation
2. **SPECS.md** - Technical requirements and specifications
3. **SECURITY.md** - Security constraints and best practices
4. **TELEGRAM.md** - Telegram bot specifications
5. **DOCS.md** - Architecture and development guidelines
6. **DEBUG.md** - Debugging guide
7. **../HOSTING.md** - Raspberry Pi hosting setup (in root directory)

## Project Context

- **Name**: PTV-Tracker-APP
- **Purpose**: Telegram bot for tracking Victorian public transport (PTV)
- **API**: Victorian Public Transport API integration
- **Hosting**: Raspberry Pi at home (polling mode)
- **Components**:
  - Telegram bot (Python, python-telegram-bot)
  - PTV API data fetching
  - No website - bot only interface

## Quick Navigation

| File | Purpose |
|------|---------|
| `SPECS.md` | Functional/non-functional requirements |
| `SECURITY.md` | Security specifications (SEC1-SEC20) |
| `TELEGRAM.md` | Bot commands, API integration, caching |
| `DEBUG.md` | Debugging and troubleshooting guide |
| `DOCS.md` | Architecture overview, deployment |
| `../HOSTING.md` | Raspberry Pi setup instructions (root dir) |

## Important Constraints

- **Telegram bot only** - No website, no web interface
- Raspberry Pi hosting (polling mode, no domain needed)
- PTV API rate limits must be respected
- API keys stored securely on Pi only (never exposed)
- See SECURITY.md for all security requirements
- See HOSTING.md for deployment instructions