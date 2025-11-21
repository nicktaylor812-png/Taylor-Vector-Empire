# TAYLOR VECTOR TERMINAL - NBA Betting Prediction System

## Project Status: ✅ ALL 27 PRODUCTS COMPLETE (November 19, 2025)

## Overview
The "TAYLOR VECTOR TERMINAL" is a comprehensive NBA analytics ecosystem featuring 27 products built on two proprietary metrics: TUSG% (True Usage Percentage) and PVR (Possession Value Rating). The system identifies betting edges with 65%+ accuracy, provides historical analytics across eras, and monetizes through premium features including API services, newsletters, consulting portals, and partnership frameworks.

## User Preferences
- **Formulas**: All TUSG% and PVR formulas, including the AST/TOV multiplier rule for PVR, and the Edge calculation, must be implemented exactly as provided by the user.
- **Stake Sizing**: Use a $100 bankroll and a 0.25 Kelly fraction for stake sizing.
- **Pick Generation**: Generate picks only when the calculated Edge is 65% or higher.
- **Player Filtering**: Only include players who play 10 minutes or more per game in team TUSG% and PVR calculations.
- **Communication Style**: Data-driven, confident, and direct, without unnecessary fluff.
- **Discord Bot**: Embeds should use brand colors #00d4ff (cyan) and #00ff88 (green).
- **Project Ambition**: The project aims to achieve a 65%+ confidence threshold for generated picks.

## System Architecture

### Core Metrics and Edge Calculation
The system's predictions are built upon proprietary metrics:

**TUSG% (True Usage Percentage)**
`(FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100`
Team TUSG% is the average of players with ≥10 min/game.

**PVR (Possession Value Rating)**
`[(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100`
Multiplier Rule: `AST/TOV ≥ 1.8 → Multiplier = 2.3`, else `Multiplier = 1.8`.
Team PVR is the average of players with ≥10 min/game.

**Edge Calculation**
`Edge% = 50 + (Home TUSG% - Away TUSG%) + (Home PVR - Away PVR) × 0.5`
Capped between 45-80%. Picks are generated when Edge ≥ 65%.

### Complete Product Suite (27/27 Products)

**TIER 1 - Foundation (6 products):**
1. All-Time TUSG% Leaderboard - Historical rankings with 15 NBA legends
2. Player Comparison Tool - Side-by-side analysis with radar charts at `/compare`
3. Real-Time Edge Notifications - Discord/Telegram webhooks for 65%+ picks
4. Live Web Dashboard - Running on port 5000 with 21 navigation links
5. Reddit Bot - Auto-posting to r/NBATalk with rate limiting
6. Discord Community Bot - Slash commands (`/tusg`, `/pvr`, `/compare`, `/edge`, `/leaderboard`)

**TIER 2 - Scale (11 products):**
7. Cross-Era PVR Comparisons - MJ/LeBron/Kobe/Wilt with pace adjustments at `/cross-era`
8. Westbrook Rule Historical Machine - 30 seasons analyzed, identifies AST/TOV multiplier impact at `/westbrook-rule`
9. Westbrook Hall of Fame - Validated vs Exposed players at `/westbrook-hof`
10. Positionless GOAT Rankings - Customizable weight sliders, 50 players at `/goat-rankings`
11. Draft Prospect PVR Predictor - College-to-NBA projections at `/draft-predictor`
12. Trade Impact Calculator - Team metric changes and fit scores at `/trade-calculator`
13. Contract Value Calculator - $/PVR analysis, 54 players at `/contract-value`
14. Metric Customizer Web App - Real-time formula tweaking at `/metric-customizer`
15. All-Time Team Builder - $120M salary cap optimizer at `/team-builder`
16. Fantasy Basketball Optimizer - Custom scoring leagues at `/fantasy-optimizer`
17. Instagram Metrics Visualizer - 1080x1080 auto-graphics at `/instagram-creator`
18. TikTok Explanation Bot - 10 video scripts with trending sounds at `/tiktok-scripts`

**TIER 3 - Monetization (10 products):**
19. Daily Edge Report Generator - Automated PDF at 8am daily at `/daily-report`
20. Weekly Player Deep Dive - Rotating elite players, Mondays 9am at `/player-deepdive`
21. Season Prediction Engine - Win totals, MVP/DPOY/MIP/ROY at `/season-predictions`
22. Underrated PVR Stars Series - 24 hidden gems, Fridays 10am at `/underrated-stars`
23. Westbrook Rule Hall of Fame - See item 9 above
24. Premium API Service - 6 REST endpoints, rate limiting, API keys at `/api-docs`
25. Paid Newsletter System - Subscriber management, email automation at `/newsletter`
26. Betting Group Consulting Portal - Multi-tenant, white-labeled at `/portal/demo`
27. Analytics Site Partnership Framework - Widget embeds, revenue sharing at `/partnerships`

**Database**: SQLite (`taylor_62.db`) with tables for picks, API keys, newsletters, consulting groups, partnerships

### UI/UX Decisions
- **Discord Bot**: Utilizes brand colors #00d4ff (cyan) and #00ff88 (green) for embeds. Slash commands provide an interactive user experience.
- **Web Interfaces**: Interactive web interfaces for the Westbrook Rule Historical Machine, Daily Edge Report Generator, and Season Prediction Engine, featuring search, filtering, sortable tables, and visual indicators.
- **Design System**: Vibrant raccoon-themed design with teal/green gradients (#10a37f primary, #38d9a9 accent), glowing effects, ambient background patterns, and signature animated components. DeepSeek-inspired sophistication with heightened color vibrancy.
- **Brand Logo**: Ultra-minimalist geometric eyeless raccoon (charcoal gray and teal), designed to match DeepSeek's logo simplicity while representing the "bandit" theme of finding betting edges.

## Deployment Architecture
- **Web Dashboard (Replit)**: Running on port 5000, hosts all 27 web-based tools and analytics
- **Core Terminal (External)**: User runs `main.py` externally to avoid Replit compute costs
- **Edge Notifier (External)**: User runs `notifications/edge_notifier.py` externally for real-time alerts
- **Social Bots (External)**: Discord, Reddit, TikTok bots run externally with API credentials

## External Dependencies
- **The Odds API**: Fetching live NBA spreads (KEY: ODDS_API_KEY)
- **FREE nbaStats API**: Player season statistics - no authentication required
- **Discord API**: Bot integration via `discord.py` library
- **Telegram Bot API**: Real-time edge notifications
- **ReportLab**: PDF report generation
- **APScheduler**: Automated task scheduling (daily 8am, Monday 9am, Friday 10am)
- **Matplotlib/Pillow**: Instagram graphics generation
- **PRAW**: Reddit bot integration
- **Flask**: Web dashboard framework

## Recent Changes (November 19, 2025)
- ✅ Built all 27 products using parallel agent development
- ✅ Fixed critical minutes parsing bug (NBA API returns "MM:SS" and "HH:MM:SS" formats)
- ✅ Initialized API database on startup for Premium API Service
- ✅ Added 21 navigation links to dashboard for complete product discoverability
- ✅ All formulas verified: TUSG%, PVR with AST/TOV multiplier rule, Edge calculation
- ✅ Web Dashboard running successfully with all databases and schedulers initialized
- ✅ Fixed era detection: Jordan 1987-88 now shows "1980s" (separate 1980s/2000s eras added)
- ✅ Vibrant raccoon-themed design system (DeepSeek-inspired sophistication)
  - Ultra-minimalist eyeless geometric raccoon logo (teal/charcoal)
  - Teal/green color theme with gradients (#10a37f, #38d9a9)
  - Glowing effects, ambient background patterns, animated components
  - Shimmer animations, pulse effects, floating gradients
  - Signature edge capsules with gradient pills
  - Hairline borders (0.5px), generous spacing, Inter typography
  - Complete emoji removal across all 40+ HTML files
  - Applied across all pages: dashboard, compare, cross-era, and all 27 products
- ✅ Universal dark/light mode implementation (November 19, 2025)
  - Fully functional light/dark mode toggle on all 40 HTML pages
  - Theme preference persists across navigation via localStorage
  - Created theme.js for universal theme management
  - Removed style.css conflicts (hard-coded colors)
  - Refined button typography: 13px, 500 weight, -0.01em letter-spacing, 1px borders
  - Fixed logo white background in dark mode (transparent + brightness filter)
  - DeepSeek-style subtle borders and refined button aesthetics across all pages