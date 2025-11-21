# Edge Notifier - Real-Time Webhook Notifications

Monitors `taylor_62.db` for high-edge picks (≥65%) and sends instant notifications via Discord and/or Telegram.

## Features

✅ **Real-time monitoring** - Polls database every 10 seconds  
✅ **Dual platform support** - Discord webhooks + Telegram bot API  
✅ **Smart deduplication** - Won't send the same pick twice  
✅ **Rich formatting** - Clean, professional notification messages  
✅ **Dashboard links** - Direct links to web dashboard included  

## Configuration

Set environment variables in Replit Secrets:

### Discord Setup
1. Create a Discord webhook in your server:
   - Go to Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL
2. Add to Replit Secrets:
   - Key: `DISCORD_WEBHOOK_URL`
   - Value: `https://discord.com/api/webhooks/...`

### Telegram Setup
1. Create a Telegram bot:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token
2. Get your chat ID:
   - Message [@userinfobot](https://t.me/userinfobot)
   - Copy your chat ID
3. Add to Replit Secrets:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Key: `TELEGRAM_CHAT_ID`
   - Value: `123456789`

## Message Format

```
🔥 EDGE DETECTED: 68.2%

Game: Lakers @ Warriors
Pick: Warriors -5.5

TUSG%: Warriors 52.3 vs Lakers 48.1
PVR: Warriors 12.4 vs Lakers 9.8

https://your-repl.repl.co
```

## Running

The notifier runs automatically as a background workflow. You can see it in the "Edge Notifier" workflow tab.

To run manually:
```bash
python notifications/edge_notifier.py
```

## How It Works

1. **Polls database** every 10 seconds for new picks with edge ≥65%
2. **Checks deduplication** using a hash of game+pick+edge
3. **Formats message** with all metrics and dashboard link
4. **Sends to Discord/Telegram** (or both if configured)
5. **Logs results** for monitoring and debugging

## Logs

Check the "Edge Notifier" workflow logs to see:
- Startup configuration
- Notification attempts
- Success/failure status
- Any errors

## Notes

- You can configure just Discord, just Telegram, or both
- The notifier will only send to configured channels
- Memory automatically cleans up old notification hashes to prevent overflow
- Runs independently of the main terminal and web dashboard
