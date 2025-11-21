# 🏀 Weekly Player Deep Dive System

## Overview

The Weekly Player Deep Dive is a comprehensive analytical system that generates in-depth reports on NBA players using Taylor Vector Terminal's proprietary TUSG% and PVR metrics.

## Features

### 1. **Automated Player Selection**
- Rotates through elite NBA players weekly (based on ISO week number)
- Featured players: LeBron James, Stephen Curry, Kevin Durant, Giannis, Jokić, Luka, Embiid, Jayson Tatum

### 2. **Comprehensive Analysis**
- ✅ Career TUSG%/PVR trends and progression
- ✅ Season-by-season breakdown
- ✅ Monthly/seasonal performance visualization
- ✅ Strengths & weaknesses analysis
- ✅ Position peer comparison (rankings and percentiles)
- ✅ Betting implications and insights

### 3. **Multiple Output Formats**
- **PDF Report** - Professional print-ready document
- **Markdown Report** - Web-friendly format with tables
- **Video Companion Script** - 6-minute narration outline with timestamps
- **HTML Template** - Standalone web page for hosting

### 4. **Archival System**
- All deep dives automatically archived in `premium/deepdives/`
- Organized by type: markdown, video_scripts, archive metadata
- JSON metadata tracking for easy retrieval

## Directory Structure

```
premium/
├── player_deepdive.py          # Main deep dive generator
├── deepdive_template.html      # Standalone HTML template
├── deepdives/                  # Archive directory
│   ├── archive/               # JSON metadata
│   ├── markdown/              # Markdown reports
│   └── video_scripts/         # Video narration scripts
└── reports/                    # PDF outputs
```

## Usage

### Generate Deep Dive for Featured Player (Automatic)
```bash
cd premium
python player_deepdive.py
```

### Generate Deep Dive for Specific Player
```python
from player_deepdive import generate_complete_deepdive

result = generate_complete_deepdive("Stephen Curry")
```

## Output Components

### 1. PDF Report (`reports/`)
- Professional multi-page report
- Career overview table
- Career progression charts (TUSG% & PVR)
- Season-by-season breakdown table
- Strengths/weaknesses analysis
- Historical context

### 2. Markdown Report (`deepdives/markdown/`)
- GitHub-flavored markdown
- Career statistics tables
- Current season performance
- Peer comparison rankings
- Betting implications
- Methodology explanation

### 3. Video Companion Script (`deepdives/video_scripts/`)
- **Format**: 6-minute structured outline
- **Sections**:
  - 0:00-0:30 - Intro & hook
  - 0:30-1:30 - Career overview
  - 1:30-3:00 - Metrics deep dive
  - 3:00-4:00 - Peer comparison
  - 4:00-5:30 - Betting implications
  - 5:30-6:00 - Conclusion & CTA
- Includes visual cue suggestions

### 4. Archive Metadata (`deepdives/archive/`)
```json
{
  "player_name": "Jayson Tatum",
  "date_generated": "2025-11-19T02:53:44",
  "pdf_path": "/path/to/pdf",
  "markdown_path": "/path/to/markdown",
  "video_script_path": "/path/to/script"
}
```

## Analysis Components

### Career TUSG%/PVR Trends
- Multi-season progression visualization
- Career averages vs current performance
- Trend identification (increasing/decreasing usage)

### Monthly Performance Charts
- Season-by-season comparison
- Above/below career average indicators
- Combined TUSG%, PVR, and PPG visualization

### Strengths & Weaknesses
Automated analysis identifies:
- Elite vs average usage rates
- Efficiency tiers (elite/above-average/average)
- Scoring ability
- Playmaking skills
- Shooting efficiency
- Trend analysis (improving/declining)

### Position Peer Comparison
- Ranks player against all active NBA players
- TUSG% ranking and percentile
- PVR ranking and percentile
- League average comparisons
- Total players analyzed (typically 600-700)

### Betting Implications
Actionable insights including:
- High usage alerts for prop bets
- Efficiency edges for team spreads
- Usage trend warnings
- Playmaking premiums
- Consistency ratings (high/moderate/low volatility)

## Metrics Explained

### TUSG% (True Usage Percentage)
**Formula**: `(FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100`

**Interpretation**:
- >30% - Elite usage, primary offensive option
- 25-30% - High usage star
- 20-25% - Moderate usage contributor
- <20% - Supporting role

### PVR (Possession Value Rating)
**Formula**: `[(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100`

Where multiplier = 2.3 if AST/TOV > 1.8, else 1.8

**Interpretation**:
- >15 - Elite efficiency
- 10-15 - Above average
- 5-10 - Average
- <5 - Below average

## Weekly Schedule

The system is designed to run **every Monday** with:
- Automatic featured player rotation
- Complete deep dive generation
- All output formats created
- Automatic archiving

## Integration Points

### Web Dashboard
The web dashboard at `/player-deepdive` provides:
- Player selection interface
- Real-time deep dive generation
- Interactive visualizations
- PDF export functionality

### Video Production
Use the video companion scripts for:
- YouTube deep dive series
- TikTok/Instagram short-form content
- Podcast talking points
- Live stream preparation

### Social Media
The markdown reports can be:
- Posted to Medium/Substack
- Shared on Twitter/X as threads
- Embedded in Discord/Slack channels
- Used for newsletter content

## Future Enhancements

Potential improvements:
- [ ] Compare player to specific position group (PG, SG, SF, PF, C)
- [ ] Add playoff vs regular season splits
- [ ] Include advanced shooting zones
- [ ] Team chemistry metrics
- [ ] Historical player comparisons (current player vs past legends)
- [ ] Predictive modeling for future performance
- [ ] Injury impact analysis

## API Data Source

**Free NBA Stats API**: `https://api.server.nbaapi.com/api/playertotals`
- No API key required
- Season data from 2015-2025
- Per-game averages calculated automatically

## License

Part of Taylor Vector Terminal - Advanced NBA Analytics Platform
© 2025 All Rights Reserved

## Support

For issues or feature requests, contact the Taylor Vector Terminal team or submit via the main dashboard feedback system.

---

*Generated on November 19, 2025*
