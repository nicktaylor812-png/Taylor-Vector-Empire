"""
TAYLOR VECTOR TERMINAL - Fantasy Basketball Optimizer
Fantasy advice tool using TUSG%/PVR for draft/trade decisions
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

def fetch_current_players(season=2025):
    """
    Fetch current season player stats from nbaStats API
    """
    all_stats = []
    page = 1
    page_size = 100
    
    print(f"🔄 Fetching 2024-25 season stats from nbaStats API...")
    
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
                        'mpg': player.get('minutesPg', 0),
                        'ppg': player.get('points', 0) / games,
                        'apg': player.get('assists', 0) / games,
                        'rpg': player.get('rebounds', 0) / games,
                        'spg': player.get('steals', 0) / games,
                        'bpg': player.get('blocks', 0) / games,
                        'tov': player.get('turnovers', 0) / games,
                        'fga': player.get('fieldAttempts', 0) / games,
                        'fgm': player.get('fieldGoals', 0) / games,
                        'fg_pct': (player.get('fieldGoals', 0) / player.get('fieldAttempts', 1)) if player.get('fieldAttempts', 0) > 0 else 0,
                        'fta': player.get('ftAttempts', 0) / games,
                        'ftm': player.get('freeThrows', 0) / games,
                        'ft_pct': (player.get('freeThrows', 0) / player.get('ftAttempts', 1)) if player.get('ftAttempts', 0) > 0 else 0,
                        'tpm': player.get('threesMade', 0) / games
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
        return all_stats
    
    except Exception as e:
        print(f"❌ Error fetching players: {e}")
        import traceback
        traceback.print_exc()
        return []

def calculate_player_tusg(player_stats):
    """
    Calculate TUSG% for a player
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
    """
    mp = player_stats.get('mpg', 0)
    fga = player_stats.get('fga', 0)
    tov = player_stats.get('tov', 0)
    fta = player_stats.get('fta', 0)
    team = player_stats.get('team', 'UNK')
    
    team_pace = TEAM_PACE.get(team, 99.5)
    
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
    pts = player_stats.get('ppg', 0)
    ast = player_stats.get('apg', 0)
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

def calculate_fantasy_pvr(player_stats, league_settings):
    """
    Calculate Fantasy PVR weighted by league scoring
    
    Args:
        player_stats: Player statistics dictionary
        league_settings: Dictionary with scoring weights
            Example: {'ppg': 1.0, 'apg': 1.5, 'rpg': 1.2, 'spg': 3.0, 'bpg': 3.0, 'tov': -1.0, 'tpm': 0.5}
    
    Returns:
        Fantasy PVR score weighted by league scoring
    """
    ppg = player_stats.get('ppg', 0)
    apg = player_stats.get('apg', 0)
    rpg = player_stats.get('rpg', 0)
    spg = player_stats.get('spg', 0)
    bpg = player_stats.get('bpg', 0)
    tov = player_stats.get('tov', 0)
    tpm = player_stats.get('tpm', 0)
    
    ppg_weight = league_settings.get('ppg', 1.0)
    apg_weight = league_settings.get('apg', 1.5)
    rpg_weight = league_settings.get('rpg', 1.2)
    spg_weight = league_settings.get('spg', 3.0)
    bpg_weight = league_settings.get('bpg', 3.0)
    tov_weight = league_settings.get('tov', -1.0)
    tpm_weight = league_settings.get('tpm', 0.5)
    
    fantasy_points = (
        ppg * ppg_weight +
        apg * apg_weight +
        rpg * rpg_weight +
        spg * spg_weight +
        bpg * bpg_weight +
        tov * tov_weight +
        tpm * tpm_weight
    )
    
    pvr = calculate_player_pvr(player_stats)
    tusg = calculate_player_tusg(player_stats)
    
    fantasy_pvr = pvr * 0.6 + (fantasy_points / 10) * 0.4
    
    efficiency_bonus = 0
    if tusg < 20 and pvr > 20:
        efficiency_bonus = 10
    elif tusg > 35 and pvr < 10:
        efficiency_bonus = -10
    
    fantasy_pvr += efficiency_bonus
    
    return round(fantasy_pvr, 2)

def rank_players_by_fantasy_value(players, league_settings, min_mpg=20):
    """
    Rank players by fantasy value
    
    Args:
        players: List of player dictionaries
        league_settings: League scoring settings
        min_mpg: Minimum minutes per game to qualify (default 20)
    
    Returns:
        Sorted list of players with fantasy metrics
    """
    qualified_players = [p for p in players if p.get('mpg', 0) >= min_mpg]
    
    results = []
    for player in qualified_players:
        tusg = calculate_player_tusg(player)
        pvr = calculate_player_pvr(player)
        fantasy_pvr = calculate_fantasy_pvr(player, league_settings)
        
        ppg = player.get('ppg', 0)
        apg = player.get('apg', 0)
        rpg = player.get('rpg', 0)
        spg = player.get('spg', 0)
        bpg = player.get('bpg', 0)
        tov = player.get('tov', 0)
        tpm = player.get('tpm', 0)
        
        ppg_weight = league_settings.get('ppg', 1.0)
        apg_weight = league_settings.get('apg', 1.5)
        rpg_weight = league_settings.get('rpg', 1.2)
        spg_weight = league_settings.get('spg', 3.0)
        bpg_weight = league_settings.get('bpg', 3.0)
        tov_weight = league_settings.get('tov', -1.0)
        tpm_weight = league_settings.get('tpm', 0.5)
        
        projected_fantasy_ppg = (
            ppg * ppg_weight +
            apg * apg_weight +
            rpg * rpg_weight +
            spg * spg_weight +
            bpg * bpg_weight +
            tov * tov_weight +
            tpm * tpm_weight
        )
        
        results.append({
            'player_name': player.get('player_name'),
            'team': player.get('team'),
            'mpg': round(player.get('mpg', 0), 1),
            'ppg': round(ppg, 1),
            'apg': round(apg, 1),
            'rpg': round(rpg, 1),
            'spg': round(spg, 1),
            'bpg': round(bpg, 1),
            'tov': round(tov, 1),
            'tpm': round(tpm, 1),
            'tusg': tusg,
            'pvr': pvr,
            'fantasy_pvr': fantasy_pvr,
            'projected_fantasy_ppg': round(projected_fantasy_ppg, 1),
            'games_played': player.get('games_played', 0)
        })
    
    results.sort(key=lambda x: x['fantasy_pvr'], reverse=True)
    
    for i, player in enumerate(results):
        player['rank'] = i + 1
    
    return results

def analyze_trade(player_a_name, player_b_name, players, league_settings):
    """
    Analyze a fantasy trade: Should I trade Player A for Player B?
    
    Args:
        player_a_name: Name of player you're giving up
        player_b_name: Name of player you're receiving
        players: List of all players
        league_settings: League scoring settings
    
    Returns:
        Trade analysis dictionary
    """
    player_a = next((p for p in players if p.get('player_name', '').lower() == player_a_name.lower()), None)
    player_b = next((p for p in players if p.get('player_name', '').lower() == player_b_name.lower()), None)
    
    if not player_a or not player_b:
        return {
            'error': 'One or both players not found',
            'recommendation': 'INVALID'
        }
    
    player_a_tusg = calculate_player_tusg(player_a)
    player_a_pvr = calculate_player_pvr(player_a)
    player_a_fantasy_pvr = calculate_fantasy_pvr(player_a, league_settings)
    
    player_b_tusg = calculate_player_tusg(player_b)
    player_b_pvr = calculate_player_pvr(player_b)
    player_b_fantasy_pvr = calculate_fantasy_pvr(player_b, league_settings)
    
    ppg_weight = league_settings.get('ppg', 1.0)
    apg_weight = league_settings.get('apg', 1.5)
    rpg_weight = league_settings.get('rpg', 1.2)
    spg_weight = league_settings.get('spg', 3.0)
    bpg_weight = league_settings.get('bpg', 3.0)
    tov_weight = league_settings.get('tov', -1.0)
    tpm_weight = league_settings.get('tpm', 0.5)
    
    player_a_fantasy_ppg = (
        player_a.get('ppg', 0) * ppg_weight +
        player_a.get('apg', 0) * apg_weight +
        player_a.get('rpg', 0) * rpg_weight +
        player_a.get('spg', 0) * spg_weight +
        player_a.get('bpg', 0) * bpg_weight +
        player_a.get('tov', 0) * tov_weight +
        player_a.get('tpm', 0) * tpm_weight
    )
    
    player_b_fantasy_ppg = (
        player_b.get('ppg', 0) * ppg_weight +
        player_b.get('apg', 0) * apg_weight +
        player_b.get('rpg', 0) * rpg_weight +
        player_b.get('spg', 0) * spg_weight +
        player_b.get('bpg', 0) * bpg_weight +
        player_b.get('tov', 0) * tov_weight +
        player_b.get('tpm', 0) * tpm_weight
    )
    
    fantasy_pvr_diff = player_b_fantasy_pvr - player_a_fantasy_pvr
    fantasy_ppg_diff = player_b_fantasy_ppg - player_a_fantasy_ppg
    pvr_diff = player_b_pvr - player_a_pvr
    tusg_diff = player_b_tusg - player_a_tusg
    
    if fantasy_pvr_diff > 5:
        recommendation = 'ACCEPT'
        verdict = f'Strong trade! Gain {fantasy_pvr_diff:+.1f} Fantasy PVR'
    elif fantasy_pvr_diff > 2:
        recommendation = 'ACCEPT'
        verdict = f'Good trade. Gain {fantasy_pvr_diff:+.1f} Fantasy PVR'
    elif fantasy_pvr_diff > -2:
        recommendation = 'HOLD'
        verdict = f'Close trade. Minimal difference ({fantasy_pvr_diff:+.1f} Fantasy PVR)'
    elif fantasy_pvr_diff > -5:
        recommendation = 'DECLINE'
        verdict = f'Losing value. Down {fantasy_pvr_diff:+.1f} Fantasy PVR'
    else:
        recommendation = 'DECLINE'
        verdict = f'Bad trade! Lose {abs(fantasy_pvr_diff):.1f} Fantasy PVR'
    
    return {
        'player_a': {
            'name': player_a.get('player_name'),
            'team': player_a.get('team'),
            'tusg': player_a_tusg,
            'pvr': player_a_pvr,
            'fantasy_pvr': player_a_fantasy_pvr,
            'fantasy_ppg': round(player_a_fantasy_ppg, 1),
            'stats': {
                'ppg': round(player_a.get('ppg', 0), 1),
                'apg': round(player_a.get('apg', 0), 1),
                'rpg': round(player_a.get('rpg', 0), 1),
                'spg': round(player_a.get('spg', 0), 1),
                'bpg': round(player_a.get('bpg', 0), 1),
                'tov': round(player_a.get('tov', 0), 1)
            }
        },
        'player_b': {
            'name': player_b.get('player_name'),
            'team': player_b.get('team'),
            'tusg': player_b_tusg,
            'pvr': player_b_pvr,
            'fantasy_pvr': player_b_fantasy_pvr,
            'fantasy_ppg': round(player_b_fantasy_ppg, 1),
            'stats': {
                'ppg': round(player_b.get('ppg', 0), 1),
                'apg': round(player_b.get('apg', 0), 1),
                'rpg': round(player_b.get('rpg', 0), 1),
                'spg': round(player_b.get('spg', 0), 1),
                'bpg': round(player_b.get('bpg', 0), 1),
                'tov': round(player_b.get('tov', 0), 1)
            }
        },
        'analysis': {
            'fantasy_pvr_diff': round(fantasy_pvr_diff, 2),
            'fantasy_ppg_diff': round(fantasy_ppg_diff, 1),
            'pvr_diff': round(pvr_diff, 2),
            'tusg_diff': round(tusg_diff, 2),
            'recommendation': recommendation,
            'verdict': verdict
        },
        'timestamp': datetime.now().isoformat()
    }

def find_waiver_wire_gems(players, league_settings, max_ownership_pct=50, min_mpg=15):
    """
    Find undervalued high-PVR players for waiver wire pickup
    
    Args:
        players: List of all players
        league_settings: League scoring settings
        max_ownership_pct: Maximum ownership percentage (simulated based on ranking)
        min_mpg: Minimum minutes to qualify
    
    Returns:
        List of waiver wire recommendations
    """
    qualified_players = [p for p in players if p.get('mpg', 0) >= min_mpg]
    
    gems = []
    for player in qualified_players:
        tusg = calculate_player_tusg(player)
        pvr = calculate_player_pvr(player)
        fantasy_pvr = calculate_fantasy_pvr(player, league_settings)
        
        if pvr > 15 and fantasy_pvr > 20:
            ppg = player.get('ppg', 0)
            apg = player.get('apg', 0)
            rpg = player.get('rpg', 0)
            spg = player.get('spg', 0)
            bpg = player.get('bpg', 0)
            tov = player.get('tov', 0)
            tpm = player.get('tpm', 0)
            
            ppg_weight = league_settings.get('ppg', 1.0)
            apg_weight = league_settings.get('apg', 1.5)
            rpg_weight = league_settings.get('rpg', 1.2)
            spg_weight = league_settings.get('spg', 3.0)
            bpg_weight = league_settings.get('bpg', 3.0)
            tov_weight = league_settings.get('tov', -1.0)
            tpm_weight = league_settings.get('tpm', 0.5)
            
            projected_fantasy_ppg = (
                ppg * ppg_weight +
                apg * apg_weight +
                rpg * rpg_weight +
                spg * spg_weight +
                bpg * bpg_weight +
                tov * tov_weight +
                tpm * tpm_weight
            )
            
            gems.append({
                'player_name': player.get('player_name'),
                'team': player.get('team'),
                'mpg': round(player.get('mpg', 0), 1),
                'ppg': round(ppg, 1),
                'apg': round(apg, 1),
                'rpg': round(rpg, 1),
                'tusg': tusg,
                'pvr': pvr,
                'fantasy_pvr': fantasy_pvr,
                'projected_fantasy_ppg': round(projected_fantasy_ppg, 1),
                'upside': 'High' if pvr > 25 else 'Medium'
            })
    
    gems.sort(key=lambda x: x['fantasy_pvr'], reverse=True)
    
    return gems[:20]

DEFAULT_LEAGUE_SETTINGS = {
    'ppg': 1.0,
    'apg': 1.5,
    'rpg': 1.2,
    'spg': 3.0,
    'bpg': 3.0,
    'tov': -1.0,
    'tpm': 0.5
}

if __name__ == '__main__':
    print("🏀 TAYLOR VECTOR TERMINAL - Fantasy Basketball Optimizer")
    print("=" * 80)
    
    players = fetch_current_players(2025)
    
    if not players:
        print("❌ Could not fetch player data")
        exit(1)
    
    print(f"\n✅ Loaded {len(players)} players")
    
    league_settings = DEFAULT_LEAGUE_SETTINGS
    
    print(f"\n📊 League Settings: {json.dumps(league_settings, indent=2)}")
    
    print("\n🏆 Top 10 Fantasy Players by Fantasy PVR:")
    print("-" * 80)
    rankings = rank_players_by_fantasy_value(players, league_settings, min_mpg=25)
    
    for player in rankings[:10]:
        print(f"{player['rank']:2d}. {player['player_name']:25s} ({player['team']:3s}) | "
              f"FPVR: {player['fantasy_pvr']:6.2f} | "
              f"FPPG: {player['projected_fantasy_ppg']:5.1f} | "
              f"PVR: {player['pvr']:5.2f} | "
              f"TUSG: {player['tusg']:5.2f}%")
    
    print("\n💎 Waiver Wire Gems (High PVR + Fantasy Value):")
    print("-" * 80)
    gems = find_waiver_wire_gems(players, league_settings, min_mpg=18)
    
    for i, gem in enumerate(gems[:10]):
        print(f"{i+1:2d}. {gem['player_name']:25s} ({gem['team']:3s}) | "
              f"FPVR: {gem['fantasy_pvr']:6.2f} | "
              f"PVR: {gem['pvr']:5.2f} | "
              f"MPG: {gem['mpg']:4.1f} | "
              f"Upside: {gem['upside']}")
    
    print("\n🔄 Trade Analysis Example:")
    print("-" * 80)
    
    if len(rankings) >= 2:
        trade_result = analyze_trade(
            rankings[0]['player_name'],
            rankings[1]['player_name'],
            players,
            league_settings
        )
        
        if 'error' not in trade_result:
            print(f"\nTrade: {trade_result['player_a']['name']} FOR {trade_result['player_b']['name']}")
            print(f"\n{trade_result['player_a']['name']}:")
            print(f"  Fantasy PVR: {trade_result['player_a']['fantasy_pvr']:.2f}")
            print(f"  Fantasy PPG: {trade_result['player_a']['fantasy_ppg']:.1f}")
            print(f"  PVR: {trade_result['player_a']['pvr']:.2f} | TUSG: {trade_result['player_a']['tusg']:.2f}%")
            
            print(f"\n{trade_result['player_b']['name']}:")
            print(f"  Fantasy PVR: {trade_result['player_b']['fantasy_pvr']:.2f}")
            print(f"  Fantasy PPG: {trade_result['player_b']['fantasy_ppg']:.1f}")
            print(f"  PVR: {trade_result['player_b']['pvr']:.2f} | TUSG: {trade_result['player_b']['tusg']:.2f}%")
            
            print(f"\n⚖️ Analysis:")
            print(f"  Fantasy PVR Difference: {trade_result['analysis']['fantasy_pvr_diff']:+.2f}")
            print(f"  Fantasy PPG Difference: {trade_result['analysis']['fantasy_ppg_diff']:+.1f}")
            print(f"\n  RECOMMENDATION: {trade_result['analysis']['recommendation']}")
            print(f"  {trade_result['analysis']['verdict']}")
    
    print("\n" + "=" * 80)
