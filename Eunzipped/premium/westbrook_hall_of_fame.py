"""
WESTBROOK RULE HALL OF FAME
Historical impact showcase of the AST/TOV multiplier rule
Identifies players "exposed" and "validated" by the rule
"""

import json
from datetime import datetime
import os

HISTORICAL_PACE = {
    range(1950, 1970): 115.0,
    range(1970, 1990): 107.0,
    range(1990, 2010): 95.0,
    range(2010, 2020): 98.0,
    range(2020, 2030): 99.5
}

def get_era_pace(season):
    """Get average NBA pace for a given season"""
    for year_range, pace in HISTORICAL_PACE.items():
        if season in year_range:
            return pace
    return 99.5

def calculate_pvr(stats, multiplier=None):
    """
    Calculate PVR for a player
    If multiplier is None, use AST/TOV-based rule
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
    
    if multiplier is None:
        multiplier = 2.3 if ast_tov_ratio > 1.8 else 1.8
    
    numerator = pts + (ast * multiplier)
    denominator = fga + tov + (0.44 * fta) + ast
    
    if denominator == 0:
        return 0.0, ast_tov_ratio, multiplier
    
    pvr = ((numerator / denominator) - 1.00) * 100
    return round(pvr, 2), round(ast_tov_ratio, 2), multiplier

HALL_OF_FAME_SEASONS = [
    {
        'name': 'Michael Jordan',
        'season': '1987-88',
        'year': 1988,
        'stats': {'mpg': 40.4, 'ppg': 35.0, 'apg': 5.9, 'fga': 27.8, 'fta': 11.9, 'tov': 3.1},
        'context': 'Peak scoring dominance with moderate playmaking'
    },
    {
        'name': 'LeBron James',
        'season': '2012-13',
        'year': 2013,
        'stats': {'mpg': 37.9, 'ppg': 26.8, 'apg': 7.3, 'fga': 17.8, 'fta': 7.3, 'tov': 3.0},
        'context': 'Elite efficiency with strong assist numbers'
    },
    {
        'name': 'Kobe Bryant',
        'season': '2005-06',
        'year': 2006,
        'stats': {'mpg': 41.0, 'ppg': 35.4, 'apg': 4.5, 'fga': 27.2, 'fta': 10.2, 'tov': 3.1},
        'context': 'Historic volume scoring, lower assist rate'
    },
    {
        'name': 'Magic Johnson',
        'season': '1986-87',
        'year': 1987,
        'stats': {'mpg': 36.3, 'ppg': 23.9, 'apg': 12.2, 'fga': 17.7, 'fta': 5.4, 'tov': 3.8},
        'context': 'Revolutionary playmaking with elite AST/TOV ratio'
    },
    {
        'name': 'Larry Bird',
        'season': '1987-88',
        'year': 1988,
        'stats': {'mpg': 37.9, 'ppg': 29.9, 'apg': 6.1, 'fga': 19.1, 'fta': 5.3, 'tov': 2.9},
        'context': 'Complete game with strong efficiency'
    },
    {
        'name': 'Stephen Curry',
        'season': '2015-16',
        'year': 2016,
        'stats': {'mpg': 34.2, 'ppg': 30.1, 'apg': 6.7, 'fga': 20.2, 'fta': 5.1, 'tov': 3.3},
        'context': 'Revolutionary shooting with solid playmaking'
    },
    {
        'name': 'Nikola Jokić',
        'season': '2021-22',
        'year': 2022,
        'stats': {'mpg': 33.5, 'ppg': 27.1, 'apg': 7.9, 'fga': 18.0, 'fta': 5.5, 'tov': 3.0},
        'context': 'Modern center playmaking excellence'
    },
    {
        'name': 'Russell Westbrook',
        'season': '2016-17',
        'year': 2017,
        'stats': {'mpg': 34.6, 'ppg': 31.6, 'apg': 10.4, 'fga': 24.0, 'fta': 10.4, 'tov': 5.4},
        'context': 'Historic triple-double season with high volume'
    },
    {
        'name': 'James Harden',
        'season': '2018-19',
        'year': 2019,
        'stats': {'mpg': 36.8, 'ppg': 36.1, 'apg': 7.5, 'fga': 24.5, 'fta': 11.0, 'tov': 5.0},
        'context': 'Extreme volume scoring with decent playmaking'
    },
    {
        'name': 'John Stockton',
        'season': '1989-90',
        'year': 1990,
        'stats': {'mpg': 37.4, 'ppg': 17.2, 'apg': 14.5, 'fga': 11.5, 'fta': 3.8, 'tov': 2.8},
        'context': 'All-time assist leader with elite ball security'
    },
    {
        'name': 'Steve Nash',
        'season': '2006-07',
        'year': 2007,
        'stats': {'mpg': 35.3, 'ppg': 18.6, 'apg': 11.6, 'fga': 12.3, 'fta': 3.9, 'tov': 2.7},
        'context': 'Seven Seconds or Less architect with pristine efficiency'
    },
    {
        'name': 'Chris Paul',
        'season': '2008-09',
        'year': 2009,
        'stats': {'mpg': 38.5, 'ppg': 22.8, 'apg': 11.0, 'fga': 15.5, 'fta': 5.0, 'tov': 2.7},
        'context': 'Point God at his peak with elite decision-making'
    },
    {
        'name': 'Oscar Robertson',
        'season': '1963-64',
        'year': 1964,
        'stats': {'mpg': 45.3, 'ppg': 31.4, 'apg': 11.0, 'fga': 26.2, 'fta': 11.5, 'tov': 4.2},
        'context': 'Original triple-double machine in fast-paced era'
    },
    {
        'name': 'Wilt Chamberlain',
        'season': '1961-62',
        'year': 1962,
        'stats': {'mpg': 48.5, 'ppg': 50.4, 'apg': 2.4, 'fga': 39.5, 'fta': 17.0, 'tov': 5.0},
        'context': 'Legendary volume scoring with minimal playmaking'
    },
    {
        'name': 'Kevin Durant',
        'season': '2013-14',
        'year': 2014,
        'stats': {'mpg': 38.5, 'ppg': 32.0, 'apg': 5.5, 'fga': 20.8, 'fta': 9.2, 'tov': 3.5},
        'context': 'Elite scorer with secondary playmaking'
    },
    {
        'name': 'Giannis Antetokounmpo',
        'season': '2019-20',
        'year': 2020,
        'stats': {'mpg': 30.4, 'ppg': 29.5, 'apg': 5.6, 'fga': 19.7, 'fta': 10.5, 'tov': 3.1},
        'context': 'Modern athletic dominance with developing playmaking'
    },
    {
        'name': 'Allen Iverson',
        'season': '2005-06',
        'year': 2006,
        'stats': {'mpg': 43.1, 'ppg': 33.0, 'apg': 7.4, 'fga': 25.3, 'fta': 11.3, 'tov': 3.3},
        'context': 'Volume scoring with solid assist numbers'
    },
    {
        'name': 'Dwyane Wade',
        'season': '2008-09',
        'year': 2009,
        'stats': {'mpg': 38.6, 'ppg': 30.2, 'apg': 7.5, 'fga': 21.0, 'fta': 10.8, 'tov': 3.4},
        'context': 'Athletic peak with strong all-around game'
    },
    {
        'name': 'Kawhi Leonard',
        'season': '2016-17',
        'year': 2017,
        'stats': {'mpg': 33.4, 'ppg': 25.5, 'apg': 3.5, 'fga': 17.4, 'fta': 6.2, 'tov': 1.8},
        'context': 'Efficient two-way star with elite ball security'
    },
    {
        'name': 'Luka Dončić',
        'season': '2022-23',
        'year': 2023,
        'stats': {'mpg': 36.2, 'ppg': 32.4, 'apg': 8.6, 'fga': 21.6, 'fta': 8.2, 'tov': 3.6},
        'context': 'Modern triple-threat with elite playmaking'
    },
    {
        'name': 'Dirk Nowitzki',
        'season': '2006-07',
        'year': 2007,
        'stats': {'mpg': 36.2, 'ppg': 24.6, 'apg': 3.4, 'fga': 17.7, 'fta': 6.7, 'tov': 1.9},
        'context': 'Elite scoring big with minimal turnovers'
    },
    {
        'name': 'Shaquille O\'Neal',
        'season': '1999-00',
        'year': 2000,
        'stats': {'mpg': 40.0, 'ppg': 29.7, 'apg': 3.8, 'fga': 19.0, 'fta': 13.1, 'tov': 2.8},
        'context': 'Dominant interior force with decent efficiency'
    },
    {
        'name': 'Tim Duncan',
        'season': '2001-02',
        'year': 2002,
        'stats': {'mpg': 40.6, 'ppg': 25.5, 'apg': 3.7, 'fga': 18.8, 'fta': 6.7, 'tov': 2.5},
        'context': 'Two-way excellence with fundamental soundness'
    },
    {
        'name': 'Hakeem Olajuwon',
        'season': '1992-93',
        'year': 1993,
        'stats': {'mpg': 39.2, 'ppg': 26.1, 'apg': 3.5, 'fga': 20.5, 'fta': 9.2, 'tov': 3.0},
        'context': 'Defensive anchor with elite interior scoring'
    },
    {
        'name': 'David Robinson',
        'season': '1993-94',
        'year': 1994,
        'stats': {'mpg': 40.5, 'ppg': 29.8, 'apg': 4.8, 'fga': 20.3, 'fta': 10.0, 'tov': 3.2},
        'context': 'Athletic big man with strong all-around stats'
    }
]

def generate_hall_of_fame():
    """Generate Hall of Fame inductees with rule impact analysis"""
    
    exposed_wing = []  # Low AST/TOV ratio (< 1.8) - benefited from lenient 1.8x multiplier
    validated_wing = []  # High AST/TOV ratio (> 1.8) - earned 2.3x multiplier
    
    for player_data in HALL_OF_FAME_SEASONS:
        stats = player_data['stats']
        
        # Calculate PVR with different scenarios
        pvr_actual, ast_tov_ratio, multiplier_used = calculate_pvr(stats)
        pvr_no_multiplier, _, _ = calculate_pvr(stats, multiplier=1.0)
        pvr_max_multiplier, _, _ = calculate_pvr(stats, multiplier=2.3)
        
        # Calculate rule impact
        if multiplier_used == 1.8:
            # "Exposed" player - needed the 1.8x multiplier
            rule_impact = pvr_actual - pvr_no_multiplier
            category = 'exposed'
        else:
            # "Validated" player - earned the 2.3x multiplier
            rule_impact = pvr_actual - pvr_no_multiplier
            category = 'validated'
        
        inductee = {
            'name': player_data['name'],
            'season': player_data['season'],
            'year': player_data['year'],
            'context': player_data['context'],
            'ppg': stats['ppg'],
            'apg': stats['apg'],
            'tov': stats['tov'],
            'mpg': stats['mpg'],
            'ast_tov_ratio': ast_tov_ratio,
            'pvr_actual': pvr_actual,
            'pvr_no_multiplier': pvr_no_multiplier,
            'pvr_max_multiplier': pvr_max_multiplier,
            'multiplier_used': multiplier_used,
            'rule_impact': round(rule_impact, 2),
            'category': category,
            'era_pace': get_era_pace(player_data['year'])
        }
        
        if category == 'exposed':
            exposed_wing.append(inductee)
        else:
            validated_wing.append(inductee)
    
    # Sort each wing
    exposed_wing.sort(key=lambda x: x['ast_tov_ratio'])  # Worst AST/TOV first
    validated_wing.sort(key=lambda x: x['ast_tov_ratio'], reverse=True)  # Best AST/TOV first
    
    # Calculate timeline data (AST/TOV trends by decade)
    timeline = calculate_ast_tov_timeline()
    
    # Generate insights
    insights = generate_insights(exposed_wing, validated_wing)
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_inductees': len(HALL_OF_FAME_SEASONS),
        'exposed_count': len(exposed_wing),
        'validated_count': len(validated_wing),
        'exposed_wing': exposed_wing,
        'validated_wing': validated_wing,
        'timeline': timeline,
        'insights': insights
    }
    
    return output

def calculate_ast_tov_timeline():
    """Calculate AST/TOV ratio trends by decade"""
    decades = {
        '1960s': [],
        '1970s': [],
        '1980s': [],
        '1990s': [],
        '2000s': [],
        '2010s': [],
        '2020s': []
    }
    
    for player in HALL_OF_FAME_SEASONS:
        year = player['year']
        stats = player['stats']
        
        ast = stats['apg']
        tov = stats['tov']
        
        if tov > 0:
            ratio = round(ast / tov, 2)
        else:
            ratio = ast
        
        if 1960 <= year < 1970:
            decades['1960s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
        elif 1970 <= year < 1980:
            decades['1970s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
        elif 1980 <= year < 1990:
            decades['1980s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
        elif 1990 <= year < 2000:
            decades['1990s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
        elif 2000 <= year < 2010:
            decades['2000s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
        elif 2010 <= year < 2020:
            decades['2010s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
        elif 2020 <= year < 2030:
            decades['2020s'].append({'name': player['name'], 'ratio': ratio, 'year': year})
    
    timeline_summary = {}
    for decade, players in decades.items():
        if players:
            avg_ratio = sum(p['ratio'] for p in players) / len(players)
            timeline_summary[decade] = {
                'avg_ast_tov': round(avg_ratio, 2),
                'sample_size': len(players),
                'players': players
            }
    
    return timeline_summary

def generate_insights(exposed_wing, validated_wing):
    """Generate key insights about the rule's impact"""
    
    # Most exposed player
    most_exposed = min(exposed_wing, key=lambda x: x['ast_tov_ratio']) if exposed_wing else None
    
    # Most validated player
    most_validated = max(validated_wing, key=lambda x: x['ast_tov_ratio']) if validated_wing else None
    
    # Biggest rule beneficiary
    all_players = exposed_wing + validated_wing
    biggest_impact = max(all_players, key=lambda x: x['rule_impact']) if all_players else None
    
    # Average impact by category
    avg_exposed_impact = sum(p['rule_impact'] for p in exposed_wing) / len(exposed_wing) if exposed_wing else 0
    avg_validated_impact = sum(p['rule_impact'] for p in validated_wing) / len(validated_wing) if validated_wing else 0
    
    return {
        'most_exposed': most_exposed,
        'most_validated': most_validated,
        'biggest_impact': biggest_impact,
        'avg_exposed_impact': round(avg_exposed_impact, 2),
        'avg_validated_impact': round(avg_validated_impact, 2),
        'rule_threshold': 1.8,
        'low_multiplier': 1.8,
        'high_multiplier': 2.3
    }

def save_hall_of_fame():
    """Generate and save Hall of Fame data to JSON"""
    data = generate_hall_of_fame()
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, 'westbrook_hall_data.json')
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("=" * 100)
    print("WESTBROOK RULE HALL OF FAME")
    print("=" * 100)
    print(f"\n📊 Total Inductees: {data['total_inductees']}")
    print(f"   - Exposed Wing: {data['exposed_count']} players")
    print(f"   - Validated Wing: {data['validated_count']} players")
    
    print("\n🔴 EXPOSED WING (Top 5 - Lowest AST/TOV Ratios)")
    print("Players who benefit from the lenient 1.8x multiplier despite poor ball security")
    print("-" * 100)
    for i, player in enumerate(data['exposed_wing'][:5], 1):
        print(f"{i}. {player['name']:25s} ({player['season']}) - AST/TOV: {player['ast_tov_ratio']:.2f} | "
              f"Rule Impact: +{player['rule_impact']:.2f} PVR")
    
    print("\n🟢 VALIDATED WING (Top 5 - Highest AST/TOV Ratios)")
    print("Elite playmakers who earned the premium 2.3x multiplier")
    print("-" * 100)
    for i, player in enumerate(data['validated_wing'][:5], 1):
        print(f"{i}. {player['name']:25s} ({player['season']}) - AST/TOV: {player['ast_tov_ratio']:.2f} | "
              f"Rule Impact: +{player['rule_impact']:.2f} PVR")
    
    print("\n💡 KEY INSIGHTS:")
    print("-" * 100)
    insights = data['insights']
    if insights['most_exposed']:
        print(f"Most Exposed: {insights['most_exposed']['name']} (AST/TOV: {insights['most_exposed']['ast_tov_ratio']:.2f})")
    if insights['most_validated']:
        print(f"Most Validated: {insights['most_validated']['name']} (AST/TOV: {insights['most_validated']['ast_tov_ratio']:.2f})")
    if insights['biggest_impact']:
        print(f"Biggest Rule Impact: {insights['biggest_impact']['name']} (+{insights['biggest_impact']['rule_impact']:.2f} PVR)")
    
    print(f"\nAverage Rule Impact:")
    print(f"  - Exposed Wing: +{insights['avg_exposed_impact']:.2f} PVR")
    print(f"  - Validated Wing: +{insights['avg_validated_impact']:.2f} PVR")
    
    print("\n📈 HISTORICAL TIMELINE (AST/TOV Trends by Decade):")
    print("-" * 100)
    for decade, data_point in sorted(data['timeline'].items()):
        print(f"{decade}: Avg AST/TOV = {data_point['avg_ast_tov']:.2f} ({data_point['sample_size']} players)")
    
    print(f"\n✅ Data saved to: {output_file}")
    print("=" * 100)
    
    return output_file

if __name__ == '__main__':
    save_hall_of_fame()
