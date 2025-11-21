"""
TAYLOR VECTOR TERMINAL - Contract Value Calculator
Analyzes if NBA players are overpaid/underpaid based on PVR
Formula: Value Score = PVR / (Salary in millions)
Higher score = Better value
"""

import json
import os

# Team pace data (possessions per 48 min) for 2024-25 season
TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

# NBA 2024-25 Player Data: Top paid players with stats and positions
PLAYER_CONTRACTS = [
    # Top tier salaries $48M+
    {'name': 'Stephen Curry', 'team': 'GSW', 'position': 'PG', 'salary': 55761216, 'stats': {'mpg': 32.5, 'ppg': 26.4, 'apg': 5.1, 'fga': 19.9, 'fta': 5.6, 'tov': 2.8}},
    {'name': 'Nikola Jokić', 'team': 'DEN', 'position': 'C', 'salary': 51415938, 'stats': {'mpg': 37.2, 'ppg': 30.1, 'apg': 10.1, 'fga': 19.8, 'fta': 7.9, 'tov': 3.2}},
    {'name': 'Joel Embiid', 'team': 'PHI', 'position': 'C', 'salary': 51415938, 'stats': {'mpg': 31.8, 'ppg': 25.8, 'apg': 3.6, 'fga': 17.2, 'fta': 9.4, 'tov': 3.4}},
    {'name': 'Kevin Durant', 'team': 'PHX', 'position': 'PF', 'salary': 51179020, 'stats': {'mpg': 37.5, 'ppg': 27.6, 'apg': 5.0, 'fga': 19.1, 'fta': 6.7, 'tov': 3.2}},
    {'name': 'Bradley Beal', 'team': 'PHX', 'position': 'SG', 'salary': 50203930, 'stats': {'mpg': 32.9, 'ppg': 17.8, 'apg': 3.5, 'fga': 14.6, 'fta': 3.8, 'tov': 2.1}},
    {'name': 'Devin Booker', 'team': 'PHX', 'position': 'SG', 'salary': 49205800, 'stats': {'mpg': 35.1, 'ppg': 25.0, 'apg': 6.5, 'fga': 19.5, 'fta': 5.3, 'tov': 2.6}},
    {'name': 'Jaylen Brown', 'team': 'BOS', 'position': 'SG', 'salary': 49205800, 'stats': {'mpg': 34.2, 'ppg': 23.9, 'apg': 4.8, 'fga': 18.7, 'fta': 5.5, 'tov': 2.5}},
    {'name': 'Paul George', 'team': 'PHI', 'position': 'SF', 'salary': 49205800, 'stats': {'mpg': 32.6, 'ppg': 18.4, 'apg': 5.3, 'fga': 14.8, 'fta': 4.2, 'tov': 2.4}},
    {'name': 'Kawhi Leonard', 'team': 'LAC', 'position': 'SF', 'salary': 49205800, 'stats': {'mpg': 28.7, 'ppg': 20.5, 'apg': 3.6, 'fga': 15.2, 'fta': 5.1, 'tov': 1.8}},
    {'name': 'Karl-Anthony Towns', 'team': 'NYK', 'position': 'C', 'salary': 49205800, 'stats': {'mpg': 36.4, 'ppg': 25.2, 'apg': 3.3, 'fga': 17.9, 'fta': 5.8, 'tov': 2.1}},
    {'name': 'Jimmy Butler', 'team': 'MIA', 'position': 'SF', 'salary': 48798677, 'stats': {'mpg': 33.2, 'ppg': 19.2, 'apg': 5.0, 'fga': 13.5, 'fta': 6.4, 'tov': 1.9}},
    {'name': 'Giannis Antetokounmpo', 'team': 'MIL', 'position': 'PF', 'salary': 48787676, 'stats': {'mpg': 35.2, 'ppg': 30.5, 'apg': 6.2, 'fga': 20.8, 'fta': 11.7, 'tov': 3.4}},
    {'name': 'Damian Lillard', 'team': 'MIL', 'position': 'PG', 'salary': 48787676, 'stats': {'mpg': 35.3, 'ppg': 25.7, 'apg': 7.5, 'fga': 19.2, 'fta': 6.8, 'tov': 3.1}},
    {'name': 'LeBron James', 'team': 'LAL', 'position': 'SF', 'salary': 48728845, 'stats': {'mpg': 35.3, 'ppg': 23.0, 'apg': 8.9, 'fga': 17.3, 'fta': 6.3, 'tov': 3.5}},
    
    # $43-47M tier
    {'name': 'Zach LaVine', 'team': 'CHI', 'position': 'SG', 'salary': 43031940, 'stats': {'mpg': 33.5, 'ppg': 21.7, 'apg': 4.4, 'fga': 17.8, 'fta': 4.9, 'tov': 2.4}},
    {'name': 'Luka Dončić', 'team': 'DAL', 'position': 'PG', 'salary': 43031940, 'stats': {'mpg': 37.2, 'ppg': 28.1, 'apg': 8.3, 'fga': 21.1, 'fta': 7.8, 'tov': 3.6}},
    {'name': 'Trae Young', 'team': 'ATL', 'position': 'PG', 'salary': 43031940, 'stats': {'mpg': 35.7, 'ppg': 22.0, 'apg': 11.6, 'fga': 19.3, 'fta': 6.1, 'tov': 4.1}},
    {'name': 'Anthony Davis', 'team': 'LAL', 'position': 'PF', 'salary': 43219440, 'stats': {'mpg': 35.8, 'ppg': 26.0, 'apg': 3.6, 'fga': 18.4, 'fta': 7.8, 'tov': 2.1}},
    {'name': 'Rudy Gobert', 'team': 'MIN', 'position': 'C', 'salary': 43827586, 'stats': {'mpg': 30.2, 'ppg': 10.4, 'apg': 1.6, 'fga': 6.8, 'fta': 3.8, 'tov': 1.5}},
    {'name': 'Fred VanVleet', 'team': 'HOU', 'position': 'PG', 'salary': 42846800, 'stats': {'mpg': 35.1, 'ppg': 15.6, 'apg': 6.4, 'fga': 13.5, 'fta': 3.9, 'tov': 2.7}},
    
    # $38-42M tier
    {'name': 'Khris Middleton', 'team': 'MIL', 'position': 'SF', 'salary': 31666667, 'stats': {'mpg': 26.7, 'ppg': 12.4, 'apg': 4.7, 'fga': 10.1, 'fta': 2.6, 'tov': 2.1}},
    {'name': 'Tobias Harris', 'team': 'DET', 'position': 'PF', 'salary': 39270000, 'stats': {'mpg': 31.8, 'ppg': 13.7, 'apg': 3.4, 'fga': 10.9, 'fta': 2.7, 'tov': 1.5}},
    {'name': 'Kyrie Irving', 'team': 'DAL', 'position': 'PG', 'salary': 41000000, 'stats': {'mpg': 33.1, 'ppg': 24.3, 'apg': 5.1, 'fga': 18.2, 'fta': 4.3, 'tov': 2.2}},
    {'name': 'Jamal Murray', 'team': 'DEN', 'position': 'PG', 'salary': 36016200, 'stats': {'mpg': 32.6, 'ppg': 18.2, 'apg': 5.5, 'fga': 14.8, 'fta': 3.7, 'tov': 2.1}},
    {'name': 'Bam Adebayo', 'team': 'MIA', 'position': 'C', 'salary': 34848340, 'stats': {'mpg': 33.8, 'ppg': 16.0, 'apg': 4.2, 'fga': 12.3, 'fta': 5.3, 'tov': 2.3}},
    
    # Rising stars and high-value players ($30-35M)
    {'name': 'Shai Gilgeous-Alexander', 'team': 'OKC', 'position': 'PG', 'salary': 35859950, 'stats': {'mpg': 34.1, 'ppg': 32.7, 'apg': 6.4, 'fga': 23.1, 'fta': 9.2, 'tov': 2.1}},
    {'name': 'Jayson Tatum', 'team': 'BOS', 'position': 'SF', 'salary': 34848340, 'stats': {'mpg': 36.9, 'ppg': 28.4, 'apg': 5.7, 'fga': 21.3, 'fta': 7.1, 'tov': 2.8}},
    {'name': 'Donovan Mitchell', 'team': 'CLE', 'position': 'SG', 'salary': 32600060, 'stats': {'mpg': 35.4, 'ppg': 23.2, 'apg': 4.4, 'fga': 19.1, 'fta': 5.8, 'tov': 2.7}},
    {'name': 'Anthony Edwards', 'team': 'MIN', 'position': 'SG', 'salary': 34005250, 'stats': {'mpg': 35.3, 'ppg': 25.9, 'apg': 5.1, 'fga': 20.5, 'fta': 7.1, 'tov': 2.9}},
    {'name': 'De\'Aaron Fox', 'team': 'SAC', 'position': 'PG', 'salary': 34848340, 'stats': {'mpg': 36.2, 'ppg': 26.3, 'apg': 6.1, 'fga': 20.2, 'fta': 6.9, 'tov': 2.5}},
    {'name': 'Tyrese Haliburton', 'team': 'IND', 'position': 'PG', 'salary': 34004634, 'stats': {'mpg': 33.8, 'ppg': 18.7, 'apg': 8.8, 'fga': 14.1, 'fta': 4.2, 'tov': 2.3}},
    {'name': 'Ja Morant', 'team': 'MEM', 'position': 'PG', 'salary': 33479000, 'stats': {'mpg': 30.4, 'ppg': 21.2, 'apg': 7.9, 'fga': 17.5, 'fta': 6.3, 'tov': 3.2}},
    {'name': 'Tyrese Maxey', 'team': 'PHI', 'position': 'PG', 'salary': 32670690, 'stats': {'mpg': 37.9, 'ppg': 27.6, 'apg': 6.9, 'fga': 21.4, 'fta': 7.2, 'tov': 2.8}},
    {'name': 'Pascal Siakam', 'team': 'IND', 'position': 'PF', 'salary': 42296482, 'stats': {'mpg': 34.6, 'ppg': 19.4, 'apg': 4.0, 'fga': 15.7, 'fta': 4.6, 'tov': 2.2}},
    
    # Mid-tier contracts ($25-30M)
    {'name': 'Jaren Jackson Jr.', 'team': 'MEM', 'position': 'PF', 'salary': 27967034, 'stats': {'mpg': 29.6, 'ppg': 21.8, 'apg': 1.6, 'fga': 15.7, 'fta': 5.4, 'tov': 1.5}},
    {'name': 'Tyler Herro', 'team': 'MIA', 'position': 'SG', 'salary': 27000000, 'stats': {'mpg': 32.9, 'ppg': 23.8, 'apg': 5.0, 'fga': 18.5, 'fta': 5.2, 'tov': 2.6}},
    {'name': 'Julius Randle', 'team': 'MIN', 'position': 'PF', 'salary': 30935520, 'stats': {'mpg': 32.1, 'ppg': 16.8, 'apg': 3.8, 'fga': 13.6, 'fta': 4.2, 'tov': 2.4}},
    {'name': 'Jalen Brunson', 'team': 'NYK', 'position': 'PG', 'salary': 26235600, 'stats': {'mpg': 35.4, 'ppg': 26.2, 'apg': 7.2, 'fga': 19.4, 'fta': 6.8, 'tov': 2.7}},
    {'name': 'Darius Garland', 'team': 'CLE', 'position': 'PG', 'salary': 30175440, 'stats': {'mpg': 29.8, 'ppg': 17.7, 'apg': 6.9, 'fga': 13.9, 'fta': 3.8, 'tov': 2.6}},
    {'name': 'Lauri Markkanen', 'team': 'UTA', 'position': 'PF', 'salary': 18044000, 'stats': {'mpg': 32.7, 'ppg': 18.4, 'apg': 2.0, 'fga': 14.2, 'fta': 4.3, 'tov': 1.4}},
    {'name': 'DeMar DeRozan', 'team': 'SAC', 'position': 'SF', 'salary': 22000000, 'stats': {'mpg': 35.9, 'ppg': 21.8, 'apg': 4.0, 'fga': 17.1, 'fta': 6.2, 'tov': 1.8}},
    {'name': 'Brandon Ingram', 'team': 'NOP', 'position': 'SF', 'salary': 36016200, 'stats': {'mpg': 33.2, 'ppg': 22.2, 'apg': 5.2, 'fga': 17.6, 'fta': 5.4, 'tov': 2.9}},
    
    # Value contracts and breakout players ($15-25M)
    {'name': 'Mikal Bridges', 'team': 'NYK', 'position': 'SF', 'salary': 23331250, 'stats': {'mpg': 38.6, 'ppg': 17.4, 'apg': 3.2, 'fga': 14.7, 'fta': 3.1, 'tov': 1.7}},
    {'name': 'Cade Cunningham', 'team': 'DET', 'position': 'PG', 'salary': 13940580, 'stats': {'mpg': 32.8, 'ppg': 24.0, 'apg': 9.0, 'fga': 18.8, 'fta': 6.4, 'tov': 3.7}},
    {'name': 'Paolo Banchero', 'team': 'ORL', 'position': 'PF', 'salary': 13534200, 'stats': {'mpg': 33.2, 'ppg': 22.6, 'apg': 5.4, 'fga': 18.2, 'fta': 6.7, 'tov': 3.1}},
    {'name': 'Franz Wagner', 'team': 'ORL', 'position': 'SF', 'salary': 12975000, 'stats': {'mpg': 32.8, 'ppg': 24.4, 'apg': 5.6, 'fga': 18.3, 'fta': 6.1, 'tov': 2.7}},
    {'name': 'Scottie Barnes', 'team': 'TOR', 'position': 'SF', 'salary': 10130320, 'stats': {'mpg': 34.1, 'ppg': 19.6, 'apg': 6.1, 'fga': 15.8, 'fta': 5.7, 'tov': 2.8}},
    {'name': 'Evan Mobley', 'team': 'CLE', 'position': 'C', 'salary': 11475360, 'stats': {'mpg': 32.6, 'ppg': 16.5, 'apg': 2.9, 'fga': 11.8, 'fta': 4.4, 'tov': 1.8}},
    {'name': 'Alperen Şengün', 'team': 'HOU', 'position': 'C', 'salary': 5475720, 'stats': {'mpg': 32.9, 'ppg': 18.8, 'apg': 5.3, 'fga': 13.1, 'fta': 5.9, 'tov': 2.5}},
]

def calculate_player_tusg(stats, team_abbr):
    """
    Calculate TUSG% for a player
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
    """
    mp = stats.get('mpg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    team_pace = TEAM_PACE.get(team_abbr, 99.5)
    
    if mp == 0 or team_pace == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * team_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_player_pvr(stats):
    """
    Calculate PVR for a player
    PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
    Multiplier: AST/TOV ≥ 1.8 → 2.3, else 1.8
    """
    pts = stats.get('ppg', 0)
    ast = stats.get('apg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
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

def calculate_contract_value():
    """
    Calculate contract value for all players using Value Score
    Formula: Value Score = PVR / (Salary in millions)
    Higher score = Better value (more PVR per dollar spent)
    """
    results = []
    
    for player in PLAYER_CONTRACTS:
        stats = player['stats']
        pvr = calculate_player_pvr(stats)
        
        actual_salary = player['salary']
        salary_in_millions = actual_salary / 1_000_000
        
        # Calculate Value Score = PVR / Salary(M)
        # Higher score means better value
        value_score = pvr / salary_in_millions if salary_in_millions > 0 else 0
        
        # Calculate fair salary based on league average value score
        # This will be adjusted after we know the average
        
        results.append({
            'name': player['name'],
            'team': player['team'],
            'position': player['position'],
            'salary': actual_salary,
            'pvr': pvr,
            'value_score': round(value_score, 2),
            'ppg': stats['ppg'],
            'apg': stats['apg'],
            'mpg': stats['mpg']
        })
    
    # Calculate league average value score
    avg_value_score = sum(p['value_score'] for p in results) / len(results)
    
    # Calculate fair salary for each player based on average value score
    for player in results:
        # Fair Salary = PVR / Average Value Score
        fair_salary = (player['pvr'] / avg_value_score) * 1_000_000 if avg_value_score > 0 else 0
        player['fair_salary'] = round(fair_salary, 2)
        player['salary_diff'] = round(player['salary'] - fair_salary, 2)
        player['salary_diff_pct'] = round((player['salary_diff'] / fair_salary * 100) if fair_salary > 0 else 0, 2)
    
    return results, avg_value_score

def categorize_players(results):
    """
    Categorize players into Best Value, Worst Contracts, and Fair Contracts
    Based on Value Score = PVR / Salary(M)
    """
    # Sort by value score (descending) - higher is better
    sorted_by_value = sorted(results, key=lambda x: x['value_score'], reverse=True)
    
    # Best Value: Highest value scores (high PVR, low salary)
    best_value = sorted_by_value[:10]
    
    # Worst Contracts: Lowest value scores (low PVR, high salary)
    worst_contracts = sorted_by_value[-10:][::-1]
    
    # Fair Contracts: Value score close to average (within 15%)
    avg_value_score = sum(p['value_score'] for p in results) / len(results)
    fair_contracts = [
        p for p in results 
        if abs(p['value_score'] - avg_value_score) / avg_value_score <= 0.15
    ][:10]
    
    return {
        'best_value': best_value,
        'worst_contracts': worst_contracts,
        'fair_contracts': fair_contracts,
        'all_players': sorted_by_value
    }

def format_currency(amount):
    """Format number as currency"""
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.1f}K"
    return f"${amount:.0f}"

def generate_insights(categories, avg_value_score):
    """Generate insights about contract values"""
    insights = []
    
    if categories['best_value']:
        best = categories['best_value'][0]
        insight = (f"🏆 BEST VALUE: {best['name']} has a Value Score of {best['value_score']:.2f} "
                  f"(PVR: {best['pvr']:.1f}, Salary: {format_currency(best['salary'])}). "
                  f"Rookie contracts deliver elite value!")
        insights.append(insight)
    
    if categories['worst_contracts']:
        worst = categories['worst_contracts'][0]
        insight = (f"💸 WORST CONTRACT: {worst['name']} has a Value Score of {worst['value_score']:.2f} "
                  f"(PVR: {worst['pvr']:.1f}, Salary: {format_currency(worst['salary'])}). "
                  f"Max contracts can be overpays if performance drops.")
        insights.append(insight)
    
    insight = (f"📊 LEAGUE AVERAGE: Value Score = {avg_value_score:.2f}. "
              f"Players above this deliver above-average value per dollar spent.")
    insights.append(insight)
    
    # Educational insight about rookie vs max contracts
    if categories['best_value'] and categories['worst_contracts']:
        best_rookie = next((p for p in categories['best_value'] if p['salary'] < 20_000_000), None)
        if best_rookie:
            insight = (f"💡 WHY ROOKIE CONTRACTS MATTER: {best_rookie['name']} makes {format_currency(best_rookie['salary'])} "
                      f"with PVR {best_rookie['pvr']:.1f}, while some max players earn 4x more with lower PVR. "
                      f"This is why contending teams need cost-controlled talent.")
            insights.append(insight)
    
    return insights

def save_results():
    """Calculate and save contract value analysis"""
    results, avg_value_score = calculate_contract_value()
    categories = categorize_players(results)
    insights = generate_insights(categories, avg_value_score)
    
    # Get unique teams and positions for filters
    teams = sorted(list(set(p['team'] for p in results)))
    positions = sorted(list(set(p['position'] for p in results)))
    
    output = {
        'best_value': categories['best_value'],
        'worst_contracts': categories['worst_contracts'],
        'fair_contracts': categories['fair_contracts'],
        'all_players': categories['all_players'],
        'insights': insights,
        'metadata': {
            'total_players': len(results),
            'avg_salary': sum(p['salary'] for p in results) / len(results),
            'avg_pvr': sum(p['pvr'] for p in results) / len(results),
            'avg_value_score': avg_value_score,
            'teams': teams,
            'positions': positions
        }
    }
    
    # Save to JSON
    output_file = os.path.join(os.path.dirname(__file__), 'contract_calculator_results.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved contract analysis to {output_file}")
    return output

if __name__ == '__main__':
    output = save_results()
    
    print("\n💰 NBA CONTRACT VALUE CALCULATOR")
    print("=" * 100)
    print(f"Formula: Value Score = PVR / (Salary in millions)")
    print(f"Higher score = Better value")
    print("=" * 100)
    print(f"Analyzed {output['metadata']['total_players']} players")
    print(f"Average Salary: {format_currency(output['metadata']['avg_salary'])}")
    print(f"Average PVR: {output['metadata']['avg_pvr']:.2f}")
    print(f"Average Value Score: {output['metadata']['avg_value_score']:.2f}")
    
    print("\n🔥 KEY INSIGHTS:")
    print("=" * 100)
    for insight in output['insights']:
        print(f"  {insight}")
    
    print("\n💎 TOP 10 BEST VALUE CONTRACTS (Highest Value Score):")
    print("=" * 100)
    for i, player in enumerate(output['best_value'], 1):
        print(f"{i:2d}. {player['name']:25s} ({player['position']:>2s}) | "
              f"Salary: {format_currency(player['salary']):>10s} | "
              f"PVR: {player['pvr']:>6.2f} | "
              f"Value Score: {player['value_score']:>6.2f}")
    
    print("\n💸 TOP 10 WORST CONTRACTS (Lowest Value Score):")
    print("=" * 100)
    for i, player in enumerate(output['worst_contracts'], 1):
        print(f"{i:2d}. {player['name']:25s} ({player['position']:>2s}) | "
              f"Salary: {format_currency(player['salary']):>10s} | "
              f"PVR: {player['pvr']:>6.2f} | "
              f"Value Score: {player['value_score']:>6.2f}")
    
    print("\n⚖️  TOP 10 FAIR CONTRACTS (Value Score near league average):")
    print("=" * 100)
    for i, player in enumerate(output['fair_contracts'], 1):
        print(f"{i:2d}. {player['name']:25s} ({player['position']:>2s}) | "
              f"Salary: {format_currency(player['salary']):>10s} | "
              f"PVR: {player['pvr']:>6.2f} | "
              f"Value Score: {player['value_score']:>6.2f}")
