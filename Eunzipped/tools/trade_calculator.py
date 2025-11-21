"""
TAYLOR VECTOR TERMINAL - Trade Impact Calculator
Analyzes how trades affect team TUSG% and PVR metrics
"""

import requests
import json
import time
from datetime import datetime

TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

TEAM_FULL_NAMES = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets',
    'CHA': 'Charlotte Hornets', 'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets', 'DET': 'Detroit Pistons',
    'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat', 'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves',
    'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks', 'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs',
    'TOR': 'Toronto Raptors', 'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
}

def fetch_current_rosters(season=2025):
    """
    Fetch current 2024-25 season player stats from nbaStats API
    Returns dictionary of players by team
    """
    all_stats = []
    page = 1
    page_size = 100
    
    print(f"🔄 Fetching 2024-25 season rosters from nbaStats API...")
    
    try:
        while True:
            url = f"https://api.server.nbaapi.com/api/playertotals?season={season}&pageSize={page_size}&page={page}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('data', [])
                
                if not players:
                    break
                
                for player in players:
                    games = player.get('games', 0)
                    if games == 0:
                        continue
                    
                    stats = {
                        'player_id': player.get('slug'),
                        'player_name': player.get('playerName'),
                        'team': player.get('team'),
                        'games_played': games,
                        'min': player.get('minutesPg', 0),
                        'pts': player.get('points', 0) / games,
                        'ast': player.get('assists', 0) / games,
                        'tov': player.get('turnovers', 0) / games,
                        'fga': player.get('fieldAttempts', 0) / games,
                        'fta': player.get('ftAttempts', 0) / games
                    }
                    all_stats.append(stats)
                
                if len(players) < page_size:
                    break
                
                page += 1
                time.sleep(0.3)
            else:
                print(f"❌ nbaStats API failed: {response.status_code}")
                break
        
        print(f"✅ Loaded {len(all_stats)} players from 2024-25 season")
        
        # Group by team
        rosters = {}
        for team_abbr in TEAM_PACE.keys():
            rosters[team_abbr] = [p for p in all_stats if p.get('team') == team_abbr and p.get('min', 0) >= 5]
        
        return rosters
    
    except Exception as e:
        print(f"❌ Error fetching rosters: {e}")
        return {}

def calculate_player_tusg(player_stats, team_abbr):
    """
    Calculate TUSG% for a player
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
    """
    mp = player_stats.get('min', 0)
    fga = player_stats.get('fga', 0)
    tov = player_stats.get('tov', 0)
    fta = player_stats.get('fta', 0)
    
    team_pace = TEAM_PACE.get(team_abbr, 99.5)
    
    if mp == 0 or team_pace == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * team_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_player_pvr(player_stats):
    """
    Calculate PVR for a player
    PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
    Multiplier: AST/TOV ≥ 1.8 → 2.3, else 1.8
    """
    pts = player_stats.get('pts', 0)
    ast = player_stats.get('ast', 0)
    fga = player_stats.get('fga', 0)
    tov = player_stats.get('tov', 0)
    fta = player_stats.get('fta', 0)
    
    if tov == 0:
        ast_tov_ratio = ast if ast > 0 else 0
    else:
        ast_tov_ratio = ast / tov
    
    multiplier = 2.3 if ast_tov_ratio > 1.8 else 1.8
    
    numerator = pts + (ast * multiplier)
    denominator = fga + tov + (0.44 * fta) + ast
    
    if denominator == 0:
        return 0.0
    
    pvr = ((numerator / denominator) - 1.00) * 100
    return round(pvr, 2)

def calculate_player_fit_score(player_tusg, player_pvr):
    """
    Calculate Fit Score for a player based on TUSG% and PVR
    
    Fit Score Logic:
    - High PVR + Low TUSG = Efficient role player (BEST fit, score 80-100)
    - High PVR + High TUSG = Star player (good fit, score 70-90)
    - Low PVR + Low TUSG = Role player (okay fit, score 50-70)
    - High TUSG + Low PVR = Ball-dominant inefficient (WORST fit, score 20-50)
    
    Formula: Base score from PVR, bonus/penalty from TUSG efficiency
    """
    pvr_score = min(max(player_pvr * 5 + 50, 0), 100)
    
    if player_pvr > 10:
        if player_tusg < 18:
            tusg_bonus = 20
        elif player_tusg < 22:
            tusg_bonus = 10
        else:
            tusg_bonus = -5
    elif player_pvr > 5:
        if player_tusg < 20:
            tusg_bonus = 5
        else:
            tusg_bonus = -10
    else:
        if player_tusg > 22:
            tusg_bonus = -20
        elif player_tusg > 18:
            tusg_bonus = -10
        else:
            tusg_bonus = 0
    
    fit_score = pvr_score + tusg_bonus
    return round(max(min(fit_score, 100), 0), 1)

def calculate_team_metrics(roster, team_abbr):
    """
    Calculate team TUSG% and PVR based on roster
    Uses minutes-weighted average for players with 10+ MPG
    """
    qualified_players = [p for p in roster if p.get('min', 0) >= 10]
    
    if not qualified_players:
        return {'tusg': 0.0, 'pvr': 0.0, 'fit_score': 0.0}
    
    total_minutes = sum(p.get('min', 0) for p in qualified_players)
    
    if total_minutes == 0:
        return {'tusg': 0.0, 'pvr': 0.0, 'fit_score': 0.0}
    
    weighted_tusg = 0
    weighted_pvr = 0
    weighted_fit = 0
    
    for player in qualified_players:
        player_min = player.get('min', 0)
        weight = player_min / total_minutes
        
        player_tusg = calculate_player_tusg(player, team_abbr)
        player_pvr = calculate_player_pvr(player)
        player_fit = calculate_player_fit_score(player_tusg, player_pvr)
        
        weighted_tusg += player_tusg * weight
        weighted_pvr += player_pvr * weight
        weighted_fit += player_fit * weight
    
    return {
        'tusg': round(weighted_tusg, 2),
        'pvr': round(weighted_pvr, 2),
        'fit_score': round(weighted_fit, 1)
    }

def simulate_trade(team_a_abbr, team_a_gives, team_b_abbr, team_b_gives, rosters):
    """
    Simulate a trade between two teams
    
    Args:
        team_a_abbr: Team A abbreviation (e.g., 'LAL')
        team_a_gives: List of player names Team A trades away
        team_b_abbr: Team B abbreviation (e.g., 'NOP')
        team_b_gives: List of player names Team B trades away
        rosters: Current rosters dictionary
    
    Returns:
        Dictionary with before/after metrics for both teams
    """
    # Get current rosters
    team_a_roster = rosters.get(team_a_abbr, []).copy()
    team_b_roster = rosters.get(team_b_abbr, []).copy()
    
    # Calculate before metrics
    team_a_before = calculate_team_metrics(team_a_roster, team_a_abbr)
    team_b_before = calculate_team_metrics(team_b_roster, team_b_abbr)
    
    # Find and move players
    team_a_traded_players = []
    team_b_traded_players = []
    
    for player_name in team_a_gives:
        for player in team_a_roster[:]:
            if player.get('player_name', '').lower() == player_name.lower():
                team_a_traded_players.append(player)
                team_a_roster.remove(player)
                break
    
    for player_name in team_b_gives:
        for player in team_b_roster[:]:
            if player.get('player_name', '').lower() == player_name.lower():
                team_b_traded_players.append(player)
                team_b_roster.remove(player)
                break
    
    # Execute trade
    for player in team_b_traded_players:
        player['team'] = team_a_abbr
        team_a_roster.append(player)
    
    for player in team_a_traded_players:
        player['team'] = team_b_abbr
        team_b_roster.append(player)
    
    # Calculate after metrics
    team_a_after = calculate_team_metrics(team_a_roster, team_a_abbr)
    team_b_after = calculate_team_metrics(team_b_roster, team_b_abbr)
    
    # Calculate impacts
    team_a_impact = {
        'tusg_change': round(team_a_after['tusg'] - team_a_before['tusg'], 2),
        'pvr_change': round(team_a_after['pvr'] - team_a_before['pvr'], 2),
        'fit_change': round(team_a_after['fit_score'] - team_a_before['fit_score'], 1)
    }
    
    team_b_impact = {
        'tusg_change': round(team_b_after['tusg'] - team_b_before['tusg'], 2),
        'pvr_change': round(team_b_after['pvr'] - team_b_before['pvr'], 2),
        'fit_change': round(team_b_after['fit_score'] - team_b_before['fit_score'], 1)
    }
    
    # Determine winner (higher PVR gain wins, if tied use TUSG% gain)
    if team_a_impact['pvr_change'] > team_b_impact['pvr_change']:
        winner = team_a_abbr
    elif team_b_impact['pvr_change'] > team_a_impact['pvr_change']:
        winner = team_b_abbr
    elif team_a_impact['tusg_change'] > team_b_impact['tusg_change']:
        winner = team_a_abbr
    elif team_b_impact['tusg_change'] > team_a_impact['tusg_change']:
        winner = team_b_abbr
    else:
        winner = 'TIE'
    
    return {
        'team_a': {
            'name': TEAM_FULL_NAMES.get(team_a_abbr, team_a_abbr),
            'abbr': team_a_abbr,
            'gave': team_a_gives,
            'received': team_b_gives,
            'before': team_a_before,
            'after': team_a_after,
            'impact': team_a_impact
        },
        'team_b': {
            'name': TEAM_FULL_NAMES.get(team_b_abbr, team_b_abbr),
            'abbr': team_b_abbr,
            'gave': team_b_gives,
            'received': team_a_gives,
            'before': team_b_before,
            'after': team_b_after,
            'impact': team_b_impact
        },
        'winner': winner,
        'timestamp': datetime.now().isoformat()
    }

# Famous historical trade examples
HISTORICAL_TRADES = [
    {
        'name': 'Lakers-Pelicans Anthony Davis Trade (2019)',
        'description': 'Lakers acquire AD, Pelicans get young core + picks',
        'team_a': 'LAL',
        'team_a_gives': ['Lonzo Ball', 'Brandon Ingram', 'Josh Hart'],
        'team_b': 'NOP',
        'team_b_gives': ['Anthony Davis'],
        'year': 2019,
        'result': 'Lakers won 2020 NBA Championship'
    },
    {
        'name': 'Mavericks-Nets Kyrie Irving Trade (2023)',
        'description': 'Mavs acquire Kyrie to pair with Luka',
        'team_a': 'DAL',
        'team_a_gives': ['Spencer Dinwiddie', 'Dorian Finney-Smith'],
        'team_b': 'BKN',
        'team_b_gives': ['Kyrie Irving'],
        'year': 2023,
        'result': 'Mavs reached 2024 Finals'
    },
    {
        'name': 'Clippers-76ers James Harden Trade (2023)',
        'description': 'Clippers acquire Harden for depth pieces',
        'team_a': 'LAC',
        'team_a_gives': ['Marcus Morris', 'Robert Covington'],
        'team_b': 'PHI',
        'team_b_gives': ['James Harden'],
        'year': 2023,
        'result': 'Clippers formed Big 4'
    },
    {
        'name': 'Nets-Rockets James Harden Trade (2021)',
        'description': 'Nets acquire Harden for Nets young assets',
        'team_a': 'BKN',
        'team_a_gives': ['Caris LeVert', 'Jarrett Allen'],
        'team_b': 'HOU',
        'team_b_gives': ['James Harden'],
        'year': 2021,
        'result': 'Nets superteam formed (KD, Harden, Kyrie)'
    },
    {
        'name': '76ers-Nets James Harden Trade (2022)',
        'description': 'Sixers acquire Harden, Nets get Simmons',
        'team_a': 'PHI',
        'team_a_gives': ['Ben Simmons', 'Seth Curry'],
        'team_b': 'BKN',
        'team_b_gives': ['James Harden'],
        'year': 2022,
        'result': 'Both teams struggled post-trade'
    },
    {
        'name': 'Celtics-Nets Big 3 Trade (2013)',
        'description': 'Nets acquire aging stars for massive haul',
        'team_a': 'BKN',
        'team_a_gives': ['MarShon Brooks', 'Kris Humphries'],
        'team_b': 'BOS',
        'team_b_gives': ['Paul Pierce', 'Kevin Garnett'],
        'year': 2013,
        'result': 'Celtics rebuild, Nets disaster'
    },
    {
        'name': 'Raptors-Spurs Kawhi Leonard Trade (2018)',
        'description': 'Raptors all-in for championship run',
        'team_a': 'TOR',
        'team_a_gives': ['DeMar DeRozan', 'Jakob Poeltl'],
        'team_b': 'SAS',
        'team_b_gives': ['Kawhi Leonard', 'Danny Green'],
        'year': 2018,
        'result': 'Raptors won 2019 NBA Championship'
    },
    {
        'name': 'Suns-Nets Kevin Durant Trade (2023)',
        'description': 'Suns acquire KD for championship push',
        'team_a': 'PHX',
        'team_a_gives': ['Mikal Bridges', 'Cam Johnson'],
        'team_b': 'BKN',
        'team_b_gives': ['Kevin Durant'],
        'year': 2023,
        'result': 'Suns superteam (KD, Booker, Beal)'
    }
]

def save_historical_trades(filename='trade_calculator_examples.json'):
    """Save historical trade examples to JSON"""
    import os
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(HISTORICAL_TRADES, f, indent=2)
    print(f"✅ Saved {len(HISTORICAL_TRADES)} historical trade examples to {filepath}")

if __name__ == '__main__':
    print("🏀 TAYLOR VECTOR TERMINAL - Trade Impact Calculator")
    print("=" * 80)
    
    # Save historical examples
    save_historical_trades()
    
    # Fetch current rosters
    rosters = fetch_current_rosters(2025)
    
    if not rosters:
        print("❌ Could not fetch rosters")
        exit(1)
    
    print("\n📊 Example Trade Simulation:")
    print("-" * 80)
    
    # Example: Lakers trade LeBron James to Cavs for players
    result = simulate_trade(
        'LAL', ['LeBron James'],
        'CLE', ['Donovan Mitchell'],
        rosters
    )
    
    print(f"\n🔄 Trade Simulation:")
    print(f"   {result['team_a']['name']} trades: {', '.join(result['team_a']['gave'])}")
    print(f"   {result['team_b']['name']} trades: {', '.join(result['team_b']['gave'])}")
    
    print(f"\n📈 {result['team_a']['name']} Impact:")
    print(f"   TUSG%: {result['team_a']['before']['tusg']:.2f}% → {result['team_a']['after']['tusg']:.2f}% "
          f"({result['team_a']['impact']['tusg_change']:+.2f}%)")
    print(f"   PVR: {result['team_a']['before']['pvr']:.2f} → {result['team_a']['after']['pvr']:.2f} "
          f"({result['team_a']['impact']['pvr_change']:+.2f})")
    print(f"   Fit Score: {result['team_a']['before']['fit_score']:.1f} → {result['team_a']['after']['fit_score']:.1f} "
          f"({result['team_a']['impact']['fit_change']:+.1f})")
    
    print(f"\n📈 {result['team_b']['name']} Impact:")
    print(f"   TUSG%: {result['team_b']['before']['tusg']:.2f}% → {result['team_b']['after']['tusg']:.2f}% "
          f"({result['team_b']['impact']['tusg_change']:+.2f}%)")
    print(f"   PVR: {result['team_b']['before']['pvr']:.2f} → {result['team_b']['after']['pvr']:.2f} "
          f"({result['team_b']['impact']['pvr_change']:+.2f})")
    print(f"   Fit Score: {result['team_b']['before']['fit_score']:.1f} → {result['team_b']['after']['fit_score']:.1f} "
          f"({result['team_b']['impact']['fit_change']:+.1f})")
    
    print(f"\n🏆 Trade Winner: {result['winner']}")
    print("=" * 80)
