"""
TAYLOR VECTOR TERMINAL - All-Time Team Builder
Fantasy team constructor using salary cap and metric optimization
"""

import json
import os
from typing import List, Dict, Tuple

# Constants
SALARY_CAP = 120_000_000  # $120M NBA standard
ROSTER_SIZE = 5  # 5 players (positionless)
LEADERBOARD_FILE = '../leaderboard/data/all_time_tusg.json'

def load_players_with_salaries() -> List[Dict]:
    """
    Load historical players from leaderboard and assign salaries
    
    Salary formula based on:
    - PVR (primary driver)
    - TUSG% (efficiency consideration)
    - Era adjustment (modern players get slight premium)
    - Superstar premium for elite PVR
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    leaderboard_path = os.path.join(script_dir, LEADERBOARD_FILE)
    
    with open(leaderboard_path, 'r') as f:
        leaderboard = json.load(f)
    
    players = []
    
    for player_data in leaderboard:
        # Calculate salary based on PVR and TUSG%
        pvr = player_data['pvr']
        tusg = player_data['tusg']
        
        # Base salary from PVR (scales exponentially for elite players)
        if pvr >= 40:  # Elite (Curry, Jokic, Magic, Bird, LeBron)
            base_salary = 45_000_000 + (pvr - 40) * 1_500_000
        elif pvr >= 30:  # All-NBA (Giannis, Durant)
            base_salary = 35_000_000 + (pvr - 30) * 1_000_000
        elif pvr >= 20:  # All-Star (Westbrook, Harden, Durant)
            base_salary = 25_000_000 + (pvr - 20) * 1_000_000
        elif pvr >= 15:  # Solid Starter (Jordan, Kareem, Shaq, Duncan)
            base_salary = 18_000_000 + (pvr - 15) * 1_400_000
        elif pvr >= 10:  # Starter (Kobe)
            base_salary = 12_000_000 + (pvr - 10) * 1_200_000
        else:  # Role Player (Wilt - era-adjusted PVR)
            base_salary = 8_000_000 + pvr * 400_000
        
        # TUSG efficiency adjustment (lower TUSG with high PVR = more valuable)
        if pvr >= 35 and tusg < 30:  # Efficient superstar
            base_salary *= 1.15
        elif pvr >= 25 and tusg < 35:  # Efficient all-star
            base_salary *= 1.10
        elif tusg > 43:  # High usage might reduce value slightly
            base_salary *= 0.95
        
        # Era adjustment (give modern players slight premium for relevance)
        season_year = int(player_data['season'].split('-')[0])
        if season_year >= 2015:  # Modern era
            base_salary *= 1.05
        elif season_year >= 2000:  # 2000s era
            base_salary *= 1.00
        elif season_year >= 1980:  # 80s-90s era
            base_salary *= 0.95
        else:  # Pre-1980
            base_salary *= 0.90
        
        # Round to nearest $100k
        salary = round(base_salary / 100_000) * 100_000
        
        # Ensure minimum and maximum bounds
        salary = max(min(salary, 55_000_000), 8_000_000)
        
        player = {
            'id': f"player_{player_data['rank']}",
            'name': player_data['player'],
            'season': player_data['season'],
            'tusg': player_data['tusg'],
            'pvr': player_data['pvr'],
            'mpg': player_data['mpg'],
            'ppg': player_data['ppg'],
            'apg': player_data['apg'],
            'era_pace': player_data.get('era_pace', 100),
            'salary': salary,
            'rank': player_data['rank']
        }
        
        players.append(player)
    
    # Sort by rank (performance)
    players.sort(key=lambda x: x['rank'])
    
    return players

def calculate_team_metrics(roster: List[Dict]) -> Dict:
    """Calculate team metrics from roster"""
    if not roster:
        return {
            'total_pvr': 0.0,
            'avg_tusg': 0.0,
            'total_salary': 0,
            'cap_space': SALARY_CAP,
            'roster_count': 0
        }
    
    total_pvr = sum(p['pvr'] for p in roster)
    avg_tusg = sum(p['tusg'] for p in roster) / len(roster)
    total_salary = sum(p['salary'] for p in roster)
    cap_space = SALARY_CAP - total_salary
    
    return {
        'total_pvr': round(total_pvr, 2),
        'avg_tusg': round(avg_tusg, 2),
        'total_salary': total_salary,
        'cap_space': cap_space,
        'roster_count': len(roster)
    }

def optimize_roster_greedy(players: List[Dict], max_players: int = ROSTER_SIZE) -> Tuple[List[Dict], Dict]:
    """
    Greedy algorithm to maximize team PVR under salary cap
    
    Strategy:
    1. Sort players by PVR/salary ratio (value per dollar)
    2. Add players in order until cap is hit or roster is full
    3. Try to swap in higher PVR players if space allows
    """
    # Calculate value per million for each player
    players_with_value = []
    for player in players:
        value_per_million = player['pvr'] / (player['salary'] / 1_000_000)
        players_with_value.append({
            **player,
            'value_per_million': value_per_million
        })
    
    # Sort by value per million (descending)
    sorted_players = sorted(players_with_value, key=lambda x: x['value_per_million'], reverse=True)
    
    # Greedy selection
    roster = []
    current_salary = 0
    
    for player in sorted_players:
        if len(roster) >= max_players:
            break
        
        if current_salary + player['salary'] <= SALARY_CAP:
            roster.append(player)
            current_salary += player['salary']
    
    # Try to optimize by swapping (upgrade to higher PVR if possible)
    improved = True
    while improved:
        improved = False
        for i, roster_player in enumerate(roster):
            for candidate in sorted_players:
                if candidate in roster:
                    continue
                
                # Try swapping
                new_salary = current_salary - roster_player['salary'] + candidate['salary']
                if new_salary <= SALARY_CAP and candidate['pvr'] > roster_player['pvr']:
                    roster[i] = candidate
                    current_salary = new_salary
                    improved = True
                    break
            if improved:
                break
    
    metrics = calculate_team_metrics(roster)
    
    return roster, metrics

def get_historical_teams() -> List[Dict]:
    """
    Get historical championship/legendary team templates
    
    These are pre-built rosters showcasing famous teams
    """
    players = load_players_with_salaries()
    
    # Helper function to find player by name and season
    def find_player(name: str, season: str = None):
        for p in players:
            if p['name'] == name:
                if season is None or p['season'] == season:
                    return p
        return None
    
    templates = []
    
    # 2015-16 Warriors (73-9 season)
    warriors_2016 = [
        find_player("Stephen Curry", "2015-16"),
        find_player("Klay Thompson", "2015-16") or find_player("Kevin Durant", "2013-14"),
        find_player("Draymond Green", "2015-16") or find_player("Giannis Antetokounmpo", "2019-20"),
        find_player("Andre Iguodala", "2015-16") or find_player("LeBron James", "2012-13"),
        find_player("Harrison Barnes", "2015-16") or find_player("Kawhi Leonard", "2015-16")
    ]
    warriors_roster = [p for p in warriors_2016 if p is not None][:5]
    
    if len(warriors_roster) >= 3:
        templates.append({
            'name': '2015-16 Warriors (73-9)',
            'description': 'Greatest regular season team ever - elite shooting and spacing',
            'roster': warriors_roster,
            'metrics': calculate_team_metrics(warriors_roster)
        })
    
    # 1995-96 Bulls (72-10 season)
    bulls_1996 = [
        find_player("Michael Jordan", "1987-88"),
        find_player("Scottie Pippen", "1995-96") or find_player("Kobe Bryant", "2005-06"),
        find_player("Dennis Rodman", "1995-96") or find_player("Tim Duncan", "2001-02"),
        find_player("Toni Kukoc", "1995-96") or find_player("Larry Bird", "1987-88"),
        find_player("Ron Harper", "1995-96") or find_player("Magic Johnson", "1986-87")
    ]
    bulls_roster = [p for p in bulls_1996 if p is not None][:5]
    
    if len(bulls_roster) >= 3:
        templates.append({
            'name': '1995-96 Bulls (72-10)',
            'description': 'Dominant championship team - perfect balance of scoring and defense',
            'roster': bulls_roster,
            'metrics': calculate_team_metrics(bulls_roster)
        })
    
    # 2012-13 Heat (LeBron MVP season)
    heat_2013 = [
        find_player("LeBron James", "2012-13"),
        find_player("Dwyane Wade", "2012-13") or find_player("James Harden", "2018-19"),
        find_player("Chris Bosh", "2012-13") or find_player("Kevin Durant", "2013-14"),
        find_player("Ray Allen", "2012-13") or find_player("Stephen Curry", "2015-16"),
        find_player("Shane Battier", "2012-13") or find_player("Kawhi Leonard", "2015-16")
    ]
    heat_roster = [p for p in heat_2013 if p is not None][:5]
    
    if len(heat_roster) >= 3:
        templates.append({
            'name': '2012-13 Heat (Championship)',
            'description': 'LeBron\'s peak - unstoppable offensive versatility',
            'roster': heat_roster,
            'metrics': calculate_team_metrics(heat_roster)
        })
    
    # Modern Superteam (highest PVR players)
    modern_superteam = sorted(players, key=lambda x: x['pvr'], reverse=True)[:5]
    templates.append({
        'name': 'PVR Dream Team',
        'description': 'Top 5 highest PVR seasons ever - ultimate efficiency',
        'roster': modern_superteam,
        'metrics': calculate_team_metrics(modern_superteam)
    })
    
    # Value Team (best PVR per dollar)
    value_players = []
    for player in players:
        player['value_ratio'] = player['pvr'] / (player['salary'] / 1_000_000)
    value_team = sorted(players, key=lambda x: x['value_ratio'], reverse=True)[:5]
    templates.append({
        'name': 'Value Kings',
        'description': 'Best PVR per dollar - maximize efficiency on a budget',
        'roster': value_team,
        'metrics': calculate_team_metrics(value_team)
    })
    
    # High Usage Team (highest TUSG%)
    usage_team = sorted(players, key=lambda x: x['tusg'], reverse=True)[:5]
    templates.append({
        'name': 'Ultimate Ball-Hogs',
        'description': 'Highest usage rates ever - one ball, five alphas',
        'roster': usage_team,
        'metrics': calculate_team_metrics(usage_team)
    })
    
    return templates

def save_team_builder_data(filename='team_builder_data.json'):
    """Save team builder data to JSON for frontend"""
    players = load_players_with_salaries()
    templates = get_historical_teams()
    
    # Get optimal roster
    optimal_roster, optimal_metrics = optimize_roster_greedy(players)
    
    data = {
        'players': players,
        'templates': [
            {
                'name': t['name'],
                'description': t['description'],
                'roster': [p['id'] for p in t['roster']],
                'metrics': t['metrics']
            }
            for t in templates
        ],
        'optimal': {
            'roster': [p['id'] for p in optimal_roster],
            'metrics': optimal_metrics
        },
        'config': {
            'salary_cap': SALARY_CAP,
            'roster_size': ROSTER_SIZE
        }
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved team builder data to {filepath}")
    print(f"   - {len(players)} players loaded")
    print(f"   - {len(templates)} team templates")
    print(f"   - Optimal team: {optimal_metrics['total_pvr']:.2f} PVR, ${optimal_metrics['total_salary']:,}")
    
    return data

if __name__ == '__main__':
    print("🏀 TAYLOR VECTOR TERMINAL - All-Time Team Builder")
    print("=" * 80)
    
    # Generate team builder data
    data = save_team_builder_data()
    
    print("\n📊 Sample Optimal Team:")
    print("-" * 80)
    
    players = {p['id']: p for p in data['players']}
    optimal_roster = [players[pid] for pid in data['optimal']['roster']]
    
    for i, player in enumerate(optimal_roster, 1):
        print(f"{i}. {player['name']} ({player['season']})")
        print(f"   PVR: {player['pvr']:.2f} | TUSG: {player['tusg']:.1f}% | Salary: ${player['salary']:,}")
        print(f"   Stats: {player['ppg']:.1f} PPG, {player['apg']:.1f} APG, {player['mpg']:.1f} MPG")
    
    print(f"\n📈 Team Metrics:")
    print(f"   Total PVR: {data['optimal']['metrics']['total_pvr']:.2f}")
    print(f"   Avg TUSG%: {data['optimal']['metrics']['avg_tusg']:.2f}%")
    print(f"   Total Salary: ${data['optimal']['metrics']['total_salary']:,}")
    print(f"   Cap Space: ${data['optimal']['metrics']['cap_space']:,}")
    
    print("\n🏆 Historical Team Templates:")
    print("-" * 80)
    for template in data['templates']:
        print(f"\n{template['name']}")
        print(f"   {template['description']}")
        print(f"   Total PVR: {template['metrics']['total_pvr']:.2f}")
        print(f"   Avg TUSG: {template['metrics']['avg_tusg']:.2f}%")
        print(f"   Salary: ${template['metrics']['total_salary']:,}")
    
    print("\n" + "=" * 80)
