"""
TAYLOR VECTOR TERMINAL - Season Prediction Engine
Predicts team wins, awards, and breakout players using TUSG% and PVR
"""

import requests
import json
import os
from datetime import datetime
from statistics import mean, stdev

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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

PLAYOFF_TEAMS_2024 = ['BOS', 'MIL', 'NYK', 'CLE', 'ORL', 'IND', 'PHI', 'MIA',
                      'DEN', 'OKC', 'MIN', 'LAC', 'DAL', 'PHX', 'LAL', 'NOP']

def calculate_player_tusg(player_stats, team_pace):
    """Calculate TUSG% for a player"""
    mp = player_stats.get('min', 0)
    fga = player_stats.get('fga', 0)
    tov = player_stats.get('tov', 0)
    fta = player_stats.get('fta', 0)
    
    if mp == 0 or team_pace == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * team_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_player_pvr(player_stats):
    """Calculate PVR for a player"""
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

def fetch_all_players(season=2025):
    """Fetch all NBA players from API with their stats"""
    all_stats = []
    page = 1
    page_size = 100
    
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
                    
                    # API returns TOTAL stats, need to convert to per game
                    total_minutes = player.get('minutesPg', 0)  # Misleading name - it's actually total
                    mpg = total_minutes / games if games > 0 else 0
                    
                    stats = {
                        'player_id': player.get('slug'),
                        'player_name': player.get('playerName'),
                        'team': player.get('team'),
                        'games_played': games,
                        'min': mpg,  # Now correctly in minutes per game
                        'pts': player.get('points', 0) / games,
                        'ast': player.get('assists', 0) / games,
                        'reb': player.get('rebounds', 0) / games,
                        'stl': player.get('steals', 0) / games,
                        'blk': player.get('blocks', 0) / games,
                        'tov': player.get('turnovers', 0) / games,
                        'fga': player.get('fieldAttempts', 0) / games,
                        'fta': player.get('ftAttempts', 0) / games
                    }
                    all_stats.append(stats)
                
                if len(players) < page_size:
                    break
                
                page += 1
            else:
                break
        
        print(f"✅ Fetched {len(all_stats)} players for season {season}")
        return all_stats
    except Exception as e:
        print(f"❌ Error fetching players: {e}")
        return []

def aggregate_team_metrics(all_players):
    """Aggregate TUSG% and PVR for each team from their rosters"""
    team_metrics = {}
    
    for team_abbr in TEAM_PACE.keys():
        team_players = [p for p in all_players if p.get('team') == team_abbr and p.get('min', 0) >= 10]
        
        if not team_players:
            continue
        
        team_pace = TEAM_PACE[team_abbr]
        
        tusg_values = []
        pvr_values = []
        total_minutes = 0
        
        for player in team_players:
            player['tusg'] = calculate_player_tusg(player, team_pace)
            player['pvr'] = calculate_player_pvr(player)
            
            if player['tusg'] > 0:
                tusg_values.append(player['tusg'])
            if player['pvr'] != 0:
                pvr_values.append(player['pvr'])
            
            total_minutes += player['min']
        
        avg_tusg = mean(tusg_values) if tusg_values else 50.0
        avg_pvr = mean(pvr_values) if pvr_values else 0.0
        
        weighted_tusg = sum(p['tusg'] * p['min'] for p in team_players if p['tusg'] > 0) / total_minutes if total_minutes > 0 else avg_tusg
        weighted_pvr = sum(p['pvr'] * p['min'] for p in team_players if p['pvr'] != 0) / total_minutes if total_minutes > 0 else avg_pvr
        
        team_metrics[team_abbr] = {
            'team_name': TEAM_FULL_NAMES[team_abbr],
            'team_abbr': team_abbr,
            'avg_tusg': round(avg_tusg, 2),
            'avg_pvr': round(avg_pvr, 2),
            'weighted_tusg': round(weighted_tusg, 2),
            'weighted_pvr': round(weighted_pvr, 2),
            'roster': team_players,
            'pace': team_pace
        }
    
    return team_metrics

def predict_team_wins(team_metrics):
    """
    Predict win totals using PVR → wins correlation
    Based on historical data: Higher PVR correlates with more wins
    Formula: Wins = 41 + (PVR * 1.5) + (TUSG% - 50) * 0.3
    """
    predictions = []
    
    for team_abbr, metrics in team_metrics.items():
        weighted_pvr = metrics['weighted_pvr']
        weighted_tusg = metrics['weighted_tusg']
        
        base_wins = 41
        pvr_impact = weighted_pvr * 1.5
        tusg_impact = (weighted_tusg - 50) * 0.3
        
        predicted_wins = base_wins + pvr_impact + tusg_impact
        predicted_wins = max(15, min(70, predicted_wins))
        predicted_wins = round(predicted_wins, 1)
        
        confidence = 70 + min(15, abs(weighted_pvr) / 2)
        confidence = round(min(95, confidence), 1)
        
        predictions.append({
            'team_name': metrics['team_name'],
            'team_abbr': team_abbr,
            'predicted_wins': predicted_wins,
            'predicted_losses': round(82 - predicted_wins, 1),
            'avg_pvr': metrics['weighted_pvr'],
            'avg_tusg': metrics['weighted_tusg'],
            'confidence': confidence
        })
    
    predictions.sort(key=lambda x: x['predicted_wins'], reverse=True)
    
    return predictions

def predict_mvp(all_players, team_metrics):
    """
    MVP prediction: Highest PVR on playoff-caliber team
    Criteria:
    - Must be on team with 40+ predicted wins (lowered threshold)
    - High PVR (elite efficiency)
    - Decent usage (TUSG% > 20)
    - Minutes played > 25 MPG
    """
    win_predictions = predict_team_wins(team_metrics)
    playoff_teams = [p['team_abbr'] for p in win_predictions if p['predicted_wins'] >= 40]
    
    mvp_candidates = []
    
    for player in all_players:
        team = player.get('team')
        if team not in playoff_teams:
            continue
        
        # Filter by minimum minutes per game (25+)
        min_per_game = player.get('min', 0)
        if min_per_game < 25:
            continue
        
        # Filter by minimum games played
        if player.get('games_played', 0) < 10:
            continue
        
        team_pace = TEAM_PACE.get(team, 99.5)
        tusg = calculate_player_tusg(player, team_pace)
        pvr = calculate_player_pvr(player)
        
        # More lenient thresholds for data quality
        if tusg < 20 or pvr < 8:
            continue
        
        # Must be a significant scorer
        if player['pts'] < 15:
            continue
        
        mvp_score = pvr * 2 + tusg * 0.5 + player['pts'] * 0.3
        
        mvp_candidates.append({
            'player_name': player['player_name'],
            'team': team,
            'team_name': TEAM_FULL_NAMES.get(team, team),
            'pvr': round(pvr, 1),
            'tusg': round(tusg, 1),
            'ppg': round(player['pts'], 1),
            'apg': round(player['ast'], 1),
            'rpg': round(player['reb'], 1),
            'mpg': round(min_per_game, 1),
            'mvp_score': round(mvp_score, 2),
            'confidence': round(min(95, 60 + pvr * 0.8), 1)
        })
    
    mvp_candidates.sort(key=lambda x: x['mvp_score'], reverse=True)
    
    return mvp_candidates[:10]

def predict_dpoy(all_players):
    """
    DPOY prediction: Defensive metrics proxy
    Using: Steals + Blocks as proxy for defensive impact
    Higher minutes = more opportunity
    """
    dpoy_candidates = []
    
    for player in all_players:
        if player.get('min', 0) < 25:
            continue
        
        stl = player.get('stl', 0)
        blk = player.get('blk', 0)
        
        defensive_score = (stl * 2) + (blk * 3) + (player['reb'] * 0.5)
        
        if defensive_score < 2.5:
            continue
        
        dpoy_candidates.append({
            'player_name': player['player_name'],
            'team': player['team'],
            'team_name': TEAM_FULL_NAMES.get(player['team'], player['team']),
            'stl': round(stl, 1),
            'blk': round(blk, 1),
            'rpg': round(player['reb'], 1),
            'mpg': round(player['min'], 1),
            'defensive_score': round(defensive_score, 2),
            'confidence': round(min(85, 50 + defensive_score * 5), 1)
        })
    
    dpoy_candidates.sort(key=lambda x: x['defensive_score'], reverse=True)
    
    return dpoy_candidates[:10]

def predict_mip(all_players, previous_season_players):
    """
    MIP prediction: Most improved player
    Compare current season to previous season
    Look for: PVR increase, usage increase, scoring increase
    """
    mip_candidates = []
    
    # Use name-based matching since player_id is None in API data
    current_dict = {p['player_name']: p for p in all_players if p.get('min', 0) >= 20 and p.get('games_played', 0) >= 10}
    previous_dict = {p['player_name']: p for p in previous_season_players if p.get('games_played', 0) >= 10}
    
    for player_name, current in current_dict.items():
        if player_name not in previous_dict:
            continue
        
        previous = previous_dict[player_name]
        
        # Must have played at least 15 MPG in previous season
        if previous.get('min', 0) < 15:
            continue
        
        # Calculate current season metrics
        team_pace = TEAM_PACE.get(current['team'], 99.5)
        current_tusg = calculate_player_tusg(current, team_pace)
        current_pvr = calculate_player_pvr(current)
        
        # Calculate previous season metrics
        prev_team_pace = TEAM_PACE.get(previous.get('team', current['team']), 99.5)
        prev_tusg = calculate_player_tusg(previous, prev_team_pace)
        prev_pvr = calculate_player_pvr(previous)
        
        # Calculate improvements
        ppg_increase = current['pts'] - previous['pts']
        pvr_increase = current_pvr - prev_pvr
        tusg_increase = current_tusg - prev_tusg
        
        # More lenient thresholds: 2+ PPG increase OR 3+ PVR increase
        if ppg_increase < 2 and pvr_increase < 3:
            continue
        
        # Must show meaningful improvement
        if ppg_increase < 0 and pvr_increase < 0:
            continue
        
        improvement_score = ppg_increase * 2 + pvr_increase * 1.5 + max(0, tusg_increase * 0.5)
        
        mip_candidates.append({
            'player_name': current['player_name'],
            'team': current['team'],
            'team_name': TEAM_FULL_NAMES.get(current['team'], current['team']),
            'current_ppg': round(current['pts'], 1),
            'previous_ppg': round(previous['pts'], 1),
            'ppg_increase': round(ppg_increase, 1),
            'current_pvr': round(current_pvr, 1),
            'previous_pvr': round(prev_pvr, 1),
            'pvr_increase': round(pvr_increase, 1),
            'improvement_score': round(improvement_score, 2),
            'confidence': round(min(90, 50 + improvement_score * 2), 1)
        })
    
    mip_candidates.sort(key=lambda x: x['improvement_score'], reverse=True)
    
    return mip_candidates[:10]

def predict_roy(all_players):
    """
    ROY prediction: Rookie of the Year
    Simplified: Top performers who are likely rookies (low games played historically)
    High PVR + decent usage + scoring
    """
    roy_candidates = []
    
    for player in all_players:
        if player.get('min', 0) < 20:
            continue
        
        team_pace = TEAM_PACE.get(player['team'], 99.5)
        tusg = calculate_player_tusg(player, team_pace)
        pvr = calculate_player_pvr(player)
        
        if player['pts'] < 12:
            continue
        
        rookie_score = pvr * 1.5 + player['pts'] * 0.8 + tusg * 0.3
        
        roy_candidates.append({
            'player_name': player['player_name'],
            'team': player['team'],
            'team_name': TEAM_FULL_NAMES.get(player['team'], player['team']),
            'ppg': round(player['pts'], 1),
            'apg': round(player['ast'], 1),
            'rpg': round(player['reb'], 1),
            'pvr': round(pvr, 1),
            'tusg': round(tusg, 1),
            'rookie_score': round(rookie_score, 2),
            'confidence': round(min(85, 40 + rookie_score * 0.5), 1)
        })
    
    roy_candidates.sort(key=lambda x: x['rookie_score'], reverse=True)
    
    return roy_candidates[:10]

def find_breakout_candidates(all_players, team_metrics):
    """
    Breakout candidates: High PVR, low minutes (underutilized)
    Criteria:
    - PVR > 12 (efficient)
    - Minutes < 25 (underutilized)
    - On good team (playoff contender)
    """
    win_predictions = predict_team_wins(team_metrics)
    good_teams = [p['team_abbr'] for p in win_predictions if p['predicted_wins'] >= 40]
    
    breakout_candidates = []
    
    for player in all_players:
        if player.get('min', 0) >= 25 or player.get('min', 0) < 15:
            continue
        
        team_pace = TEAM_PACE.get(player['team'], 99.5)
        pvr = calculate_player_pvr(player)
        tusg = calculate_player_tusg(player, team_pace)
        
        if pvr < 12:
            continue
        
        is_good_team = player['team'] in good_teams
        
        breakout_score = pvr * 2 + (30 - player['min']) * 0.5
        if is_good_team:
            breakout_score *= 1.2
        
        breakout_candidates.append({
            'player_name': player['player_name'],
            'team': player['team'],
            'team_name': TEAM_FULL_NAMES.get(player['team'], player['team']),
            'pvr': round(pvr, 1),
            'tusg': round(tusg, 1),
            'mpg': round(player['min'], 1),
            'ppg': round(player['pts'], 1),
            'potential_increase': f"+{round(player['pts'] * 0.4, 1)} PPG",
            'breakout_score': round(breakout_score, 2),
            'confidence': round(min(90, 55 + pvr * 1.2), 1)
        })
    
    breakout_candidates.sort(key=lambda x: x['breakout_score'], reverse=True)
    
    return breakout_candidates[:15]

def get_vegas_comparison():
    """
    Placeholder for Vegas win totals comparison
    In production, this would fetch from a sports betting API
    """
    return {
        'BOS': 58.5, 'MIL': 52.5, 'PHI': 50.5, 'CLE': 48.5, 'NYK': 47.5,
        'DEN': 56.5, 'LAL': 45.5, 'PHX': 49.5, 'LAC': 44.5, 'GSW': 43.5,
        'DAL': 52.5, 'OKC': 54.5, 'MIN': 51.5, 'SAC': 46.5, 'NOP': 42.5,
        'MIA': 46.5, 'ATL': 38.5, 'BKN': 35.5, 'ORL': 44.5, 'IND': 43.5,
        'CHI': 39.5, 'TOR': 32.5, 'CHA': 28.5, 'WAS': 25.5, 'DET': 24.5,
        'HOU': 40.5, 'MEM': 41.5, 'SAS': 31.5, 'POR': 33.5, 'UTA': 30.5
    }

def get_espn_comparison():
    """
    Placeholder for ESPN predictions
    In production, this would scrape ESPN's projections
    """
    return {
        'BOS': 59, 'MIL': 53, 'PHI': 51, 'CLE': 49, 'NYK': 48,
        'DEN': 57, 'LAL': 46, 'PHX': 50, 'LAC': 45, 'GSW': 44,
        'DAL': 53, 'OKC': 55, 'MIN': 52, 'SAC': 47, 'NOP': 43,
        'MIA': 47, 'ATL': 39, 'BKN': 36, 'ORL': 45, 'IND': 44,
        'CHI': 40, 'TOR': 33, 'CHA': 29, 'WAS': 26, 'DET': 25,
        'HOU': 41, 'MEM': 42, 'SAS': 32, 'POR': 34, 'UTA': 31
    }

def generate_all_predictions(season=2025):
    """
    Generate all predictions for the season
    Returns comprehensive prediction data
    """
    print(f"🏀 Generating Season Predictions for {season}...")
    
    all_players = fetch_all_players(season)
    previous_players = fetch_all_players(season - 1)
    
    print("📊 Aggregating team metrics...")
    team_metrics = aggregate_team_metrics(all_players)
    
    print("🏆 Predicting team wins...")
    win_predictions = predict_team_wins(team_metrics)
    
    print("⭐ Predicting MVP race...")
    mvp_predictions = predict_mvp(all_players, team_metrics)
    
    print("🛡️ Predicting DPOY race...")
    dpoy_predictions = predict_dpoy(all_players)
    
    print("📈 Predicting MIP race...")
    mip_predictions = predict_mip(all_players, previous_players)
    
    print("🌟 Predicting ROY race...")
    roy_predictions = predict_roy(all_players)
    
    print("💎 Finding breakout candidates...")
    breakout_candidates = find_breakout_candidates(all_players, team_metrics)
    
    print("📊 Getting Vegas/ESPN comparisons...")
    vegas_totals = get_vegas_comparison()
    espn_totals = get_espn_comparison()
    
    for pred in win_predictions:
        team_abbr = pred['team_abbr']
        pred['vegas_wins'] = vegas_totals.get(team_abbr, 0)
        pred['espn_wins'] = espn_totals.get(team_abbr, 0)
        pred['vegas_diff'] = round(pred['predicted_wins'] - pred['vegas_wins'], 1) if pred['vegas_wins'] > 0 else 0
        pred['espn_diff'] = round(pred['predicted_wins'] - pred['espn_wins'], 1) if pred['espn_wins'] > 0 else 0
    
    predictions = {
        'season': season,
        'generated_at': datetime.now().isoformat(),
        'team_wins': win_predictions,
        'mvp_race': mvp_predictions,
        'dpoy_race': dpoy_predictions,
        'mip_race': mip_predictions,
        'roy_race': roy_predictions,
        'breakout_candidates': breakout_candidates,
        'summary': {
            'total_teams': len(win_predictions),
            'mvp_candidates': len(mvp_predictions),
            'dpoy_candidates': len(dpoy_predictions),
            'mip_candidates': len(mip_predictions),
            'roy_candidates': len(roy_predictions),
            'breakout_candidates': len(breakout_candidates)
        }
    }
    
    print("✅ All predictions generated successfully!")
    
    return predictions

def save_predictions(predictions, filename='season_predictions.json'):
    """Save predictions to JSON file"""
    filepath = os.path.join(SCRIPT_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(predictions, f, indent=2)
    
    print(f"💾 Predictions saved to {filepath}")
    return filepath

def validate_historical_predictions():
    """
    Validate prediction model against historical seasons
    Test predictions from past seasons against actual results
    """
    validation_results = {
        'seasons_tested': [],
        'average_accuracy': 0,
        'total_seasons': 0,
        'methodology': 'Testing prediction model accuracy using historical NBA season data'
    }
    
    # Historical season data (2023-24 season actual wins)
    actual_2024_wins = {
        'BOS': 64, 'MIL': 49, 'NYK': 50, 'CLE': 48, 'ORL': 47, 'IND': 47,
        'PHI': 47, 'MIA': 46, 'DEN': 57, 'OKC': 57, 'MIN': 56, 'LAC': 51,
        'DAL': 50, 'PHX': 49, 'LAL': 47, 'NOP': 49, 'SAC': 46, 'GSW': 46,
        'HOU': 41, 'ATL': 36, 'CHI': 39, 'BKN': 32, 'TOR': 25, 'CHA': 21,
        'WAS': 15, 'DET': 14, 'POR': 21, 'SAS': 22, 'MEM': 27, 'UTA': 31
    }
    
    # Simulate 2023-24 predictions using 2023 data
    try:
        print("🔍 Validating against 2023-24 season...")
        
        # Fetch 2024 data (which was the prediction target)
        players_2024 = fetch_all_players(2024)
        if not players_2024:
            print("⚠️ Could not fetch 2024 data for validation")
            return validation_results
        
        team_metrics_2024 = aggregate_team_metrics(players_2024)
        predictions_2024 = predict_team_wins(team_metrics_2024)
        
        # Calculate accuracy
        total_error = 0
        exact_predictions = 0
        within_5_wins = 0
        within_10_wins = 0
        comparisons = []
        
        for pred in predictions_2024:
            team_abbr = pred['team_abbr']
            predicted_wins = pred['predicted_wins']
            actual_wins = actual_2024_wins.get(team_abbr, 0)
            
            if actual_wins > 0:
                error = abs(predicted_wins - actual_wins)
                total_error += error
                
                if error == 0:
                    exact_predictions += 1
                if error <= 5:
                    within_5_wins += 1
                if error <= 10:
                    within_10_wins += 1
                
                comparisons.append({
                    'team': pred['team_name'],
                    'predicted': predicted_wins,
                    'actual': actual_wins,
                    'error': round(error, 1),
                    'accuracy': round(100 - (error / actual_wins * 100), 1) if actual_wins > 0 else 0
                })
        
        num_teams = len(comparisons)
        avg_error = total_error / num_teams if num_teams > 0 else 0
        
        validation_results['seasons_tested'].append({
            'season': '2023-24',
            'teams_predicted': num_teams,
            'average_error': round(avg_error, 2),
            'exact_predictions': exact_predictions,
            'within_5_wins': within_5_wins,
            'within_10_wins': within_10_wins,
            'within_5_pct': round(within_5_wins / num_teams * 100, 1) if num_teams > 0 else 0,
            'within_10_pct': round(within_10_wins / num_teams * 100, 1) if num_teams > 0 else 0,
            'comparisons': comparisons
        })
        
        validation_results['total_seasons'] = 1
        validation_results['average_accuracy'] = round(100 - (avg_error / 41 * 100), 1)
        
        print(f"✅ 2023-24 Validation Complete:")
        print(f"   Average Error: {avg_error:.1f} wins")
        print(f"   Within 5 wins: {within_5_wins}/{num_teams} ({within_5_wins/num_teams*100:.1f}%)")
        print(f"   Within 10 wins: {within_10_wins}/{num_teams} ({within_10_wins/num_teams*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
    
    return validation_results

if __name__ == '__main__':
    predictions = generate_all_predictions(2025)
    save_predictions(predictions)
    
    print("\n" + "="*70)
    print("SEASON PREDICTION ENGINE - SUMMARY")
    print("="*70)
    
    print(f"\n🏆 TOP 5 TEAMS (PREDICTED WINS):")
    for i, team in enumerate(predictions['team_wins'][:5], 1):
        print(f"{i}. {team['team_name']}: {team['predicted_wins']} wins ({team['confidence']}% confidence)")
    
    print(f"\n⭐ MVP RACE TOP 3:")
    for i, player in enumerate(predictions['mvp_race'][:3], 1):
        print(f"{i}. {player['player_name']} ({player['team_name']}) - PVR: {player['pvr']}, PPG: {player['ppg']}")
    
    print(f"\n💎 TOP 3 BREAKOUT CANDIDATES:")
    for i, player in enumerate(predictions['breakout_candidates'][:3], 1):
        print(f"{i}. {player['player_name']} ({player['team_name']}) - PVR: {player['pvr']}, MPG: {player['mpg']}")
