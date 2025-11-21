"""
TAYLOR VECTOR TERMINAL - Positionless GOAT Rankings
Custom ranking system combining TUSG%, PVR, and Longevity
"""

import json
import os

LONGEVITY_DATA = {
    'Michael Jordan': 15,
    'LeBron James': 21,
    'Kobe Bryant': 20,
    'Wilt Chamberlain': 14,
    'Kareem Abdul-Jabbar': 20,
    'Magic Johnson': 13,
    'Larry Bird': 13,
    "Shaquille O'Neal": 19,
    'Tim Duncan': 19,
    'Kevin Durant': 17,
    'Stephen Curry': 15,
    'Giannis Antetokounmpo': 11,
    'Nikola Jokić': 9,
    'Russell Westbrook': 16,
    'James Harden': 15
}

def load_player_data():
    """Load TUSG% and PVR data from JSON"""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'leaderboard', 'data', 'all_time_tusg.json')
    with open(data_path, 'r') as f:
        return json.load(f)

def normalize_values(values):
    """Normalize values to 0-100 scale"""
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [50.0] * len(values)
    return [(v - min_val) / (max_val - min_val) * 100 for v in values]

def calculate_goat_scores(tusg_weight=0.40, pvr_weight=0.40, longevity_weight=0.20):
    """
    Calculate GOAT scores for all players
    
    Formula: GOAT Score = (TUSG% × weight1) + (PVR × weight2) + (Years × weight3)
    
    Args:
        tusg_weight: Weight for TUSG% (default 0.40)
        pvr_weight: Weight for PVR (default 0.40)
        longevity_weight: Weight for Longevity (default 0.20)
    
    Returns:
        List of player rankings with GOAT scores
    """
    players = load_player_data()
    
    for player in players:
        player['years'] = LONGEVITY_DATA.get(player['player'], 0)
    
    tusg_values = [p['tusg'] for p in players]
    pvr_values = [p['pvr'] for p in players]
    years_values = [p['years'] for p in players]
    
    tusg_normalized = normalize_values(tusg_values)
    pvr_normalized = normalize_values(pvr_values)
    years_normalized = normalize_values(years_values)
    
    for i, player in enumerate(players):
        player['tusg_norm'] = round(tusg_normalized[i], 2)
        player['pvr_norm'] = round(pvr_normalized[i], 2)
        player['years_norm'] = round(years_normalized[i], 2)
        
        player['goat_score'] = round(
            (tusg_normalized[i] * tusg_weight) +
            (pvr_normalized[i] * pvr_weight) +
            (years_normalized[i] * longevity_weight),
            2
        )
    
    players.sort(key=lambda x: x['goat_score'], reverse=True)
    
    for idx, player in enumerate(players, 1):
        player['goat_rank'] = idx
    
    return players

def generate_rankings_json(tusg_weight=0.40, pvr_weight=0.40, longevity_weight=0.20):
    """Generate rankings and return as JSON string"""
    rankings = calculate_goat_scores(tusg_weight, pvr_weight, longevity_weight)
    return json.dumps(rankings, indent=2)

def save_rankings(filename='tools/goat_rankings.json'):
    """Save default rankings to JSON file"""
    rankings = calculate_goat_scores()
    with open(filename, 'w') as f:
        json.dump(rankings, f, indent=2)
    print(f"✅ Saved GOAT rankings to {filename}")
    return rankings

if __name__ == '__main__':
    rankings = save_rankings()
    
    print("\n🏀 POSITIONLESS GOAT RANKINGS (Default Weights)")
    print("=" * 90)
    print(f"Formula: TUSG% (40%) + PVR (40%) + Longevity (20%)")
    print("=" * 90)
    
    for player in rankings[:10]:
        print(f"{player['goat_rank']:2d}. {player['player']:25s} | "
              f"GOAT Score: {player['goat_score']:6.2f} | "
              f"TUSG: {player['tusg']:5.2f}% | PVR: {player['pvr']:5.2f} | Years: {player['years']:2d}")
    
    print("\n💡 WEIGHT SCENARIOS:")
    print("-" * 90)
    
    print("\n📊 Pure Usage (100% TUSG):")
    usage_rankings = calculate_goat_scores(1.0, 0.0, 0.0)
    for i, p in enumerate(usage_rankings[:3], 1):
        print(f"  {i}. {p['player']} - TUSG: {p['tusg']}%")
    
    print("\n⚡ Pure Efficiency (100% PVR):")
    efficiency_rankings = calculate_goat_scores(0.0, 1.0, 0.0)
    for i, p in enumerate(efficiency_rankings[:3], 1):
        print(f"  {i}. {p['player']} - PVR: {p['pvr']}")
    
    print("\n⏳ Pure Longevity (100% Years):")
    longevity_rankings = calculate_goat_scores(0.0, 0.0, 1.0)
    for i, p in enumerate(longevity_rankings[:3], 1):
        print(f"  {i}. {p['player']} - Years: {p['years']}")
    
    print("\n⚖️  Balanced (33.3% each):")
    balanced_rankings = calculate_goat_scores(0.333, 0.333, 0.334)
    for i, p in enumerate(balanced_rankings[:3], 1):
        print(f"  {i}. {p['player']} - Score: {p['goat_score']}")
