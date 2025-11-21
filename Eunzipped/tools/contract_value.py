"""
TAYLOR VECTOR TERMINAL - Contract Value Calculator
Analyzes dollar value per PVR point to find over/underpaid players
Formula: Value Score = PVR / (Annual Salary in millions)
"""

import json
import os

NBA_CONTRACTS_2024_25 = [
    {"player": "Stephen Curry", "team": "GSW", "salary": 55.76, "ppg": 30.1, "apg": 6.7, "fga": 20.0, "tov": 3.1, "fta": 5.3, "pvr": 40.27},
    {"player": "Nikola Jokić", "team": "DEN", "salary": 51.42, "ppg": 27.1, "apg": 7.9, "fga": 18.4, "tov": 3.0, "fta": 5.8, "pvr": 44.54},
    {"player": "Joel Embiid", "team": "PHI", "salary": 51.42, "ppg": 33.1, "apg": 4.2, "fga": 20.1, "tov": 3.4, "fta": 11.7, "pvr": 22.15},
    {"player": "Bradley Beal", "team": "PHX", "salary": 50.20, "ppg": 23.2, "apg": 5.1, "fga": 18.4, "tov": 3.2, "fta": 4.8, "pvr": 12.34},
    {"player": "Damian Lillard", "team": "MIL", "salary": 48.79, "ppg": 32.2, "apg": 7.3, "fga": 21.8, "tov": 4.0, "fta": 8.0, "pvr": 24.56},
    {"player": "Kawhi Leonard", "team": "LAC", "salary": 48.79, "ppg": 26.2, "apg": 5.2, "fga": 19.0, "tov": 2.0, "fta": 5.6, "pvr": 28.33},
    {"player": "Giannis Antetokounmpo", "team": "MIL", "salary": 48.00, "ppg": 29.5, "apg": 5.6, "fga": 20.5, "tov": 3.7, "fta": 10.3, "pvr": 28.35},
    {"player": "LeBron James", "team": "LAL", "salary": 48.73, "ppg": 26.8, "apg": 7.3, "fga": 19.0, "tov": 3.5, "fta": 7.5, "pvr": 39.21},
    {"player": "Kevin Durant", "team": "PHX", "salary": 47.65, "ppg": 32.0, "apg": 5.5, "fga": 21.0, "tov": 3.8, "fta": 7.8, "pvr": 23.79},
    {"player": "Paul George", "team": "LAC", "salary": 45.64, "ppg": 23.8, "apg": 5.1, "fga": 17.8, "tov": 3.4, "fta": 5.2, "pvr": 19.45},
    {"player": "Anthony Davis", "team": "LAL", "salary": 43.22, "ppg": 25.9, "apg": 3.1, "fga": 18.6, "tov": 2.1, "fta": 7.3, "pvr": 18.67},
    {"player": "Jaylen Brown", "team": "BOS", "salary": 49.21, "ppg": 26.6, "apg": 3.5, "fga": 19.0, "tov": 2.8, "fta": 6.0, "pvr": 16.78},
    {"player": "Devin Booker", "team": "PHX", "salary": 49.21, "ppg": 27.8, "apg": 6.9, "fga": 19.6, "tov": 3.1, "fta": 5.6, "pvr": 22.45},
    {"player": "Karl-Anthony Towns", "team": "MIN", "salary": 49.21, "ppg": 24.6, "apg": 4.4, "fga": 17.0, "tov": 2.9, "fta": 5.3, "pvr": 20.12},
    {"player": "Luka Dončić", "team": "DAL", "salary": 43.03, "ppg": 32.4, "apg": 8.0, "fga": 21.6, "tov": 3.6, "fta": 8.2, "pvr": 32.67},
    {"player": "Trae Young", "team": "ATL", "salary": 43.03, "ppg": 26.2, "apg": 10.2, "fga": 20.4, "tov": 4.1, "fta": 7.4, "pvr": 28.90},
    {"player": "Rudy Gobert", "team": "MIN", "salary": 41.00, "ppg": 15.6, "apg": 1.2, "fga": 7.8, "tov": 1.5, "fta": 3.6, "pvr": 8.45},
    {"player": "Jimmy Butler", "team": "MIA", "salary": 48.80, "ppg": 22.9, "apg": 5.3, "fga": 16.2, "tov": 1.4, "fta": 7.5, "pvr": 25.33},
    {"player": "Tobias Harris", "team": "PHI", "salary": 39.27, "ppg": 17.2, "apg": 3.1, "fga": 12.8, "tov": 1.3, "fta": 3.4, "pvr": 10.56},
    {"player": "Khris Middleton", "team": "MIL", "salary": 40.38, "ppg": 20.1, "apg": 5.4, "fga": 15.1, "tov": 2.5, "fta": 4.3, "pvr": 18.22},
    {"player": "Jamal Murray", "team": "DEN", "salary": 36.02, "ppg": 21.2, "apg": 6.2, "fga": 16.0, "tov": 2.7, "fta": 4.8, "pvr": 23.45},
    {"player": "Pascal Siakam", "team": "TOR", "salary": 37.89, "ppg": 24.2, "apg": 5.8, "fga": 18.0, "tov": 2.5, "fta": 5.9, "pvr": 21.34},
    {"player": "Ben Simmons", "team": "BKN", "salary": 37.89, "ppg": 11.9, "apg": 6.9, "fga": 9.5, "tov": 3.3, "fta": 3.9, "pvr": 12.67},
    {"player": "Fred VanVleet", "team": "HOU", "salary": 42.85, "ppg": 17.4, "apg": 6.2, "fga": 14.3, "tov": 1.8, "fta": 3.9, "pvr": 17.89},
    {"player": "CJ McCollum", "team": "NOP", "salary": 33.33, "ppg": 20.9, "apg": 4.4, "fga": 17.0, "tov": 2.3, "fta": 3.7, "pvr": 14.56},
    {"player": "Zach LaVine", "team": "CHI", "salary": 43.03, "ppg": 24.8, "apg": 4.2, "fga": 18.9, "tov": 3.4, "fta": 5.5, "pvr": 15.67},
    {"player": "Draymond Green", "team": "GSW", "salary": 25.81, "ppg": 8.5, "apg": 6.8, "fga": 7.4, "tov": 2.8, "fta": 2.0, "pvr": 22.45},
    {"player": "Klay Thompson", "team": "GSW", "salary": 43.22, "ppg": 21.9, "apg": 2.4, "fga": 17.0, "tov": 1.7, "fta": 2.5, "pvr": 8.34},
    {"player": "Tyler Herro", "team": "MIA", "salary": 27.00, "ppg": 20.7, "apg": 5.3, "fga": 16.5, "tov": 2.5, "fta": 4.8, "pvr": 16.78},
    {"player": "Andrew Wiggins", "team": "GSW", "salary": 33.62, "ppg": 17.1, "apg": 2.2, "fga": 12.9, "tov": 1.3, "fta": 3.2, "pvr": 7.89},
    {"player": "Domantas Sabonis", "team": "SAC", "salary": 30.75, "ppg": 19.1, "apg": 7.3, "fga": 13.0, "tov": 3.4, "fta": 5.0, "pvr": 24.56},
    {"player": "Kristaps Porziņģis", "team": "BOS", "salary": 36.02, "ppg": 20.1, "apg": 2.7, "fga": 14.0, "tov": 1.5, "fta": 4.7, "pvr": 12.34},
    {"player": "De'Aaron Fox", "team": "SAC", "salary": 34.85, "ppg": 25.0, "apg": 6.1, "fga": 19.0, "tov": 2.8, "fta": 6.9, "pvr": 21.45},
    {"player": "Bam Adebayo", "team": "MIA", "salary": 34.85, "ppg": 19.1, "apg": 3.4, "fga": 13.5, "tov": 2.2, "fta": 5.9, "pvr": 16.78},
    {"player": "Jrue Holiday", "team": "BOS", "salary": 36.86, "ppg": 19.3, "apg": 7.4, "fga": 13.5, "tov": 2.6, "fta": 4.5, "pvr": 24.12},
    {"player": "Julius Randle", "team": "NYK", "salary": 29.46, "ppg": 25.1, "apg": 4.1, "fga": 17.9, "tov": 3.0, "fta": 6.2, "pvr": 16.45},
    {"player": "Jayson Tatum", "team": "BOS", "salary": 34.85, "ppg": 30.1, "apg": 4.6, "fga": 21.9, "tov": 2.9, "fta": 7.2, "pvr": 18.56},
    {"player": "Donovan Mitchell", "team": "CLE", "salary": 32.60, "ppg": 28.3, "apg": 4.4, "fga": 20.2, "tov": 2.7, "fta": 6.5, "pvr": 17.89},
    {"player": "Brandon Ingram", "team": "NOP", "salary": 36.02, "ppg": 24.7, "apg": 5.8, "fga": 18.9, "tov": 3.2, "fta": 5.8, "pvr": 19.23},
    {"player": "Shai Gilgeous-Alexander", "team": "OKC", "salary": 30.91, "ppg": 30.1, "apg": 5.5, "fga": 20.4, "tov": 2.8, "fta": 8.8, "pvr": 26.78},
    {"player": "LaMelo Ball", "team": "CHA", "salary": 35.09, "ppg": 23.3, "apg": 8.4, "fga": 20.1, "tov": 5.1, "fta": 5.3, "pvr": 20.45},
    {"player": "Tyrese Haliburton", "team": "IND", "salary": 29.67, "ppg": 20.7, "apg": 10.4, "fga": 15.3, "tov": 2.5, "fta": 4.6, "pvr": 32.56},
    {"player": "Anthony Edwards", "team": "MIN", "salary": 42.18, "ppg": 24.6, "apg": 5.2, "fga": 19.6, "tov": 3.3, "fta": 7.5, "pvr": 18.90},
    {"player": "Zion Williamson", "team": "NOP", "salary": 39.15, "ppg": 26.0, "apg": 4.6, "fga": 18.1, "tov": 3.7, "fta": 8.0, "pvr": 20.67},
    {"player": "Ja Morant", "team": "MEM", "salary": 33.48, "ppg": 26.2, "apg": 8.1, "fga": 20.0, "tov": 3.4, "fta": 7.4, "pvr": 24.34},
    {"player": "Paolo Banchero", "team": "ORL", "salary": 11.06, "ppg": 20.0, "apg": 3.9, "fga": 15.4, "tov": 2.8, "fta": 5.7, "pvr": 14.56},
    {"player": "Victor Wembanyama", "team": "SAS", "salary": 12.16, "ppg": 21.4, "apg": 3.9, "fga": 15.8, "tov": 3.7, "fta": 5.5, "pvr": 16.89},
    {"player": "Chet Holmgren", "team": "OKC", "salary": 10.11, "ppg": 16.5, "apg": 2.9, "fga": 11.9, "tov": 1.9, "fta": 3.3, "pvr": 15.34},
    {"player": "Scoot Henderson", "team": "POR", "salary": 9.70, "ppg": 14.0, "apg": 5.4, "fga": 12.8, "tov": 3.5, "fta": 3.7, "pvr": 11.23},
    {"player": "Jaren Jackson Jr.", "team": "MEM", "salary": 26.27, "ppg": 18.6, "apg": 1.6, "fga": 14.0, "tov": 1.6, "fta": 4.4, "pvr": 8.90},
    {"player": "Scottie Barnes", "team": "TOR", "salary": 36.48, "ppg": 19.9, "apg": 5.8, "fga": 15.3, "tov": 2.0, "fta": 4.8, "pvr": 20.45},
    {"player": "Alperen Şengün", "team": "HOU", "salary": 17.50, "ppg": 21.1, "apg": 5.0, "fga": 14.2, "tov": 3.3, "fta": 5.8, "pvr": 20.12},
    {"player": "Mikal Bridges", "team": "BKN", "salary": 23.30, "ppg": 19.6, "apg": 3.3, "fga": 14.7, "tov": 1.6, "fta": 3.4, "pvr": 12.78},
    {"player": "Evan Mobley", "team": "CLE", "salary": 36.49, "ppg": 16.2, "apg": 2.8, "fga": 11.5, "tov": 1.5, "fta": 3.7, "pvr": 13.45},
]

def calculate_pvr(player_data):
    """Calculate PVR for a player"""
    pts = player_data['ppg']
    ast = player_data['apg']
    fga = player_data['fga']
    tov = player_data['tov']
    fta = player_data['fta']
    
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

def calculate_contract_values():
    """
    Calculate contract value for all players
    Value Score = PVR / (Annual Salary in millions)
    Higher score = Better value
    """
    results = []
    
    for player in NBA_CONTRACTS_2024_25:
        pvr = player.get('pvr', calculate_pvr(player))
        salary = player['salary']
        
        if salary == 0:
            value_score = 0
            dollars_per_pvr = 0
        else:
            value_score = round(pvr / salary, 4)
            dollars_per_pvr = round(salary / pvr, 2) if pvr > 0 else 999.99
        
        if dollars_per_pvr < 1.5:
            classification = "Elite Value"
            tier_color = "#22c55e"
        elif dollars_per_pvr < 3.0:
            classification = "Fair"
            tier_color = "#fbbf24"
        else:
            classification = "Overpaid"
            tier_color = "#ef4444"
        
        results.append({
            'player': player['player'],
            'team': player['team'],
            'salary': salary,
            'ppg': player['ppg'],
            'apg': player['apg'],
            'fga': player['fga'],
            'tov': player['tov'],
            'fta': player['fta'],
            'pvr': pvr,
            'value_score': value_score,
            'dollars_per_pvr': dollars_per_pvr,
            'classification': classification,
            'tier_color': tier_color
        })
    
    results.sort(key=lambda x: x['value_score'], reverse=True)
    
    for idx, player in enumerate(results, 1):
        player['value_rank'] = idx
    
    return results

def save_results(filename='contract_value_results.json'):
    """Save contract analysis results to JSON file"""
    results = calculate_contract_values()
    
    output = {
        'last_updated': '2024-11-19',
        'total_players': len(results),
        'players': results,
        'classification_rules': {
            'elite_value': '<$1.5M per PVR',
            'fair': '$1.5-3M per PVR',
            'overpaid': '>$3M per PVR'
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved contract value analysis to {filename}")
    return results

if __name__ == '__main__':
    results = save_results()
    
    print("\n💰 CONTRACT VALUE ANALYSIS")
    print("=" * 100)
    print(f"Formula: Value Score = PVR / (Annual Salary in millions)")
    print("=" * 100)
    
    print("\n🏆 TOP 10 BEST VALUE CONTRACTS")
    print("-" * 100)
    for player in results[:10]:
        print(f"{player['value_rank']:2d}. {player['player']:25s} | "
              f"${player['salary']:.2f}M | PVR: {player['pvr']:6.2f} | "
              f"${player['dollars_per_pvr']:6.2f}M/PVR | {player['classification']}")
    
    print("\n💸 TOP 10 WORST VALUE CONTRACTS (Most Overpaid)")
    print("-" * 100)
    worst = sorted(results, key=lambda x: x['dollars_per_pvr'], reverse=True)
    for player in worst[:10]:
        print(f"{player['value_rank']:2d}. {player['player']:25s} | "
              f"${player['salary']:.2f}M | PVR: {player['pvr']:6.2f} | "
              f"${player['dollars_per_pvr']:6.2f}M/PVR | {player['classification']}")
    
    print("\n📊 CLASSIFICATION BREAKDOWN")
    print("-" * 100)
    elite = len([p for p in results if p['classification'] == 'Elite Value'])
    fair = len([p for p in results if p['classification'] == 'Fair'])
    overpaid = len([p for p in results if p['classification'] == 'Overpaid'])
    
    print(f"🌟 Elite Value (<$1.5M per PVR): {elite} players")
    print(f"⚖️  Fair ($1.5-3M per PVR): {fair} players")
    print(f"💸 Overpaid (>$3M per PVR): {overpaid} players")
    
    print("\n💡 KEY INSIGHTS:")
    print("-" * 100)
    best = results[0]
    print(f"Best Value: {best['player']} (${best['salary']:.2f}M, {best['pvr']:.2f} PVR) = ${best['dollars_per_pvr']:.2f}M per PVR - {best['classification'].upper()}")
    
    jokic = next((p for p in results if 'Jokić' in p['player']), None)
    if jokic:
        print(f"Nikola Jokić: ${jokic['salary']:.2f}M, {jokic['pvr']:.2f} PVR = ${jokic['dollars_per_pvr']:.2f}M per PVR - {jokic['classification'].upper()}")
    
    curry = next((p for p in results if 'Curry' in p['player']), None)
    if curry:
        print(f"Stephen Curry: ${curry['salary']:.2f}M, {curry['pvr']:.2f} PVR = ${curry['dollars_per_pvr']:.2f}M per PVR - {curry['classification'].upper()}")
