# ngrok Setup Guide for NesterVoiceAI

This guide explains how to set up ngrok to create a public HTTPS URL for your NesterVoiceAI bot, allowing anyone on the internet to access it.

## What is ngrok?

ngrok creates a secure tunnel from a public URL to your local development server. This allows you to:
- Share your bot with others without deploying to a server
- Test webhooks and integrations
- Demo your bot to clients
- Access your bot from mobile devices

## Quick Start

### 1. Install and Configure ngrok

```bash
cd /Users/apple/Desktop/nester\ ai\ bot\ opensource
./scripts/setup-ngrok.sh
```

This script will:
- Install ngrok (via Homebrew on macOS)
- Prompt you for your ngrok authtoken
- Configure ngrok and save the token to `.env`

### 2. Get Your ngrok Authtoken

1. Sign up for a free account at: https://dashboard.ngrok.com/signup
2. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy the authtoken when prompted by the setup script

### 3. Start Your Bot

```bash
# Terminal 1: Start the bot
export PYTHONPATH=$(pwd)
python app/main.py
```

Wait for the bot to start (you should see "Server started" messages).

### 4. Start ngrok Tunnel

```bash
# Terminal 2: Start ngrok
./scripts/start-ngrok.sh
```

You'll see output like:

```
Session Status                online
Account                       Your Name (Plan: Free)
Region                        United States (us)
Latency                       20ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd1234.ngrok-free.app -> http://localhost:7860

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

### 5. Share Your Bot URL

Your bot is now publicly accessible at the HTTPS URL shown (e.g., `https://abcd1234.ngrok-free.app`)

**Share this URL with users:**
```
https://abcd1234.ngrok-free.app
```

Users can open this URL in their browser to access your voice bot interface.

## ngrok Plans

### Free Plan
- Random URL (changes each time you restart ngrok)
- Example: `https://abcd1234.ngrok-free.app`
- Limited to 1 ngrok process
- 40 connections/minute limit
- Perfect for testing and demos

### Paid Plans ($8/month+)
- Custom static domains (e.g., `https://mybot.ngrok-free.app`)
- Higher rate limits
- Multiple simultaneous tunnels
- Custom domains

## Using Custom Domains (Paid Plans Only)

If you have a paid ngrok plan with a custom domain:

1. Add to `.env`:
```bash
NGROK_DOMAIN=mybot.ngrok-free.app
```

2. Start with custom domain:
```bash
./scripts/start-ngrok-with-domain.sh
```

## Monitoring ngrok

### Web Interface
ngrok provides a local web interface to monitor traffic:
```
http://127.0.0.1:4040
```

This shows:
- Request/response details
- Connection statistics
- Replay requests for debugging

### View Logs
ngrok logs appear in the terminal where you started it. Monitor for:
- Connection attempts
- HTTP requests
- Errors

## Troubleshooting

### "ngrok not found"
Run the setup script:
```bash
./scripts/setup-ngrok.sh
```

### "authtoken not configured"
1. Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
2. Run:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### "ERR_NGROK_108" (Session limit)
Free plan allows only 1 ngrok process. Stop any other ngrok tunnels:
```bash
pkill ngrok
./scripts/start-ngrok.sh
```

### Connection Refused
Make sure your bot is running first:
```bash
# Check if bot is running
curl http://localhost:7860/health
```

### Slow Response Times
- Free ngrok tunnels can add 50-200ms latency
- Use the closest region (default: US)
- Consider upgrading to paid plan for better performance

## Security Considerations

### ngrok Warning Banner
Free ngrok URLs show a warning banner before accessing your site. Users need to click "Visit Site" to continue. This is normal for free plans.

To remove the banner:
- Upgrade to a paid plan ($8/month)
- Or deploy to a real server (AWS Lightsail, etc.)

### Rate Limiting
Free ngrok has a 40 connections/minute limit. For production use:
- Upgrade to paid plan
- Deploy to a real server

### Exposing Your Local Machine
ngrok creates a public tunnel to your local machine. Best practices:
- Only run ngrok when actively sharing
- Stop ngrok when done (`Ctrl+C`)
- Don't share ngrok URLs in public forums
- Use authentication if available (paid plans)

## Production Deployment

ngrok is great for demos and testing, but for production:

1. **Deploy to AWS Lightsail** (see `deployment/` folder)
2. **Use Docker** (see `deployment/docker/`)
3. **Set up HTTPS with Caddy** (see `deployment/docker/docker-compose.https.yml`)

For production deployment guidance, see: [README.md](../README.md#deployment)

## Commands Reference

| Command | Description |
|---------|-------------|
| `./scripts/setup-ngrok.sh` | Install and configure ngrok |
| `./scripts/start-ngrok.sh` | Start ngrok tunnel (random URL) |
| `./scripts/start-ngrok-with-domain.sh` | Start with custom domain (paid) |
| `ngrok http 7860` | Manually start tunnel on port 7860 |
| `ngrok config add-authtoken TOKEN` | Configure authtoken |
| `pkill ngrok` | Stop all ngrok processes |

## Example Workflow

```bash
# 1. One-time setup
./scripts/setup-ngrok.sh

# 2. Start bot (Terminal 1)
export PYTHONPATH=$(pwd)
python app/main.py

# 3. Start ngrok (Terminal 2)
./scripts/start-ngrok.sh

# 4. Share URL with users
# Copy the HTTPS URL from ngrok output
# Example: https://abcd1234.ngrok-free.app

# 5. When done, stop both:
# Ctrl+C in both terminals
```

## Support

- ngrok Documentation: https://ngrok.com/docs
- ngrok Dashboard: https://dashboard.ngrok.com
- NesterVoiceAI Issues: https://github.com/nesterlabs/nestervoiceai/issues
