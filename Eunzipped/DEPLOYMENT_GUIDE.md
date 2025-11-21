# 🦝 TAYLOR VECTOR TERMINAL - Complete Deployment Guide

## What You Have
**27 NBA Analytics Products** built on proprietary TUSG% and PVR metrics with 65%+ edge detection

### Core Components
- **Web Dashboard** (port 5000) - All 27 products with light/dark mode
- **Edge Detection Terminal** (main.py) - Live betting analysis every 45 seconds
- **Discord Bot** - Slash commands + embeds
- **Reddit Bot** - Auto-posting to r/NBATalk
- **Premium API** - 6 REST endpoints with authentication
- **Monetization Systems** - Newsletter, consulting portal, partnerships
- **Database** - SQLite (taylor_62.db) with all picks and subscribers

### Metrics Formulas
```
TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
  where Multiplier = 2.3 if AST/TOV ≥ 1.8, else 1.8
Edge% = 50 + (Home TUSG% - Away TUSG%) + (Home PVR - Away PVR) × 0.5
```

## Quick Start (Any Platform)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
export ODDS_API_KEY="your_the_odds_api_key"
export BALLDONTLIE_API_KEY="your_balldontlie_key"  # Optional
export DISCORD_TOKEN="your_discord_bot_token"  # For Discord bot
export REDDIT_CLIENT_ID="your_reddit_client_id"  # For Reddit bot
export REDDIT_CLIENT_SECRET="your_reddit_secret"
export REDDIT_USERNAME="your_username"
export REDDIT_PASSWORD="your_password"
```

### 3. Run Web Dashboard
```bash
cd web
python app.py
# Access at http://localhost:5000
```

### 4. Run Edge Detection Terminal (Separate Process)
```bash
python main.py
# Analyzes games every 45 seconds, saves picks to database
```

### 5. Run Bots (Optional)
```bash
# Discord Bot
python bots/discord_bot.py

# Reddit Bot
python bots/reddit_bot.py
```

## File Structure
```
├── main.py                  # Edge detection terminal (954 players)
├── taylor_62.db            # SQLite database (picks, API keys, subscribers)
├── web/
│   ├── app.py              # Flask dashboard (all 27 products)
│   ├── templates/          # 40+ HTML pages with light/dark mode
│   └── static/
│       ├── css/theme.css   # DeepSeek-inspired design system
│       ├── js/theme.js     # Universal theme management
│       └── images/logo_minimal.png  # Multi-color teal raccoon
├── bots/
│   ├── discord_bot.py      # Slash commands (/tusg, /pvr, /edge, etc)
│   └── reddit_bot.py       # Auto-posting with rate limiting
├── api/
│   └── premium_api.py      # REST API with authentication
├── premium/
│   ├── daily_edge_report.py
│   ├── weekly_player_deepdive.py
│   ├── newsletter_system.py
│   ├── consulting_portal.py
│   └── partnership_framework.py
└── notifications/
    └── edge_notifier.py    # Discord/Telegram webhooks
```

## Platform-Specific Deployment

### Heroku
```bash
# Already configured with Procfile
heroku create your-app-name
heroku config:set ODDS_API_KEY=your_key
git push heroku main
```

### Railway/Render
- Import this folder
- Set environment variables in dashboard
- Deploy command: `cd web && python app.py`

### VPS (DigitalOcean, AWS, etc)
```bash
# Install dependencies
pip install -r requirements.txt

# Run with supervisor or systemd
# Web: cd web && gunicorn -w 4 -b 0.0.0.0:5000 app:app
# Terminal: python main.py
```

### Local Development
```bash
cd web && python app.py  # Terminal 1
python main.py           # Terminal 2 (edge detection)
```

## Database Schema
**Picks Table** - All betting edges ≥65%
**API Keys Table** - Premium API authentication
**Newsletter Subscribers** - Email automation system
**Consulting Groups** - Multi-tenant portal data
**Partnerships** - Revenue sharing analytics

## Design System
- **Colors**: #10a37f (teal), #38d9a9 (green accent), #f8f9fa (light bg)
- **Typography**: Inter font, 13px buttons, hairline borders (0.5px)
- **Logo**: Ultra-minimalist teal/black/gray/white raccoon (DeepSeek-style)
- **Theme**: Full light/dark mode with localStorage persistence

## API Keys Required
- **The Odds API** (ODDS_API_KEY) - Live NBA spreads - https://the-odds-api.com
- **BallDontLie API** (optional) - Backup player stats
- **Discord** (DISCORD_TOKEN) - Bot integration
- **Reddit** (client_id, client_secret) - Auto-posting

## Support
All 27 products documented in individual HTML pages at `/product-name`
Edge threshold: 65% minimum (configurable in main.py)
Bankroll: $100 with 0.25 Kelly fraction
