"""
TAYLOR VECTOR TERMINAL - Historical TUSG% & PVR Calculator
Calculates metrics for all-time NBA greats with era-adjusted pace
"""

import json

# Historical NBA pace data (possessions per 48 min) by era
HISTORICAL_PACE = {
    # 1950s-1960s: Fast pace era
    range(1950, 1970): 115.0,
    # 1970s-1980s: Moderate pace
    range(1970, 1990): 107.0,
    # 1990s-2000s: Slower pace
    range(1990, 2010): 95.0,
    # 2010-2020: Modern pace increase
    range(2010, 2020): 98.0,
    # 2020+: Current era
    range(2020, 2030): 99.5
}

def get_era_pace(season):
    """Get average NBA pace for a given season"""
    for year_range, pace in HISTORICAL_PACE.items():
        if season in year_range:
            return pace
    return 99.5  # Default modern pace

def calculate_player_tusg_historical(stats, season):
    """
    Calculate TUSG% for historical player
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
    """
    mp = stats.get('mpg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    # Use era-adjusted pace
    team_pace = get_era_pace(season)
    
    if mp == 0 or team_pace == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * team_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_player_pvr_historical(stats):
    """
    Calculate PVR for historical player
    PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
    """
    pts = stats.get('ppg', 0)
    ast = stats.get('apg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    # Calculate AST/TOV ratio for multiplier
    if tov == 0:
        ast_tov_ratio = ast if ast > 0 else 0
    else:
        ast_tov_ratio = ast / tov
    
    # Multiplier rule: AST/TOV > 1.8 → 2.3x, else 1.8x
    multiplier = 2.3 if ast_tov_ratio > 1.8 else 1.8
    
    numerator = pts + (ast * multiplier)
    denominator = fga + tov + (0.44 * fta) + ast
    
    if denominator == 0:
        return 0.0
    
    pvr = ((numerator / denominator) - 1.00) * 100
    return round(pvr, 2)

# All-Time Greats Sample Data (Career Best Seasons)
ALL_TIME_GREATS = [
    {
        'name': 'Michael Jordan',
        'season': '1987-88',
        'year': 1988,
        'stats': {'mpg': 40.4, 'ppg': 35.0, 'apg': 5.9, 'fga': 27.8, 'fta': 11.9, 'tov': 3.1}
    },
    {
        'name': 'LeBron James',
        'season': '2012-13',
        'year': 2013,
        'stats': {'mpg': 37.9, 'ppg': 26.8, 'apg': 7.3, 'fga': 17.8, 'fta': 7.3, 'tov': 3.0}
    },
    {
        'name': 'Kobe Bryant',
        'season': '2005-06',
        'year': 2006,
        'stats': {'mpg': 41.0, 'ppg': 35.4, 'apg': 4.5, 'fga': 27.2, 'fta': 10.2, 'tov': 3.1}
    },
    {
        'name': 'Wilt Chamberlain',
        'season': '1961-62',
        'year': 1962,
        'stats': {'mpg': 48.5, 'ppg': 50.4, 'apg': 2.4, 'fga': 39.5, 'fta': 17.0, 'tov': 5.0}
    },
    {
        'name': 'Kareem Abdul-Jabbar',
        'season': '1971-72',
        'year': 1972,
        'stats': {'mpg': 44.2, 'ppg': 34.8, 'apg': 4.6, 'fga': 25.2, 'fta': 10.0, 'tov': 3.2}
    },
    {
        'name': 'Magic Johnson',
        'season': '1986-87',
        'year': 1987,
        'stats': {'mpg': 36.3, 'ppg': 23.9, 'apg': 12.2, 'fga': 17.7, 'fta': 5.4, 'tov': 3.8}
    },
    {
        'name': 'Larry Bird',
        'season': '1987-88',
        'year': 1988,
        'stats': {'mpg': 37.9, 'ppg': 29.9, 'apg': 6.1, 'fga': 19.1, 'fta': 5.3, 'tov': 2.9}
    },
    {
        'name': 'Shaquille O\'Neal',
        'season': '1999-00',
        'year': 2000,
        'stats': {'mpg': 40.0, 'ppg': 29.7, 'apg': 3.8, 'fga': 19.0, 'fta': 13.1, 'tov': 2.8}
    },
    {
        'name': 'Tim Duncan',
        'season': '2001-02',
        'year': 2002,
        'stats': {'mpg': 40.6, 'ppg': 25.5, 'apg': 3.7, 'fga': 18.8, 'fta': 6.7, 'tov': 2.5}
    },
    {
        'name': 'Kevin Durant',
        'season': '2013-14',
        'year': 2014,
        'stats': {'mpg': 38.5, 'ppg': 32.0, 'apg': 5.5, 'fga': 20.8, 'fta': 9.2, 'tov': 3.5}
    },
    {
        'name': 'Stephen Curry',
        'season': '2015-16',
        'year': 2016,
        'stats': {'mpg': 34.2, 'ppg': 30.1, 'apg': 6.7, 'fga': 20.2, 'fta': 5.1, 'tov': 3.3}
    },
    {
        'name': 'Giannis Antetokounmpo',
        'season': '2019-20',
        'year': 2020,
        'stats': {'mpg': 30.4, 'ppg': 29.5, 'apg': 5.6, 'fga': 19.7, 'fta': 10.5, 'tov': 3.1}
    },
    {
        'name': 'Nikola Jokić',
        'season': '2021-22',
        'year': 2022,
        'stats': {'mpg': 33.5, 'ppg': 27.1, 'apg': 7.9, 'fga': 18.0, 'fta': 5.5, 'tov': 3.0}
    },
    {
        'name': 'Russell Westbrook',
        'season': '2016-17',
        'year': 2017,
        'stats': {'mpg': 34.6, 'ppg': 31.6, 'apg': 10.4, 'fga': 24.0, 'fta': 10.4, 'tov': 5.4}
    },
    {
        'name': 'James Harden',
        'season': '2018-19',
        'year': 2019,
        'stats': {'mpg': 36.8, 'ppg': 36.1, 'apg': 7.5, 'fga': 24.5, 'fta': 11.0, 'tov': 5.0}
    }
]

def generate_leaderboard():
    """Generate all-time TUSG% and PVR leaderboard"""
    leaderboard = []
    
    for player in ALL_TIME_GREATS:
        tusg = calculate_player_tusg_historical(player['stats'], player['year'])
        pvr = calculate_player_pvr_historical(player['stats'])
        
        leaderboard.append({
            'rank': 0,  # Will be set after sorting
            'player': player['name'],
            'season': player['season'],
            'tusg': tusg,
            'pvr': pvr,
            'mpg': player['stats']['mpg'],
            'ppg': player['stats']['ppg'],
            'apg': player['stats']['apg'],
            'era_pace': get_era_pace(player['year'])
        })
    
    # Sort by TUSG% descending
    leaderboard.sort(key=lambda x: x['tusg'], reverse=True)
    
    # Assign ranks
    for idx, entry in enumerate(leaderboard, 1):
        entry['rank'] = idx
    
    return leaderboard

def save_leaderboard():
    """Generate and save leaderboard to JSON"""
    leaderboard = generate_leaderboard()
    
    with open('data/all_time_tusg.json', 'w') as f:
        json.dump(leaderboard, f, indent=2)
    
    print(f"✅ Generated leaderboard with {len(leaderboard)} players")
    return leaderboard

if __name__ == '__main__':
    leaderboard = save_leaderboard()
    
    print("\n🏀 ALL-TIME TUSG% LEADERBOARD (Top 10)")
    print("="*80)
    for player in leaderboard[:10]:
        print(f"{player['rank']:2d}. {player['player']:25s} {player['season']:10s} | "
              f"TUSG: {player['tusg']:6.2f}% | PVR: {player['pvr']:6.2f} | "
              f"PPG: {player['ppg']:4.1f}")
