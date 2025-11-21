import requests
import sqlite3
import time
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BANKROLL = 100
MIN_EDGE = 65.0
ODDS_API_KEY = os.getenv('ODDS_API_KEY', '9dc6732846dcf221cd38f9214e01ef9f')
BALLDONTLIE_API_KEY = os.getenv('BALLDONTLIE_API_KEY', 'eada3064-5b46-4fe0-948c-1771738e4021')

DB_FILE = 'taylor_62.db'

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            game TEXT,
            pick TEXT,
            edge REAL,
            home_tusg REAL,
            away_tusg REAL,
            home_pvr REAL,
            away_pvr REAL,
            spread REAL
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

def get_live_spreads():
    """Fetch live NBA spreads from The Odds API"""
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=spreads&oddsFormat=american"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            games = response.json()
            logger.info(f"✅ The Odds API: {len(games)} live NBA games with spreads")
            return games if games else []
        else:
            logger.error(f"❌ The Odds API failed: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ The Odds API error: {e}")
        return []

def get_player_season_averages(season=2025):
    """Fetch current season averages from FREE nbaStats API (NO KEY REQUIRED)"""
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
                    
                    # Parse minutes (API returns various formats: "MM:SS", "MM:SS:hundredths", "HH:MM:SS", or numeric)
                    minutes_str = player.get('minutesPg', '0:00')
                    try:
                        if isinstance(minutes_str, str) and ':' in minutes_str:
                            parts = minutes_str.split(':')
                            if len(parts) == 3:
                                first = float(parts[0])
                                if first > 59:  # True HH:MM:SS format (hours exceed 59)
                                    minutes = first * 60 + float(parts[1]) + float(parts[2]) / 60
                                else:  # MM:SS:hundredths format (e.g., "28:43:00" = 28 min, 43 sec)
                                    minutes = first + float(parts[1]) / 60 + float(parts[2]) / 3600
                            elif len(parts) == 2:  # MM:SS format
                                minutes = float(parts[0]) + float(parts[1]) / 60
                            else:
                                minutes = 0.0
                        else:
                            minutes = float(minutes_str) if minutes_str else 0.0
                    except (ValueError, AttributeError):
                        minutes = 0.0  # Gracefully handle bad inputs
                    
                    stats = {
                        'player_id': player.get('slug'),
                        'player_name': player.get('playerName'),
                        'team': player.get('team'),
                        'games_played': games,
                        'min': minutes,
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
                logger.error(f"❌ nbaStats API failed: {response.status_code}")
                break
        
        logger.info(f"✅ FREE NBA API: {len(all_stats)} player season averages loaded")
        return all_stats
    except Exception as e:
        logger.error(f"❌ Error fetching season averages: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_team_players_stats(team_name, all_stats):
    """Get stats for all players on a specific team"""
    team_mapping = {
        'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
        'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
        'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
        'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
        'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
        'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
        'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
        'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
        'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
        'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
    }
    
    team_abbr = team_mapping.get(team_name)
    if not team_abbr:
        return []
    
    return [s for s in all_stats if s.get('team') == team_abbr]

TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

def calculate_player_tusg(player_stats, team_pace):
    """
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
    """
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
    return tusg

def calculate_team_tusg(team_players_stats, team_abbr):
    """Calculate average TUSG% for entire team"""
    if not team_players_stats:
        return 50.0
    
    team_pace = TEAM_PACE.get(team_abbr, 99.5)
    
    tusg_values = []
    for player in team_players_stats:
        if player.get('min', 0) >= 10:
            tusg = calculate_player_tusg(player, team_pace)
            if tusg > 0:
                tusg_values.append(tusg)
    
    if not tusg_values:
        return 50.0
    
    return sum(tusg_values) / len(tusg_values)

def calculate_player_pvr(player_stats):
    """
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
    return pvr

def calculate_team_pvr(team_players_stats):
    """Calculate average PVR for entire team"""
    if not team_players_stats:
        return 0.0
    
    pvr_values = []
    for player in team_players_stats:
        if player.get('min', 0) >= 10:
            pvr = calculate_player_pvr(player)
            pvr_values.append(pvr)
    
    if not pvr_values:
        return 0.0
    
    return sum(pvr_values) / len(pvr_values)

def save_pick(game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread):
    """Save pick to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO picks (game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Database error: {e}")

def analyze():
    """Main analysis function - Combines FREE NBA API stats + The Odds API spreads"""
    logger.info("🏀 TAYLOR VECTOR TERMINAL - Starting analysis...")
    
    spreads = get_live_spreads()
    
    if not spreads:
        logger.warning("❌ No live games with spreads available")
        return
    
    player_stats = get_player_season_averages(2025)
    
    if not player_stats:
        logger.warning("⚠️ Could not load player stats, using simplified calculation")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🎯 TAYLOR VECTOR TERMINAL | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*70}")
    logger.info(f"Analyzing {len(spreads)} games with live spreads")
    
    picks_found = 0
    
    for game in spreads:
        try:
            home_team = game.get('home_team', 'Unknown')
            away_team = game.get('away_team', 'Unknown')
            
            bookmakers = game.get('bookmakers', [])
            if not bookmakers:
                continue
            
            spread_market = None
            for bookmaker in bookmakers:
                markets = bookmaker.get('markets', [])
                for market in markets:
                    if market.get('key') == 'spreads':
                        spread_market = market
                        break
                if spread_market:
                    break
            
            if not spread_market:
                continue
            
            outcomes = spread_market.get('outcomes', [])
            home_spread = None
            away_spread = None
            
            for outcome in outcomes:
                if outcome.get('name') == home_team:
                    home_spread = outcome.get('point', 0)
                elif outcome.get('name') == away_team:
                    away_spread = outcome.get('point', 0)
            
            if home_spread is None or away_spread is None:
                continue
            
            home_stats = get_team_players_stats(home_team, player_stats)
            away_stats = get_team_players_stats(away_team, player_stats)
            
            team_mapping = {
                'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
                'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
                'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
                'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
                'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
                'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
                'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
                'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
                'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
                'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
            }
            
            home_abbr = team_mapping.get(home_team, 'UNK')
            away_abbr = team_mapping.get(away_team, 'UNK')
            
            home_tusg = calculate_team_tusg(home_stats, home_abbr) if home_stats else 50.0
            away_tusg = calculate_team_tusg(away_stats, away_abbr) if away_stats else 50.0
            
            home_pvr = calculate_team_pvr(home_stats) if home_stats else 0.0
            away_pvr = calculate_team_pvr(away_stats) if away_stats else 0.0
            
            edge = 50 + (home_tusg - away_tusg) + (home_pvr - away_pvr) * 0.5
            edge = max(min(edge, 80), 45)
            
            if edge >= MIN_EDGE:
                picks_found += 1
                game_text = f"{away_team} @ {home_team}"
                pick_text = f"{home_team} {home_spread:+.1f}"
                
                save_pick(game_text, pick_text, edge, home_tusg, away_tusg, home_pvr, away_pvr, home_spread)
                
                logger.info(f"\n🔥 {game_text}")
                logger.info(f"   PICK: {pick_text} | EDGE: {edge:.1f}%")
                logger.info(f"   TUSG: Home={home_tusg:.1f} vs Away={away_tusg:.1f}")
                logger.info(f"   PVR: Home={home_pvr:.1f} vs Away={away_pvr:.1f}")
                logger.info(f"   Spread: {home_spread:+.1f}")
        
        except Exception as e:
            logger.error(f"❌ Error processing game: {e}")
            import traceback
            traceback.print_exc()
    
    if picks_found == 0:
        logger.info("⚠️ No picks with edge ≥ 65% found this cycle")
    else:
        logger.info(f"✅ Generated {picks_found} high-confidence picks!")
    
    logger.info(f"{'='*70}\n")

logger.info("🚀 TAYLOR VECTOR TERMINAL - LIVE BETTING SYSTEM")
logger.info(f"💰 Bankroll: ${BANKROLL}")
logger.info(f"🎯 Min Edge: {MIN_EDGE}%")
logger.info(f"📊 Data: FREE NBA API (player stats) + The Odds API (spreads)")
logger.info(f"🔑 APIs: Both FREE & Configured ✅")
logger.info("⏰ Running every 45 seconds...\n")

init_database()

while True:
    try:
        analyze()
        time.sleep(45)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
        break
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(45)
