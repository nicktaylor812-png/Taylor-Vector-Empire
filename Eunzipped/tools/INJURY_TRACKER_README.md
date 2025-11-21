# 🏥 Injury Comeback Tracker - TAYLOR VECTOR TERMINAL

## Overview
Educational tool tracking NBA player performance before and after major injuries using TUSG% and PVR metrics.

## Features

### 📊 Historical Injury Database (22 Injuries)
Tracks major NBA injuries including:
- ACL Tears (Klay Thompson, Derrick Rose, Zach LaVine, Jamal Murray, Kristaps Porzingis)
- Achilles Tears (Kevin Durant, Kobe Bryant, DeMarcus Cousins, John Wall)
- Other major injuries (Paul George, Gordon Hayward, Isaiah Thomas, etc.)

### 🔍 Search Functionality
- Search by player name
- Filter by injury type
- Real-time filtering

### 🚨 Current Injury Watch
Live tracking of currently injured players:
- Ja Morant (Shoulder Labral Tear)
- Kawhi Leonard (Knee Inflammation)
- Joel Embiid (Knee Meniscus)

Shows:
- Days until expected return
- Pre-injury metrics
- Projected post-injury performance
- Expected impact severity

### 📈 Recovery Projections by Injury Type

**Very High Severity:**
- Achilles Tear: 65% PVR retention (1yr), 75% (2yr)
- Hip Injury: 60% PVR retention (1yr), 68% (2yr)
- Knee Dislocation: 55% PVR retention (1yr), 70% (2yr)

**High Severity:**
- ACL Tear: 75% PVR retention (1yr), 88% (2yr)
- Quad Rupture: 68% PVR retention (1yr), 78% (2yr)
- Multiple Knee Surgeries: 85% PVR retention (1yr), 91% (2yr)

**Moderate Severity:**
- Ankle Fracture: 80% PVR retention (1yr), 90% (2yr)
- Quad Tendinopathy: 92% PVR retention (1yr), 98% (2yr)

**Low Severity:**
- Knee Meniscus: 96% PVR retention (1yr), 98% (2yr)

### 📊 Key Metrics Tracked
- **TUSG%**: True Usage Percentage (volume metric)
- **PVR**: Points Value Rating (efficiency metric)
- **PPG**: Points per game
- **APG**: Assists per game
- **MPG**: Minutes per game

### 💡 Educational Insights
Shows which injuries primarily affect:
- **Efficiency (PVR)**: Achilles tears, hip injuries
- **Usage (TUSG%)**: Generally better retained than efficiency
- **Both**: Severe knee injuries

## Usage

### Running the Tracker
1. **Generate/Update Data:**
   ```bash
   cd tools
   python injury_tracker.py
   ```

2. **View Web Interface:**
   Open `tools/injury_tracker.html` in a web browser

### Features in Web Interface
- **Search**: Type player name or injury type to filter
- **Select Injury**: Click any injury card to view detailed analysis
- **View Charts**: See pre vs post-injury metrics visualized
- **Current Watch**: Monitor active injuries with projections
- **Trends**: Analyze recovery patterns by injury type

## Key Findings

### Best Recoveries (2-Year)
1. Zach LaVine - 117% PVR retention (ACL Tear)
2. Paul George - 104% PVR retention (Leg Fracture)
3. Kawhi Leonard - 98% PVR retention (Quad Tendinopathy)
4. Jamal Murray - 97% PVR retention (ACL Tear)
5. Kevin Durant - 97% PVR retention (Achilles Tear)

### Worst Recoveries
1. Isaiah Thomas - 44% PVR retention (Hip Injury)
2. DeMarcus Cousins - 48% PVR retention (Achilles Tear)
3. Andrew Bynum - 49% PVR retention (Multiple Knee Injuries)

## Files
- `injury_tracker.py`: Python script with injury database and analytics
- `injury_tracker.html`: Interactive web interface
- `injury_tracker_data.json`: Generated data file (auto-created)

## Educational Value
Demonstrates:
- How different injuries affect player performance
- Importance of age at injury time
- Difference between volume (TUSG%) and efficiency (PVR) recovery
- Value of historical data in projecting recovery timelines
