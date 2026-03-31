# PTV-Tracker-APP Specifications

## Requirements

### Functional Requirements

#### FR1: Telegram Bot Core
- **FR1.1**: Bot runs on Raspberry Pi using polling mode (no webhook needed)
- **FR1.2**: Bot responds to user commands within 2 seconds
- **FR1.3**: Bot supports PTV tracking queries and commands
- **FR1.4**: Real-time notification system for transport updates

#### FR2: Telegram Bot Commands
- **FR2.1**: `/start` - Initialize bot and display welcome message
- **FR2.2**: `/help` - Show available commands and usage
- **FR2.3**: `/status <stop>` - Check departures for a specific stop
- **FR2.4**: `/routes <type>` - List train/tram/bus routes
- **FR2.5**: `/track <route>` - Add a route to track for alerts
- **FR2.6**: `/list` - Show all tracked routes

#### FR3: PTV API Integration
- **FR3.1**: Fetch real-time departure data from PTV API
- **FR3.2**: Generate HMAC-SHA1 signature for API authentication
- **FR3.3**: Respect PTV API rate limits (max requests per minute)
- **FR3.4**: Graceful error handling for API failures

#### FR4: Data Management
- **FR4.1**: Store user preferences (tracked routes, notification settings)
- **FR4.2**: JSON file storage on Raspberry Pi (simple, no database needed)
- **FR4.3**: Data retention policy (auto-delete old data)
- **FR4.4**: User data export on request

### Non-Functional Requirements

#### Performance
- **NFR1**: Bot response time < 2 seconds for commands
- **NFR2**: PTV API fetch < 5 seconds (including signature generation)
- **NFR3**: Support 50+ concurrent users
- **NFR4**: Polling interval: check Telegram every 1-2 seconds

#### Security
- **NFR5**: Bot token stored in environment variables only
- **NFR6**: PTV API credentials never exposed in code or logs
- **NFR7**: Rate limiting for bot commands (prevent spam)
- **NFR8**: Input validation on all user commands
*See [SECURITY.md](SECURITY.md) for detailed security specifications*

#### Reliability
- **NFR9**: Bot runs 24/7 via systemd service
- **NFR10**: Auto-restart on crash (`Restart=always`)
- **NFR11**: Reconnect automatically after network interruption
- **NFR12**: Log all errors for debugging

#### Compatibility
- **NFR13**: Telegram API v6.0+ compatibility
- **NFR14**: Python 3.7+ support
- **NFR15**: Raspberry Pi OS (Debian-based) compatibility

## Technical Specifications

### Telegram Bot Specifications

#### Bot Commands
```
/start - Initialize bot and show help
/help - Show available commands and usage
/status <stop_id> - Check departures for a stop
/routes <type> - List routes (train/tram/bus)
/track <route_id> - Track a route for alerts
/list - Show all tracked routes
/stop <route_id> - Stop tracking a route
```

#### Bot Features
- **Natural Language Processing**: Basic command parsing with optional arguments
- **Inline Mode**: Not required (polling mode sufficient)
- **Group Support**: Work in Telegram groups with @botname commands
- **Custom Keyboards**: ReplyKeyboardMarkup for common actions
- **Error Messages**: User-friendly error descriptions

*See [TELEGRAM.md](TELEGRAM.md) for detailed telegram bot specifications*

### PTV API Integration

#### API Client Requirements
- **Language**: Python with `requests` library
- **Authentication**: HMAC-SHA1 signature with DevID + API Key
- **Endpoint**: `https://timetableapi.ptv.vic.gov.au/v3/`
- **Rate Limiting**: Implement client-side rate limiting

#### Supported Endpoints
- `GET /v3/route_types` - List transport modes
- `GET /v3/routes` - List all routes
- `GET /v3/departures/route_type/{route_type}/stop/{stop_id}` - Departures
- `GET /v3/stops/route/{route_id}` - Stops on a route

#### Caching Strategy
- **Static Data**: Route list (cache 24 hours)
- **Dynamic Data**: Departures (cache 1-2 minutes)
- **No Cache**: Real-time tracking requests

### Data Management

#### Data Storage
- **Primary Storage**: JSON files on Raspberry Pi
- **Location**: `~/ptv-bot/data/`
- **User Data**: One file per Telegram user ID (`user_{id}.json`)
- **Backup**: Optional rsync to external storage

#### Data Models
```
UserData: {
  telegram_id: int,
  tracked_routes: [route_id],
  preferred_stops: [stop_id],
  notification_settings: {quiet_hours: bool},
  created_at: timestamp
}

Route: {
  id: int,
  route_name: str,
  route_type: int,  # 0=train, 1=tram, 2=bus
  route_number: str
}

Departure: {
  route_id: int,
  stop_id: int,
  direction: str,
  scheduled: timestamp,
  estimated: timestamp,
  platform: str
}
```

## Integration Requirements

### External Services
- **Telegram Bot API**: For bot functionality (polling mode)
- **PTV Timetable API**: For transport data
- **GitHub**: Repository hosting only

### Third-Party Dependencies
- **Version Control**: Git
- **Language**: Python 3.7+
- **Package Manager**: pip
- **Testing**: pytest
- **Process Manager**: systemd

## Deployment

### Raspberry Pi Setup
- **OS**: Raspberry Pi OS Lite (64-bit recommended)
- **Python**: 3.7 or higher
- **Network**: Ethernet preferred, WiFi acceptable
- **Power**: Official Raspberry Pi PSU
- **Storage**: 16GB+ microSD card

### Service Configuration
- **Service Name**: `ptv-bot`
- **User**: `pi`
- **Auto-start**: Enabled
- **Restart Policy**: `always` with 10-second delay
- **Logging**: systemd journal

## Compliance and Legal

### Data Protection
- **GDPR Compliance**: Minimal data collection, user deletion on request
- **Privacy Policy**: State what data is stored (Telegram ID, preferences only)
- **Data Portability**: Export via `/export` command

### Licensing
- **Open Source**: MIT License recommended
- **Dependencies**: python-telegram-bot (LGPL), requests (Apache 2.0)
- **Attribution**: Credit to PTV for transport data

## Testing Requirements

### Test Coverage
- **Unit Tests**: > 70% coverage for command handlers
- **Integration Tests**: PTV API integration with mocked responses
- **End-to-End Tests**: Telegram bot flow testing (manual)
- **Performance Tests**: API response time monitoring

### Quality Assurance
- **Code Review**: Peer review for all changes
- **Pre-commit Hooks**: Prevent secret commits
- **Security Checks**: `bandit` for Python security linting
- **Manual Testing**: Test all commands before deployment
