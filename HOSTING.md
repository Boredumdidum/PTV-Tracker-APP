# Hosting Guide - PTV-Tracker-APP

This guide covers setting up Cloudflare Tunnel for secure hosting without port forwarding.

## Why Cloudflare Tunnel?

- **No port forwarding** - Keeps your home network secure
- **Automatic HTTPS** - SSL certificate handled automatically
- **DDoS protection** - Cloudflare's network protection
- **Static URL** - No dynamic DNS needed
- **Free** - Zero cost for personal use

---

## Prerequisites

- Raspberry Pi (3B+ or 4 recommended) with Raspberry Pi OS
- Domain name (or use Cloudflare's free subdomains)
- Cloudflare account (free tier works fine)

---

## Step 1: Install cloudflared

On your Raspberry Pi:

```bash
# Download and install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb

# For Pi 3 or earlier (32-bit), use:
# curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm.deb

sudo dpkg -i cloudflared.deb
```

---

## Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will:
1. Print a URL to visit in your browser
2. Open the Cloudflare dashboard
3. Select which domain to use
4. Download a certificate to your Pi (`~/.cloudflared/cert.pem`)

---

## Step 3: Create Your Tunnel

```bash
# Create the tunnel (name it anything)
cloudflared tunnel create ptv-tracker

# Note the Tunnel ID output - you'll need it
# Example: 12345abc-6789-0def-ghij-klmnopqrstuv
```

---

## Step 4: Configure the Tunnel

Create config file:

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

Add this content (replace `YOUR_TUNNEL_ID` and `your-domain.com`):

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/pi/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  # Telegram bot webhook endpoint
  - hostname: bot.your-domain.com
    service: http://localhost:5000
  
  # PTV API proxy endpoint
  - hostname: api.your-domain.com
    service: http://localhost:5000
  
  # Default/fallback
  - service: http_status:404
```

---

## Step 5: Set Up DNS Records

```bash
# Route traffic to your tunnel
cloudflared tunnel route dns ptv-tracker bot.your-domain.com
cloudflared tunnel route dns ptv-tracker api.your-domain.com
```

Or manually in Cloudflare dashboard:
1. Go to DNS settings
2. Add CNAME record: `bot` → `YOUR_TUNNEL_ID.cfargotunnel.com`
3. Add CNAME record: `api` → `YOUR_TUNNEL_ID.cfargotunnel.com`

---

## Step 6: Run as a Service

```bash
# Install as system service
sudo cloudflared service install

# Start the service
sudo systemctl start cloudflared

# Enable auto-start on boot
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## Step 7: Test Your Setup

```bash
# Check tunnel is running
cloudflared tunnel info ptv-tracker

# Test connectivity
curl https://api.your-domain.com/health
```

---

## Backend Application Setup

Your Flask/FastAPI app should listen on `localhost:5000`:

```python
# app.py - Minimal example
from flask import Flask, jsonify
import requests
import hmac
import hashlib
import os

app = Flask(__name__)

PTV_DEV_ID = os.environ['PTV_DEV_ID']
PTV_API_KEY = os.environ['PTV_API_KEY']

def generate_signature(path):
    import time
    timestamp = str(int(time.time()))
    raw = f'{path}?devid={PTV_DEV_ID}&timestamp={timestamp}'
    signature = hmac.new(
        PTV_API_KEY.encode(),
        raw.encode(),
        hashlib.sha1
    ).hexdigest()
    return f'https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}'

@app.route('/ptv/<path:endpoint>')
def proxy_ptv(endpoint):
    url = generate_signature(f'/{endpoint}')
    response = requests.get(url, timeout=10)
    return jsonify(response.json())

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Run with:
```bash
export PTV_DEV_ID=your_dev_id
export PTV_API_KEY=your_api_key
python3 app.py
```

---

## Telegram Bot Webhook Configuration

Once tunnel is running, set your webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://bot.your-domain.com/webhook"}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tunnel won't start | Check `sudo systemctl status cloudflared` for errors |
| DNS not resolving | Wait 5-10 minutes for propagation, check Cloudflare DNS tab |
| 502 errors | Ensure backend app is running on localhost:5000 |
| Certificate errors | Run `cloudflared tunnel login` again |

---

## Security Notes

- Keep `~/.cloudflared/*.json` files private (they contain tunnel credentials)
- Never commit these files to git
- Use environment variables for API keys
- Consider adding firewall rules on Pi: `sudo ufw allow from 127.0.0.1 to any port 5000`

---

## Updating cloudflared

```bash
# Check current version
cloudflared --version

# Update to latest
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb
sudo systemctl restart cloudflared
```
