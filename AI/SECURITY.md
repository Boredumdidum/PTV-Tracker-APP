# PTV-Tracker-APP Security Specifications

## Security Requirements

### Telegram Bot Security
- **SEC1**: Secure bot token storage (`.env` file, never commit)
- **SEC2**: Bot token rotation capability (regenerate via @BotFather if leaked)
- **SEC3**: Command authorization checks (validate user permissions)
- **SEC4**: Prevent bot command injection attacks (input sanitization)
- **SEC5**: PTV API key protection (stored only on Raspberry Pi)

### Data Protection
- **SEC6**: PTV API credentials stored in environment variables only
- **SEC7**: No hardcoded secrets in source code
- **SEC8**: `.env` file excluded from git (add to `.gitignore`)
- **SEC9**: File permissions on `.env` (chmod 600)

### Raspberry Pi Security
- **SEC10**: Minimal open ports (no inbound connections needed for polling mode)
- **SEC11**: Regular system updates (`sudo apt update && sudo apt upgrade`)
- **SEC12**: Firewall configuration (UFW optional for defense in depth)
- **SEC13**: Secure physical access to the Pi

### API Security
- **SEC14**: PTV API rate limiting compliance (respect API limits)
- **SEC15**: Request timeout handling (prevent hanging connections)
- **SEC16**: Error message sanitization (don't leak internal details to users)

### Infrastructure Security
- **SEC17**: GitHub repository security (private or public with no secrets)
- **SEC18**: Dependency vulnerability scanning (`pip-audit` or similar)
- **SEC19**: Secure deployment practices (SSH keys for git, not passwords)
- **SEC20**: Logging and monitoring for security events

## Compliance

### Data Privacy
- **GDPR Compliance**: User consent, data minimization, right to deletion
- **Privacy Policy**: Clear data usage and storage policies
- **Data Portability**: User data export capabilities
- **Bot Data**: Only store Telegram user ID, no personal information

### Legal Requirements
- **Terms of Service**: Clear user agreements and liability disclaimers
- **API Terms**: Compliance with Telegram Bot API terms
- **PTV API Terms**: Compliance with Victorian Public Transport API terms
- **Open Source Licensing**: MIT license (add LICENSE file)

## Security Best Practices

### Development
- **Code Review**: Security-focused peer reviews
- **Secret Scanning**: Pre-commit hooks to prevent secret commits
- **Dependency Management**: Regular updates (`pip install --upgrade`)
- **Secure Coding**: No SQL injection, command injection vulnerabilities

### Operations
- **Access Control**: SSH key-based access to Pi, disable password auth
- **Backup Security**: Encrypted backups of user preferences
- **Incident Response**: Documented procedures for token compromise
- **Monitoring**: systemd service logs (`journalctl -u ptv-bot -f`)

## Threat Model

### Potential Threats
- **Bot Token Leak**: If `.env` is accidentally committed
- **Pi Compromise**: Physical or network access to the device
- **API Abuse**: Excessive PTV API usage draining quota
- **Supply Chain**: Vulnerabilities in python-telegram-bot or requests libraries

### Mitigation Strategies
- **Defense in Depth**: Multiple security layers (file permissions, gitignore, env vars)
- **Zero Trust**: Verify all API responses, don't trust input
- **Regular Audits**: Check for secret leaks in git history
- **Incident Planning**: Token rotation procedure documented

## Emergency Procedures

### If Bot Token is Leaked
1. Immediately message @BotFather
2. Use `/revoke` to invalidate the leaked token
3. Generate new token with `/token`
4. Update `.env` file on Pi
5. Restart bot service: `sudo systemctl restart ptv-bot`

### If PTV API Key is Compromised
1. Contact PTV support to revoke the key
2. Generate new DevID + API Key pair
3. Update `.env` file
4. Restart bot service
