# 🦝 TAYLOR VECTOR EMPIRE - COMPLETE EXPORT BUNDLE

## What's Inside This Package

**8MB Complete Analytics Empire** - Everything you need to run your NBA betting system on any platform.

### 📦 Contents
- ✅ **27 Products** (all tiers: Foundation, Scale, Monetization)
- ✅ **Edge Detection Terminal** (main.py - 954 players)
- ✅ **Web Dashboard** (Flask app with 40+ pages)
- ✅ **All Bots** (Discord, Reddit, Telegram notifier)
- ✅ **Monetization Systems** (API, newsletter, consulting, partnerships)
- ✅ **Database** (taylor_62.db with schema)
- ✅ **Logo** (Multi-color teal raccoon - DeepSeek style)
- ✅ **Design System** (Light/dark mode, theme persistence)

### 🚀 Quick Deployment

**1. Extract Archive**
```bash
tar -xzf TAYLOR_VECTOR_EMPIRE_COMPLETE.tar.gz
cd [extracted-folder]
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Set API Keys**
```bash
export ODDS_API_KEY="your_the_odds_api_key"
```

**4. Launch**
```bash
# Terminal 1: Web Dashboard
cd web && python app.py

# Terminal 2: Edge Detection
python main.py
```

**5. Access**
- Web Dashboard: http://localhost:5000
- All 27 products accessible via navigation

### 📖 Full Documentation
See `DEPLOYMENT_GUIDE.md` for:
- Platform-specific deployment (Heroku, Railway, VPS)
- All environment variables
- Bot setup instructions
- API endpoint documentation
- Database schema details

### 🎯 Core Features
- **Edge Detection**: Analyzes 9 live NBA games every 45 seconds
- **65% Threshold**: Only shows high-confidence betting picks
- **Proprietary Metrics**: TUSG% and PVR with Westbrook Rule
- **Automated Reports**: Daily (8am), Weekly (Mon 9am, Fri 10am)
- **Multi-Platform**: Works on Heroku, Railway, VPS, localhost

### 📊 Metrics Formulas
```
TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
  where Multiplier = 2.3 if AST/TOV ≥ 1.8, else 1.8
Edge% = 50 + (Home TUSG% - Away TUSG%) + (Home PVR - Away PVR) × 0.5
```

### 💎 The 27 Products
See `.export_manifest.txt` for complete checklist.

**Foundation**: Leaderboards, Comparison, Notifications, Dashboard, Bots
**Scale**: Cross-Era, Westbrook Machine, GOAT Rankings, Trade Calculator, etc.
**Monetization**: Daily Reports, Premium API, Newsletter, Consulting, Partnerships

### 🔑 Required API Keys
- **The Odds API** (required) - https://the-odds-api.com
- **Discord Token** (optional) - For Discord bot
- **Reddit Credentials** (optional) - For Reddit auto-posting

### 🎨 Design
- DeepSeek-inspired aesthetic with teal/green gradients
- Full light/dark mode toggle with localStorage
- 40+ responsive HTML pages
- Ultra-minimalist raccoon logo (teal/black/gray/white)

---

**🚀 EMPIRE EXTRACTED - DEPLOY ANYWHERE**
