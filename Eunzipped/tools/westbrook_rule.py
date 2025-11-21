"""
WESTBROOK RULE HISTORICAL MACHINE
Analyzes AST/TOV multiplier rule impact across NBA history (1950-2025)
Identifies "broken" seasons and cross-era comparisons
"""

import json
from datetime import datetime

HISTORICAL_PACE = {
    range(1950, 1970): 115.0,
    range(1970, 1990): 107.0,
    range(1990, 2010): 95.0,
    range(2010, 2020): 98.0,
    range(2020, 2030): 99.5
}

def get_era_pace(season):
    for year_range, pace in HISTORICAL_PACE.items():
        if season in year_range:
            return pace
    return 99.5

def calculate_tusg(stats, season):
    mp = stats.get('mpg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    team_pace = get_era_pace(season)
    
    if mp == 0 or team_pace == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * team_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_pvr(stats, multiplier=None):
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

def calculate_tusg_with_modern_pace(stats, original_season, target_pace=99.5):
    mp = stats.get('mpg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    if mp == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * target_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

HISTORICAL_SEASONS = [
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
    },
    {
        'name': 'John Stockton',
        'season': '1989-90',
        'year': 1990,
        'stats': {'mpg': 37.4, 'ppg': 17.2, 'apg': 14.5, 'fga': 11.5, 'fta': 3.8, 'tov': 2.8}
    },
    {
        'name': 'Steve Nash',
        'season': '2006-07',
        'year': 2007,
        'stats': {'mpg': 35.3, 'ppg': 18.6, 'apg': 11.6, 'fga': 12.3, 'fta': 3.9, 'tov': 2.7}
    },
    {
        'name': 'Chris Paul',
        'season': '2008-09',
        'year': 2009,
        'stats': {'mpg': 38.5, 'ppg': 22.8, 'apg': 11.0, 'fga': 15.5, 'fta': 5.0, 'tov': 2.7}
    },
    {
        'name': 'Oscar Robertson',
        'season': '1963-64',
        'year': 1964,
        'stats': {'mpg': 45.3, 'ppg': 31.4, 'apg': 11.0, 'fga': 26.2, 'fta': 11.5, 'tov': 4.2}
    },
    {
        'name': 'Jerry West',
        'season': '1965-66',
        'year': 1966,
        'stats': {'mpg': 41.9, 'ppg': 31.3, 'apg': 6.1, 'fga': 25.5, 'fta': 9.8, 'tov': 3.5}
    },
    {
        'name': 'Elgin Baylor',
        'season': '1960-61',
        'year': 1961,
        'stats': {'mpg': 43.1, 'ppg': 34.8, 'apg': 5.1, 'fga': 28.6, 'fta': 11.5, 'tov': 4.0}
    },
    {
        'name': 'Julius Erving',
        'season': '1979-80',
        'year': 1980,
        'stats': {'mpg': 37.4, 'ppg': 26.9, 'apg': 4.6, 'fga': 19.7, 'fta': 8.0, 'tov': 3.1}
    },
    {
        'name': 'Hakeem Olajuwon',
        'season': '1992-93',
        'year': 1993,
        'stats': {'mpg': 39.2, 'ppg': 26.1, 'apg': 3.5, 'fga': 20.5, 'fta': 9.2, 'tov': 3.0}
    },
    {
        'name': 'David Robinson',
        'season': '1993-94',
        'year': 1994,
        'stats': {'mpg': 40.5, 'ppg': 29.8, 'apg': 4.8, 'fga': 20.3, 'fta': 10.0, 'tov': 3.2}
    },
    {
        'name': 'Kevin Garnett',
        'season': '2003-04',
        'year': 2004,
        'stats': {'mpg': 39.4, 'ppg': 24.2, 'apg': 5.0, 'fga': 19.0, 'fta': 7.1, 'tov': 2.6}
    },
    {
        'name': 'Dirk Nowitzki',
        'season': '2006-07',
        'year': 2007,
        'stats': {'mpg': 36.2, 'ppg': 24.6, 'apg': 3.4, 'fga': 17.7, 'fta': 6.7, 'tov': 1.9}
    },
    {
        'name': 'Dwyane Wade',
        'season': '2008-09',
        'year': 2009,
        'stats': {'mpg': 38.6, 'ppg': 30.2, 'apg': 7.5, 'fga': 21.0, 'fta': 10.8, 'tov': 3.4}
    },
    {
        'name': 'Allen Iverson',
        'season': '2005-06',
        'year': 2006,
        'stats': {'mpg': 43.1, 'ppg': 33.0, 'apg': 7.4, 'fga': 25.3, 'fta': 11.3, 'tov': 3.3}
    },
    {
        'name': 'Kawhi Leonard',
        'season': '2016-17',
        'year': 2017,
        'stats': {'mpg': 33.4, 'ppg': 25.5, 'apg': 3.5, 'fga': 17.4, 'fta': 6.2, 'tov': 1.8}
    },
    {
        'name': 'Luka Dončić',
        'season': '2022-23',
        'year': 2023,
        'stats': {'mpg': 36.2, 'ppg': 32.4, 'apg': 8.6, 'fga': 21.6, 'fta': 8.2, 'tov': 3.6}
    }
]

def analyze_westbrook_rule():
    results = []
    broken_seasons = []
    
    print("=" * 100)
    print("WESTBROOK RULE HISTORICAL MACHINE")
    print("Analyzing AST/TOV Multiplier Rule Impact (1950-2025)")
    print("=" * 100)
    
    for player in HISTORICAL_SEASONS:
        stats = player['stats']
        season = player['year']
        
        tusg_actual = calculate_tusg(stats, season)
        pvr_actual, ast_tov_ratio, multiplier_used = calculate_pvr(stats)
        
        pvr_always_high, _, _ = calculate_pvr(stats, multiplier=2.3)
        pvr_always_low, _, _ = calculate_pvr(stats, multiplier=1.8)
        
        tusg_modern_pace = calculate_tusg_with_modern_pace(stats, season, 99.5)
        
        pvr_delta = pvr_actual - pvr_always_low if multiplier_used == 2.3 else 0.0
        
        is_broken = ast_tov_ratio > 3.0 and tusg_actual > 25.0
        
        result = {
            'player': player['name'],
            'season': player['season'],
            'year': season,
            'era_pace': get_era_pace(season),
            'tusg_actual': tusg_actual,
            'tusg_modern_pace': tusg_modern_pace,
            'ast_tov_ratio': ast_tov_ratio,
            'multiplier_used': multiplier_used,
            'pvr_actual': pvr_actual,
            'pvr_always_high': pvr_always_high,
            'pvr_always_low': pvr_always_low,
            'pvr_delta': round(pvr_delta, 2),
            'is_broken': is_broken,
            'ppg': stats['ppg'],
            'apg': stats['apg'],
            'tov': stats['tov'],
            'fga': stats['fga'],
            'fta': stats['fta']
        }
        
        results.append(result)
        
        if is_broken:
            broken_seasons.append(result)
    
    results.sort(key=lambda x: x['pvr_delta'], reverse=True)
    
    print("\n🔥 TOP 10 'WESTBROOK RULE' BENEFICIARIES")
    print("Players who gain the most PVR from AST/TOV > 1.8 multiplier bonus")
    print("-" * 100)
    print(f"{'Rank':<6}{'Player':<25}{'Season':<12}{'AST/TOV':<10}{'PVR Gain':<12}{'Actual PVR':<12}")
    print("-" * 100)
    
    for idx, player in enumerate(results[:10], 1):
        print(f"{idx:<6}{player['player']:<25}{player['season']:<12}{player['ast_tov_ratio']:<10.2f}"
              f"{'+' + str(player['pvr_delta']):<12}{player['pvr_actual']:<12.2f}")
    
    print("\n\n💥 'BROKEN' SEASONS (AST/TOV > 3.0 + High Usage)")
    print("These seasons would have insane PVR with even higher multipliers")
    print("-" * 100)
    print(f"{'Player':<25}{'Season':<12}{'AST/TOV':<10}{'TUSG%':<10}{'PVR':<10}{'If 3.0x Mult':<15}")
    print("-" * 100)
    
    for player in broken_seasons:
        player_stats = {
            'ppg': player['ppg'],
            'apg': player['apg'],
            'tov': player['tov'],
            'fga': player['fga'],
            'fta': player['fta']
        }
        pvr_3x, _, _ = calculate_pvr(player_stats, multiplier=3.0)
        print(f"{player['player']:<25}{player['season']:<12}{player['ast_tov_ratio']:<10.2f}"
              f"{player['tusg_actual']:<10.2f}{player['pvr_actual']:<10.2f}{pvr_3x:<15.2f}")
    
    print("\n\n🕐 CROSS-ERA COMPARISONS (Modern Pace = 99.5)")
    print("How players would perform in different eras")
    print("-" * 100)
    print(f"{'Player':<25}{'Season':<12}{'Era Pace':<12}{'TUSG (Era)':<12}{'TUSG (Modern)':<15}")
    print("-" * 100)
    
    pace_changes = sorted(
        [r for r in results if abs(r['tusg_actual'] - r['tusg_modern_pace']) > 2.0],
        key=lambda x: abs(x['tusg_actual'] - x['tusg_modern_pace']),
        reverse=True
    )[:10]
    
    for player in pace_changes:
        print(f"{player['player']:<25}{player['season']:<12}{player['era_pace']:<12.1f}"
              f"{player['tusg_actual']:<12.2f}{player['tusg_modern_pace']:<15.2f}")
    
    print("\n\n📊 KEY INSIGHTS:")
    print("-" * 100)
    
    magic = [r for r in results if 'Magic' in r['player']][0]
    print(f"• Magic Johnson in {magic['season']} had AST/TOV ratio of {magic['ast_tov_ratio']}")
    print(f"  - Actual PVR: {magic['pvr_actual']}")
    print(f"  - With 2020s pace: TUSG% would be {magic['tusg_modern_pace']}% (was {magic['tusg_actual']}%)")
    
    westbrook = [r for r in results if 'Westbrook' in r['player']][0]
    print(f"\n• Westbrook's {westbrook['season']} season was unprecedented:")
    print(f"  - TUSG%: {westbrook['tusg_actual']}% (highest volume in modern era)")
    print(f"  - AST/TOV: {westbrook['ast_tov_ratio']} (just below 2.0 threshold)")
    print(f"  - If AST/TOV was 2.0: PVR would be {westbrook['pvr_always_high']} (vs actual {westbrook['pvr_actual']})")
    
    stockton = [r for r in results if 'Stockton' in r['player']][0]
    print(f"\n• John Stockton's {stockton['season']} efficiency was elite:")
    print(f"  - AST/TOV: {stockton['ast_tov_ratio']} (5.18:1 ratio)")
    print(f"  - PVR benefit from multiplier: +{stockton['pvr_delta']}")
    
    wilt = [r for r in results if 'Wilt' in r['player']][0]
    print(f"\n• Wilt's {wilt['season']} would struggle in modern era:")
    print(f"  - Era TUSG%: {wilt['tusg_actual']}% (pace: {wilt['era_pace']})")
    print(f"  - Modern TUSG%: {wilt['tusg_modern_pace']}% (pace: 99.5) - volume would be unsustainable")
    
    print("\n" + "=" * 100)
    
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'total_seasons': len(results),
        'broken_seasons_count': len(broken_seasons),
        'analysis': results,
        'broken_seasons': broken_seasons,
        'top_beneficiaries': results[:10],
        'insights': {
            'magic_johnson': {
                'season': magic['season'],
                'ast_tov_ratio': magic['ast_tov_ratio'],
                'pvr_actual': magic['pvr_actual'],
                'pvr_with_modern_pace': magic['tusg_modern_pace']
            },
            'russell_westbrook': {
                'season': westbrook['season'],
                'tusg': westbrook['tusg_actual'],
                'ast_tov_ratio': westbrook['ast_tov_ratio'],
                'pvr_actual': westbrook['pvr_actual'],
                'pvr_if_2_0_ratio': westbrook['pvr_always_high']
            }
        }
    }
    
    with open('westbrook_rule_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✅ Results exported to westbrook_rule_results.json")
    return output_data

if __name__ == '__main__':
    analyze_westbrook_rule()
