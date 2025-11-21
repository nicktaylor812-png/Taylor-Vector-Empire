"""
TAYLOR VECTOR TERMINAL - Underrated PVR Stars Series
Discovery engine for high-PVR, low-profile players (Hidden Gems)

Criteria:
- PVR > 15 (elite efficiency)
- TUSG% < 25% (low usage - not the main star)
- MPG < 30 (limited minutes - untapped potential)

Underrated Score = (PVR / TUSG%) × (Minutes Potential)
Minutes Potential = (30 - MPG) → higher when player gets fewer minutes
"""

import requests
import json
import os
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(SCRIPT_DIR, 'reports')

# Team Pace Data (2024-25 Season)
TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

def get_player_season_averages(season=2025):
    """Fetch current season averages from FREE nbaStats API (NO KEY REQUIRED)"""
    all_stats = []
    page = 1
    page_size = 100
    
    try:
        logger.info(f"Fetching player season averages for {season} season...")
        
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
                        'fta': player.get('ftAttempts', 0) / games,
                        'reb': player.get('totalRb', 0) / games,
                        'stl': player.get('steals', 0) / games,
                        'blk': player.get('blocks', 0) / games
                    }
                    all_stats.append(stats)
                
                if len(players) < page_size:
                    break
                
                page += 1
                time.sleep(0.3)
            else:
                logger.error(f"❌ nbaStats API failed: {response.status_code}")
                break
        
        logger.info(f"✅ Loaded {len(all_stats)} player season averages")
        return all_stats
    except Exception as e:
        logger.error(f"❌ Error fetching season averages: {e}")
        import traceback
        traceback.print_exc()
        return []

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
    return round(tusg, 2)

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
    return round(pvr, 2)

def calculate_underrated_score(pvr, tusg, mpg):
    """
    Calculate Underrated Score
    
    Formula: (PVR / TUSG%) × (Minutes Potential)
    Minutes Potential = (30 - MPG)
    
    Higher score = More underrated
    - High PVR (efficient)
    - Low TUSG% (not high usage)
    - Low MPG (untapped potential)
    """
    if tusg == 0:
        return 0.0
    
    minutes_potential = max(30 - mpg, 0)
    
    underrated_score = (pvr / tusg) * minutes_potential
    
    return round(underrated_score, 4)

def get_underrated_stars(min_pvr=15.0, max_tusg=25.0, max_mpg=30.0):
    """
    Discover underrated/hidden gem players
    
    Criteria:
    - PVR > min_pvr (default 15.0) - Elite efficiency
    - TUSG% < max_tusg (default 25.0) - Low usage
    - MPG < max_mpg (default 30.0) - Limited minutes
    
    Returns:
    - List of players sorted by underrated score
    """
    logger.info(f"\n🔍 Searching for underrated stars with:")
    logger.info(f"   PVR > {min_pvr}, TUSG% < {max_tusg}%, MPG < {max_mpg}")
    
    # Fetch current season data
    all_players = get_player_season_averages(2025)
    
    if not all_players:
        logger.warning("⚠️ No player data available")
        return []
    
    underrated = []
    
    for player in all_players:
        mpg = player.get('min', 0)
        team_abbr = player.get('team')
        
        # Skip if no team or insufficient minutes
        if not team_abbr or mpg < 10:
            continue
        
        # Get team pace
        team_pace = TEAM_PACE.get(team_abbr, 99.5)
        
        # Calculate TUSG% and PVR
        tusg = calculate_player_tusg(player, team_pace)
        pvr = calculate_player_pvr(player)
        
        # Apply filters
        if pvr <= min_pvr:
            continue
        if tusg >= max_tusg:
            continue
        if mpg >= max_mpg:
            continue
        
        # Calculate underrated score
        underrated_score = calculate_underrated_score(pvr, tusg, mpg)
        
        underrated.append({
            'player': player['player_name'],
            'team': team_abbr,
            'mpg': round(mpg, 1),
            'ppg': round(player['pts'], 1),
            'apg': round(player['ast'], 1),
            'rpg': round(player.get('reb', 0), 1),
            'fga': round(player['fga'], 1),
            'tov': round(player['tov'], 1),
            'fta': round(player['fta'], 1),
            'pvr': pvr,
            'tusg': tusg,
            'underrated_score': underrated_score,
            'minutes_potential': round(max(30 - mpg, 0), 1)
        })
    
    # Sort by underrated score (highest first)
    underrated.sort(key=lambda x: x['underrated_score'], reverse=True)
    
    # Add ranking
    for idx, player in enumerate(underrated, 1):
        player['rank'] = idx
    
    logger.info(f"✅ Found {len(underrated)} underrated stars")
    
    return underrated

def get_featured_underrated_player():
    """
    Get the featured underrated player of the week
    
    Algorithm:
    - Rotate weekly based on week number
    - Always pick from top 10 underrated players
    """
    underrated = get_underrated_stars()
    
    if not underrated:
        return None
    
    # Rotate through top 10 based on week number
    week_number = datetime.now().isocalendar()[1]
    top_10 = underrated[:min(10, len(underrated))]
    
    featured_index = week_number % len(top_10)
    featured = top_10[featured_index]
    
    return featured

def analyze_why_underrated(player_data):
    """
    Generate analysis of why a player is underrated
    """
    reasons = []
    
    pvr = player_data['pvr']
    tusg = player_data['tusg']
    mpg = player_data['mpg']
    ppg = player_data['ppg']
    apg = player_data['apg']
    underrated_score = player_data['underrated_score']
    
    # Elite efficiency
    if pvr > 20.0:
        reasons.append(f"Elite PVR of {pvr:.1f} (top-tier efficiency)")
    elif pvr > 15.0:
        reasons.append(f"Strong PVR of {pvr:.1f} (highly efficient)")
    
    # Low usage advantage
    if tusg < 20.0:
        reasons.append(f"Ultra-low usage ({tusg:.1f}% TUSG) - not the primary option")
    elif tusg < 25.0:
        reasons.append(f"Low usage ({tusg:.1f}% TUSG) - secondary role player")
    
    # Minutes potential
    minutes_potential = player_data.get('minutes_potential', 0)
    if minutes_potential > 10:
        reasons.append(f"Playing only {mpg:.1f} MPG - {minutes_potential:.1f} minutes of untapped potential")
    elif minutes_potential > 5:
        reasons.append(f"Limited to {mpg:.1f} MPG - room for increased role")
    
    # Underrated score highlight
    if underrated_score > 10.0:
        reasons.append(f"Exceptional underrated score: {underrated_score:.2f} (hidden gem alert!)")
    elif underrated_score > 5.0:
        reasons.append(f"Strong underrated score: {underrated_score:.2f}")
    
    # Well-rounded game
    if ppg > 10.0 and apg > 3.0:
        reasons.append(f"Balanced production: {ppg:.1f} PPG + {apg:.1f} APG")
    
    return reasons

def get_fantasy_implications(player_data):
    """
    Analyze fantasy basketball implications
    """
    implications = []
    
    pvr = player_data['pvr']
    mpg = player_data['mpg']
    ppg = player_data['ppg']
    apg = player_data['apg']
    rpg = player_data.get('rpg', 0)
    tusg = player_data['tusg']
    
    # High efficiency fantasy asset
    if pvr > 20.0:
        implications.append(f"🏆 Elite fantasy efficiency (PVR: {pvr:.1f})")
    elif pvr > 15.0:
        implications.append(f"💎 Strong fantasy efficiency (PVR: {pvr:.1f})")
    
    # Upside potential
    if mpg < 25:
        implications.append(f"📈 Huge upside if minutes increase (currently {mpg:.1f} MPG)")
    
    # Per-minute production
    if pvr > 18.0 and mpg < 28:
        implications.append(f"⚡ Elite per-minute production - watch for injury opportunities")
    
    # Low usage = consistent
    if tusg < 22.0:
        implications.append(f"✅ Consistent role ({tusg:.1f}% usage) - predictable fantasy output")
    
    # Assist value
    if apg > 3.5:
        implications.append(f"🎯 Valuable assist provider ({apg:.1f} APG)")
    
    # Scoring upside
    if ppg > 12.0 and mpg < 28:
        implications.append(f"🔥 Scoring upside if given more minutes ({ppg:.1f} PPG in {mpg:.1f} MPG)")
    
    return implications

def get_betting_implications(player_data):
    """
    Analyze betting implications
    """
    implications = []
    
    player = player_data['player']
    pvr = player_data['pvr']
    ppg = player_data['ppg']
    apg = player_data['apg']
    rpg = player_data.get('rpg', 0)
    mpg = player_data['mpg']
    
    # Player props
    if pvr > 18.0:
        pra = ppg + rpg + apg
        implications.append(f"Look for OVER on PRA props (averaging {pra:.1f} in limited minutes)")
    
    # Injury replacement value
    if pvr > 15.0 and mpg < 28:
        implications.append(f"Prime injury replacement candidate - production will spike with starter minutes")
    
    # Team spread impact
    if pvr > 20.0:
        implications.append(f"Strong impact player - monitor {player_data['team']} spreads when active vs DNP")
    
    # Under-the-radar value
    implications.append(f"Underpriced in player performance markets due to limited minutes")
    
    # Blowout opportunity
    if mpg < 25:
        implications.append(f"Watch for garbage time opportunities in blowouts for prop value")
    
    return implications

def get_team_fit_analysis(player_data):
    """
    Analyze team fit and trade value
    """
    analysis = []
    
    pvr = player_data['pvr']
    tusg = player_data['tusg']
    mpg = player_data['mpg']
    team = player_data['team']
    
    # Current team role
    if mpg < 20:
        analysis.append(f"Currently buried in {team}'s rotation ({mpg:.1f} MPG)")
    elif mpg < 28:
        analysis.append(f"Playing secondary role for {team} ({mpg:.1f} MPG)")
    
    # Trade value
    if pvr > 18.0 and tusg < 22.0:
        analysis.append(f"High trade value: Efficient, low-usage players fit any system")
    
    # Ideal fit
    if pvr > 20.0:
        analysis.append(f"Would thrive on a team needing efficient role players")
    
    if tusg < 20.0:
        analysis.append(f"Perfect complementary piece for star-driven teams")
    
    # Upside scenario
    if pvr > 15.0 and mpg < 25:
        analysis.append(f"Could be a breakout candidate with a trade to a minutes-rich situation")
    
    return analysis

def generate_social_media_snippet(player_data):
    """
    Generate social media promotion snippet
    """
    player = player_data['player']
    team = player_data['team']
    pvr = player_data['pvr']
    tusg = player_data['tusg']
    mpg = player_data['mpg']
    ppg = player_data['ppg']
    underrated_score = player_data['underrated_score']
    
    snippets = {
        'twitter': f"🔥 UNDERRATED STAR ALERT 🔥\n\n"
                  f"{player} ({team})\n"
                  f"📊 PVR: {pvr:.1f} (ELITE)\n"
                  f"⚡ TUSG: {tusg:.1f}% (LOW USAGE)\n"
                  f"⏰ MPG: {mpg:.1f} (UNTAPPED)\n"
                  f"💎 Underrated Score: {underrated_score:.2f}\n\n"
                  f"Averaging {ppg:.1f} PPG in limited minutes!\n"
                  f"Watch this hidden gem 👀\n\n"
                  f"#NBA #HiddenGems #TaylorVectorTerminal",
        
        'instagram': f"💎 HIDDEN GEM ALERT 💎\n\n"
                    f"{player} | {team}\n\n"
                    f"PVR: {pvr:.1f} 🔥\n"
                    f"TUSG%: {tusg:.1f}% ⚡\n"
                    f"Minutes: {mpg:.1f} ⏰\n\n"
                    f"Elite efficiency in a limited role.\n"
                    f"This player is UNDERVALUED.\n\n"
                    f"Underrated Score: {underrated_score:.2f}\n\n"
                    f"#NBA #Analytics #Basketball #HiddenGems #PVR",
        
        'reddit': f"**🔥 Underrated Star of the Week: {player} ({team}) 🔥**\n\n"
                 f"**Why you should be watching:**\n\n"
                 f"* **PVR:** {pvr:.1f} (elite efficiency)\n"
                 f"* **TUSG%:** {tusg:.1f}% (low usage - not primary option)\n"
                 f"* **MPG:** {mpg:.1f} (limited minutes = untapped potential)\n"
                 f"* **PPG:** {ppg:.1f}\n\n"
                 f"**Underrated Score:** {underrated_score:.2f}\n\n"
                 f"This player is producing at an elite level in a secondary role. "
                 f"If given more minutes or traded to a better situation, we could see a major breakout.\n\n"
                 f"What do you think? Sleeper pick or overrated?",
        
        'tiktok': f"HIDDEN GEM ALERT 🚨\n\n"
                 f"{player} - {team}\n\n"
                 f"Elite PVR: {pvr:.1f}\n"
                 f"Low Usage: {tusg:.1f}%\n"
                 f"Only {mpg:.1f} MPG\n\n"
                 f"Underrated Score: {underrated_score:.2f}\n\n"
                 f"This player is COOKING in limited minutes 👨‍🍳\n"
                 f"Watch for the breakout 📈"
    }
    
    return snippets

def generate_weekly_report(output_filename=None):
    """
    Generate weekly underrated stars report (JSON format)
    
    Returns:
    - Path to generated report file
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Get featured player and top 10 hidden gems
    featured = get_featured_underrated_player()
    top_10 = get_underrated_stars()[:10]
    
    if not featured:
        logger.warning("⚠️ No underrated players found")
        return None
    
    if not output_filename:
        week_number = datetime.now().isocalendar()[1]
        output_filename = f"underrated_stars_week_{week_number}_2025.json"
    
    filepath = os.path.join(REPORTS_DIR, output_filename)
    
    # Generate analysis for featured player
    analysis = {
        'why_underrated': analyze_why_underrated(featured),
        'fantasy_implications': get_fantasy_implications(featured),
        'betting_implications': get_betting_implications(featured),
        'team_fit_analysis': get_team_fit_analysis(featured)
    }
    
    # Generate social media snippets
    social_snippets = generate_social_media_snippet(featured)
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'week_number': datetime.now().isocalendar()[1],
        'featured_player': featured,
        'analysis': analysis,
        'social_media_snippets': social_snippets,
        'top_10_hidden_gems': top_10,
        'criteria': {
            'min_pvr': 15.0,
            'max_tusg': 25.0,
            'max_mpg': 30.0
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"✅ Weekly report saved: {filepath}")
    
    return filepath

def get_all_underrated_stats():
    """
    Get comprehensive stats about underrated players
    """
    underrated = get_underrated_stars()
    
    if not underrated:
        return {}
    
    return {
        'total_hidden_gems': len(underrated),
        'avg_pvr': round(sum(p['pvr'] for p in underrated) / len(underrated), 2),
        'avg_tusg': round(sum(p['tusg'] for p in underrated) / len(underrated), 2),
        'avg_mpg': round(sum(p['mpg'] for p in underrated) / len(underrated), 2),
        'avg_underrated_score': round(sum(p['underrated_score'] for p in underrated) / len(underrated), 4),
        'top_pvr': max(p['pvr'] for p in underrated),
        'lowest_tusg': min(p['tusg'] for p in underrated),
        'lowest_mpg': min(p['mpg'] for p in underrated)
    }

if __name__ == '__main__':
    print("\n💎 UNDERRATED PVR STARS SERIES - Discovery Engine")
    print("=" * 80)
    
    # Get underrated stars
    underrated = get_underrated_stars()
    
    print(f"\nFound {len(underrated)} hidden gem players")
    print(f"Criteria: PVR > 15, TUSG% < 25%, MPG < 30")
    print("=" * 80)
    
    # Show top 10
    if underrated:
        print("\n🏆 TOP 10 HIDDEN GEMS (By Underrated Score)")
        print("-" * 80)
        for player in underrated[:10]:
            print(f"{player['rank']:2d}. {player['player']:25s} ({player['team']}) | "
                  f"PVR: {player['pvr']:6.2f} | TUSG: {player['tusg']:5.2f}% | "
                  f"MPG: {player['mpg']:5.1f} | Score: {player['underrated_score']:.4f}")
        
        # Featured player analysis
        featured = get_featured_underrated_player()
        if featured:
            print(f"\n⭐ FEATURED PLAYER THIS WEEK: {featured['player']} ({featured['team']})")
            print("-" * 80)
            print(f"PVR: {featured['pvr']:.2f} | TUSG: {featured['tusg']:.2f}% | "
                  f"MPG: {featured['mpg']:.1f} | Underrated Score: {featured['underrated_score']:.4f}")
            
            print("\n🔍 WHY UNDERRATED:")
            for reason in analyze_why_underrated(featured):
                print(f"  • {reason}")
            
            print("\n🏀 FANTASY IMPLICATIONS:")
            for implication in get_fantasy_implications(featured):
                print(f"  • {implication}")
            
            print("\n💰 BETTING IMPLICATIONS:")
            for implication in get_betting_implications(featured):
                print(f"  • {implication}")
            
            print("\n🔄 TEAM FIT & TRADE VALUE:")
            for item in get_team_fit_analysis(featured):
                print(f"  • {item}")
            
            print("\n📱 SOCIAL MEDIA SNIPPET (Twitter):")
            print("-" * 80)
            snippets = generate_social_media_snippet(featured)
            print(snippets['twitter'])
        
        # Stats
        stats = get_all_underrated_stats()
        print("\n📊 HIDDEN GEMS STATISTICS")
        print("-" * 80)
        print(f"Total Hidden Gems: {stats['total_hidden_gems']}")
        print(f"Average PVR: {stats['avg_pvr']:.2f}")
        print(f"Average TUSG%: {stats['avg_tusg']:.2f}%")
        print(f"Average MPG: {stats['avg_mpg']:.1f}")
        print(f"Average Underrated Score: {stats['avg_underrated_score']:.4f}")
        
        # Generate report
        print("\n📝 Generating weekly report...")
        filepath = generate_weekly_report()
        if filepath:
            print(f"✅ Report saved: {filepath}")
    else:
        print("\n⚠️ No underrated players found matching criteria")
