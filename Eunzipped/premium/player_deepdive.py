"""
TAYLOR VECTOR TERMINAL - Weekly Player Deep Dive Generator
Comprehensive one-player metric breakdowns with career analysis
"""

import requests
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(SCRIPT_DIR, 'reports')
DEEPDIVES_DIR = os.path.join(SCRIPT_DIR, 'deepdives')
ARCHIVE_DIR = os.path.join(DEEPDIVES_DIR, 'archive')
MARKDOWN_DIR = os.path.join(DEEPDIVES_DIR, 'markdown')
VIDEO_SCRIPTS_DIR = os.path.join(DEEPDIVES_DIR, 'video_scripts')

# Team pace data (2024-25 season)
TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

# Historical pace by era
HISTORICAL_PACE = {
    range(1950, 1970): 115.0,
    range(1970, 1990): 107.0,
    range(1990, 2010): 95.0,
    range(2010, 2020): 98.0,
    range(2020, 2030): 99.5
}

# Position classifications
POSITIONS = {
    'PG': 'Point Guard',
    'SG': 'Shooting Guard', 
    'SF': 'Small Forward',
    'PF': 'Power Forward',
    'C': 'Center',
    'G': 'Guard',
    'F': 'Forward',
    'G-F': 'Guard-Forward',
    'F-G': 'Forward-Guard',
    'F-C': 'Forward-Center',
    'C-F': 'Center-Forward'
}

def get_era_pace(season):
    """Get average NBA pace for a given season"""
    for year_range, pace in HISTORICAL_PACE.items():
        if season in year_range:
            return pace
    return 99.5

def calculate_tusg(stats, team_abbr=None, season=None):
    """
    Calculate TUSG% for player
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
    """
    mp = stats.get('min', 0) or stats.get('mpg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    # Get team pace
    if team_abbr and team_abbr in TEAM_PACE:
        team_pace = TEAM_PACE[team_abbr]
    elif season:
        team_pace = get_era_pace(season)
    else:
        team_pace = 99.5
    
    if mp == 0 or team_pace == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * team_pace
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_pvr(stats):
    """
    Calculate PVR for player
    PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
    """
    pts = stats.get('pts', 0) or stats.get('ppg', 0)
    ast = stats.get('ast', 0) or stats.get('apg', 0)
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

def fetch_player_career_stats(player_slug):
    """Fetch player's career statistics from nbaStats API"""
    all_seasons = []
    
    # Try to fetch all available seasons (2015-2025 as reasonable range)
    for season in range(2015, 2026):
        try:
            url = f"https://api.server.nbaapi.com/api/playertotals?season={season}&pageSize=1000"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('data', [])
                
                # Find player in this season
                player_data = None
                for player in players:
                    if player.get('slug') == player_slug or player.get('playerName', '').lower() == player_slug.lower():
                        player_data = player
                        break
                
                if player_data and player_data.get('games', 0) > 0:
                    games = player_data.get('games', 1)
                    
                    season_stats = {
                        'season': season,
                        'season_str': f"{season-1}-{str(season)[-2:]}",
                        'team': player_data.get('team', 'UNK'),
                        'games': games,
                        'min': player_data.get('minutesPg', 0),
                        'pts': player_data.get('points', 0) / games,
                        'ast': player_data.get('assists', 0) / games,
                        'reb': player_data.get('rebounds', 0) / games,
                        'tov': player_data.get('turnovers', 0) / games,
                        'fga': player_data.get('fieldAttempts', 0) / games,
                        'fgm': player_data.get('fieldGoals', 0) / games,
                        'fta': player_data.get('ftAttempts', 0) / games,
                        'ftm': player_data.get('freeThrows', 0) / games,
                        'tpa': player_data.get('threeAttempts', 0) / games,
                        'tpm': player_data.get('threeGoals', 0) / games
                    }
                    
                    # Calculate metrics
                    season_stats['tusg'] = calculate_tusg(season_stats, season_stats['team'], season)
                    season_stats['pvr'] = calculate_pvr(season_stats)
                    season_stats['fg_pct'] = (season_stats['fgm'] / season_stats['fga'] * 100) if season_stats['fga'] > 0 else 0
                    season_stats['ft_pct'] = (season_stats['ftm'] / season_stats['fta'] * 100) if season_stats['fta'] > 0 else 0
                    season_stats['tp_pct'] = (season_stats['tpm'] / season_stats['tpa'] * 100) if season_stats['tpa'] > 0 else 0
                    
                    all_seasons.append(season_stats)
        except Exception as e:
            print(f"Error fetching season {season}: {e}")
            continue
    
    return all_seasons

def get_available_players():
    """Get list of all available players from current season"""
    try:
        url = "https://api.server.nbaapi.com/api/playertotals?season=2025&pageSize=1000"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            players = data.get('data', [])
            
            player_list = []
            for player in players:
                if player.get('games', 0) > 0:
                    player_list.append({
                        'slug': player.get('slug'),
                        'name': player.get('playerName'),
                        'team': player.get('team')
                    })
            
            player_list.sort(key=lambda x: x['name'])
            return player_list
    except Exception as e:
        print(f"Error fetching players: {e}")
        return []

def analyze_strengths_weaknesses(career_stats):
    """Analyze player's strengths and weaknesses based on metrics"""
    if not career_stats:
        return {'strengths': [], 'weaknesses': [], 'summary': ''}
    
    # Get latest season stats
    latest = career_stats[-1]
    
    # Calculate career averages
    career_tusg = sum(s['tusg'] for s in career_stats) / len(career_stats)
    career_pvr = sum(s['pvr'] for s in career_stats) / len(career_stats)
    career_ppg = sum(s['pts'] for s in career_stats) / len(career_stats)
    career_apg = sum(s['ast'] for s in career_stats) / len(career_stats)
    career_fg_pct = sum(s['fg_pct'] for s in career_stats) / len(career_stats)
    
    strengths = []
    weaknesses = []
    
    # TUSG analysis
    if career_tusg > 30:
        strengths.append(f"Elite usage rate ({career_tusg:.1f}% TUSG) - primary offensive option")
    elif career_tusg > 25:
        strengths.append(f"High usage rate ({career_tusg:.1f}% TUSG) - consistent offensive role")
    elif career_tusg < 15:
        weaknesses.append(f"Low usage rate ({career_tusg:.1f}% TUSG) - limited offensive opportunities")
    
    # PVR analysis
    if career_pvr > 15:
        strengths.append(f"Elite efficiency ({career_pvr:.1f} PVR) - exceptional possession value")
    elif career_pvr > 10:
        strengths.append(f"High efficiency ({career_pvr:.1f} PVR) - above-average production")
    elif career_pvr < 5:
        weaknesses.append(f"Below-average efficiency ({career_pvr:.1f} PVR) - room for improvement")
    
    # Scoring analysis
    if career_ppg > 25:
        strengths.append(f"Elite scorer ({career_ppg:.1f} PPG career average)")
    elif career_ppg > 20:
        strengths.append(f"High-volume scorer ({career_ppg:.1f} PPG)")
    
    # Playmaking analysis
    if career_apg > 7:
        strengths.append(f"Elite playmaker ({career_apg:.1f} APG) - exceptional court vision")
    elif career_apg > 5:
        strengths.append(f"Strong playmaking ({career_apg:.1f} APG)")
    
    # Shooting efficiency
    if career_fg_pct > 50:
        strengths.append(f"Efficient shooter ({career_fg_pct:.1f}% FG) - high conversion rate")
    elif career_fg_pct < 42:
        weaknesses.append(f"Below-average shooting ({career_fg_pct:.1f}% FG)")
    
    # Trend analysis
    if len(career_stats) >= 3:
        recent_tusg = sum(s['tusg'] for s in career_stats[-3:]) / 3
        early_tusg = sum(s['tusg'] for s in career_stats[:3]) / min(3, len(career_stats))
        
        if recent_tusg > early_tusg + 5:
            strengths.append("Increasing usage - growing offensive role")
        elif recent_tusg < early_tusg - 5:
            weaknesses.append("Declining usage - reduced offensive opportunities")
    
    summary = f"Career averages: {career_tusg:.1f}% TUSG, {career_pvr:.1f} PVR, {career_ppg:.1f} PPG, {career_apg:.1f} APG"
    
    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'summary': summary
    }

def fetch_position_peers(player_position, current_season=2025, min_games=10):
    """Fetch players in the same position for peer comparison"""
    try:
        url = f"https://api.server.nbaapi.com/api/playertotals?season={current_season}&pageSize=1000"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            players = data.get('data', [])
            
            peers = []
            for player in players:
                if player.get('games', 0) >= min_games:
                    games = player.get('games', 1)
                    stats = {
                        'name': player.get('playerName'),
                        'team': player.get('team', 'UNK'),
                        'games': games,
                        'min': player.get('minutesPg', 0),
                        'pts': player.get('points', 0) / games,
                        'ast': player.get('assists', 0) / games,
                        'reb': player.get('rebounds', 0) / games,
                        'tov': player.get('turnovers', 0) / games,
                        'fga': player.get('fieldAttempts', 0) / games,
                        'fta': player.get('ftAttempts', 0) / games
                    }
                    stats['tusg'] = calculate_tusg(stats, stats['team'], current_season)
                    stats['pvr'] = calculate_pvr(stats)
                    peers.append(stats)
            
            return peers
    except Exception as e:
        print(f"Error fetching position peers: {e}")
        return []

def analyze_position_peer_comparison(player_stats, player_name, position='All'):
    """Compare player to position peers"""
    if not player_stats:
        return {'rank': 0, 'percentile': 0, 'peers_analyzed': 0, 'comparison': ''}
    
    latest_stats = player_stats[-1]
    player_tusg = latest_stats['tusg']
    player_pvr = latest_stats['pvr']
    
    peers = fetch_position_peers(position, latest_stats['season'])
    
    if not peers:
        return {'rank': 0, 'percentile': 0, 'peers_analyzed': 0, 'comparison': 'No peer data available'}
    
    peers_sorted_tusg = sorted(peers, key=lambda x: x['tusg'], reverse=True)
    peers_sorted_pvr = sorted(peers, key=lambda x: x['pvr'], reverse=True)
    
    tusg_rank = next((i+1 for i, p in enumerate(peers_sorted_tusg) if p['name'] == player_name), len(peers))
    pvr_rank = next((i+1 for i, p in enumerate(peers_sorted_pvr) if p['name'] == player_name), len(peers))
    
    tusg_percentile = ((len(peers) - tusg_rank + 1) / len(peers)) * 100
    pvr_percentile = ((len(peers) - pvr_rank + 1) / len(peers)) * 100
    
    avg_tusg = sum(p['tusg'] for p in peers) / len(peers)
    avg_pvr = sum(p['pvr'] for p in peers) / len(peers)
    
    comparison = f"""
    {player_name} ranks #{tusg_rank} in TUSG% (Top {tusg_percentile:.0f}%) and #{pvr_rank} in PVR (Top {pvr_percentile:.0f}%) among {len(peers)} active players.
    
    League averages: {avg_tusg:.1f}% TUSG, {avg_pvr:.1f} PVR
    {player_name}: {player_tusg:.1f}% TUSG ({'+' if player_tusg > avg_tusg else ''}{player_tusg - avg_tusg:.1f} vs avg), {player_pvr:.1f} PVR ({'+' if player_pvr > avg_pvr else ''}{player_pvr - avg_pvr:.1f} vs avg)
    """
    
    return {
        'tusg_rank': tusg_rank,
        'pvr_rank': pvr_rank,
        'tusg_percentile': tusg_percentile,
        'pvr_percentile': pvr_percentile,
        'peers_analyzed': len(peers),
        'avg_tusg': avg_tusg,
        'avg_pvr': avg_pvr,
        'comparison': comparison.strip()
    }

def analyze_betting_implications(career_stats, player_name):
    """Analyze betting implications based on metrics"""
    if not career_stats:
        return {'implications': [], 'summary': 'No data available for betting analysis'}
    
    latest = career_stats[-1]
    implications = []
    
    if latest['tusg'] > 30:
        implications.append(f"HIGH USAGE ALERT: {player_name} commands {latest['tusg']:.1f}% TUSG - expect high shot volume in every game")
        implications.append(f"PROP BETS: Strong candidate for over on points/FGA props due to elite usage")
    
    if latest['pvr'] > 15:
        implications.append(f"EFFICIENCY EDGE: {latest['pvr']:.1f} PVR indicates elite value per possession")
        implications.append(f"GAME IMPACT: High PVR correlates with team performance - consider team spread bets")
    elif latest['pvr'] < 8:
        implications.append(f"EFFICIENCY CONCERN: {latest['pvr']:.1f} PVR below league average - fade props on efficiency-based markets")
    
    if len(career_stats) >= 5:
        recent_tusg = [s['tusg'] for s in career_stats[-5:]]
        tusg_trend = (recent_tusg[-1] - recent_tusg[0]) / 5
        
        if tusg_trend > 1:
            implications.append(f"RISING USAGE: TUSG trending up ({tusg_trend:+.1f}%/season) - monitor for increased offensive role")
        elif tusg_trend < -1:
            implications.append(f"DECLINING USAGE: TUSG trending down ({tusg_trend:+.1f}%/season) - be cautious on volume props")
    
    if latest['ast'] > 7:
        implications.append(f"PLAYMAKING PREMIUM: {latest['ast']:.1f} APG - strong assist prop candidate, impacts team offense")
    
    consistency = None
    if len(career_stats) >= 3:
        recent_pvrs = [s['pvr'] for s in career_stats[-3:]]
        pvr_std = (sum((x - sum(recent_pvrs)/len(recent_pvrs))**2 for x in recent_pvrs) / len(recent_pvrs))**0.5
        
        if pvr_std < 2:
            implications.append(f"CONSISTENCY: Low PVR variance ({pvr_std:.1f}) - reliable for same game parlays")
            consistency = 'High'
        elif pvr_std > 4:
            implications.append(f"VOLATILITY: High PVR variance ({pvr_std:.1f}) - risky for props, good for live betting adjustments")
            consistency = 'Low'
        else:
            consistency = 'Moderate'
    
    summary = f"{player_name} betting profile: {latest['tusg']:.1f}% TUSG (usage), {latest['pvr']:.1f} PVR (efficiency), {consistency or 'Unknown'} consistency"
    
    return {
        'implications': implications,
        'summary': summary,
        'tusg': latest['tusg'],
        'pvr': latest['pvr'],
        'consistency': consistency
    }

def create_monthly_performance_chart(career_stats):
    """Create monthly performance breakdown chart (simulated from season data)"""
    if not career_stats or len(career_stats) < 2:
        return None
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    seasons = [s['season_str'] for s in career_stats]
    tusg_values = [s['tusg'] for s in career_stats]
    pvr_values = [s['pvr'] for s in career_stats]
    ppg_values = [s['pts'] for s in career_stats]
    
    colors_tusg = ['#00d4ff' if x > sum(tusg_values)/len(tusg_values) else '#ff4444' for x in tusg_values]
    colors_pvr = ['#00ff88' if x > sum(pvr_values)/len(pvr_values) else '#ff4444' for x in pvr_values]
    
    ax1.bar(seasons, tusg_values, color=colors_tusg, alpha=0.7, edgecolor='black')
    ax1.axhline(y=sum(tusg_values)/len(tusg_values), color='white', linestyle='--', linewidth=2, label='Career Avg')
    ax1.set_ylabel('TUSG%', fontsize=12, fontweight='bold')
    ax1.set_title('Season TUSG% Performance (Above/Below Career Average)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    ax2_twin = ax2.twinx()
    width = 0.35
    x = range(len(seasons))
    
    bars1 = ax2.bar([i - width/2 for i in x], pvr_values, width, color=colors_pvr, alpha=0.7, edgecolor='black', label='PVR')
    ax2_line = ax2_twin.plot(x, ppg_values, marker='o', color='#ffaa00', linewidth=2, markersize=8, label='PPG')
    
    ax2.set_ylabel('PVR', fontsize=12, fontweight='bold')
    ax2_twin.set_ylabel('PPG', fontsize=12, fontweight='bold', color='#ffaa00')
    ax2.set_xlabel('Season', fontsize=12, fontweight='bold')
    ax2.set_title('Season PVR & Scoring Performance', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(seasons, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def create_career_chart(career_stats, chart_type='tusg'):
    """Create career progression chart"""
    if not career_stats:
        return None
    
    seasons = [s['season_str'] for s in career_stats]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if chart_type == 'tusg':
        values = [s['tusg'] for s in career_stats]
        ax.plot(seasons, values, marker='o', linewidth=2, color='#00d4ff', markersize=8)
        ax.set_ylabel('TUSG%', fontsize=12, fontweight='bold')
        ax.set_title('Career TUSG% Progression', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    elif chart_type == 'pvr':
        values = [s['pvr'] for s in career_stats]
        ax.plot(seasons, values, marker='o', linewidth=2, color='#00ff88', markersize=8)
        ax.set_ylabel('PVR', fontsize=12, fontweight='bold')
        ax.set_title('Career PVR Progression', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    elif chart_type == 'combined':
        tusg_values = [s['tusg'] for s in career_stats]
        pvr_values = [s['pvr'] for s in career_stats]
        
        ax2 = ax.twinx()
        
        line1 = ax.plot(seasons, tusg_values, marker='o', linewidth=2, color='#00d4ff', markersize=8, label='TUSG%')
        line2 = ax2.plot(seasons, pvr_values, marker='s', linewidth=2, color='#00ff88', markersize=8, label='PVR')
        
        ax.set_ylabel('TUSG%', fontsize=12, fontweight='bold', color='#00d4ff')
        ax2.set_ylabel('PVR', fontsize=12, fontweight='bold', color='#00ff88')
        ax.set_title('Career Metrics Progression', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left')
    
    ax.set_xlabel('Season', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def generate_player_deepdive_pdf(player_name, career_stats, output_filename=None):
    """Generate comprehensive player deep dive PDF report"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    if not output_filename:
        safe_name = player_name.replace(' ', '_').lower()
        output_filename = f"player_deepdive_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    filepath = os.path.join(REPORTS_DIR, output_filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=36)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#00d4ff'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8
    )
    
    # Header
    title = Paragraph("TAYLOR VECTOR TERMINAL", title_style)
    elements.append(title)
    
    subtitle = Paragraph(f"Weekly Player Deep Dive: {player_name}", subtitle_style)
    elements.append(subtitle)
    
    date_text = Paragraph(
        f"<b>Report Date:</b> {datetime.now().strftime('%A, %B %d, %Y')}",
        normal_style
    )
    elements.append(date_text)
    elements.append(Spacer(1, 0.3*inch))
    
    if not career_stats:
        elements.append(Paragraph("No career statistics available for this player.", normal_style))
    else:
        # Career Overview
        elements.append(Paragraph("Career Overview", heading_style))
        
        total_games = sum(s['games'] for s in career_stats)
        total_seasons = len(career_stats)
        career_tusg = sum(s['tusg'] for s in career_stats) / len(career_stats)
        career_pvr = sum(s['pvr'] for s in career_stats) / len(career_stats)
        career_ppg = sum(s['pts'] for s in career_stats) / len(career_stats)
        career_apg = sum(s['ast'] for s in career_stats) / len(career_stats)
        career_rpg = sum(s['reb'] for s in career_stats) / len(career_stats)
        
        overview_data = [
            ['Metric', 'Value'],
            ['Total Seasons', str(total_seasons)],
            ['Total Games', str(total_games)],
            ['Career TUSG%', f"{career_tusg:.2f}%"],
            ['Career PVR', f"{career_pvr:.2f}"],
            ['Career PPG', f"{career_ppg:.1f}"],
            ['Career APG', f"{career_apg:.1f}"],
            ['Career RPG', f"{career_rpg:.1f}"]
        ]
        
        overview_table = Table(overview_data, colWidths=[3*inch, 2.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(overview_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Career Progression Chart
        elements.append(Paragraph("Career Metrics Progression", heading_style))
        
        chart_img = create_career_chart(career_stats, 'combined')
        if chart_img:
            img = Image(chart_img, width=6.5*inch, height=4*inch)
            elements.append(img)
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(PageBreak())
        
        # Season-by-Season Breakdown
        elements.append(Paragraph("Season-by-Season Breakdown", heading_style))
        
        season_data = [['Season', 'Team', 'Games', 'MPG', 'PPG', 'APG', 'TUSG%', 'PVR']]
        
        for season in career_stats:
            season_data.append([
                season['season_str'],
                season['team'],
                str(season['games']),
                f"{season['min']:.1f}",
                f"{season['pts']:.1f}",
                f"{season['ast']:.1f}",
                f"{season['tusg']:.1f}%",
                f"{season['pvr']:.1f}"
            ])
        
        season_table = Table(season_data, colWidths=[0.8*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.6*inch])
        season_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(season_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Strengths & Weaknesses Analysis
        analysis = analyze_strengths_weaknesses(career_stats)
        
        elements.append(Paragraph("Strengths & Weaknesses Analysis", heading_style))
        elements.append(Paragraph(analysis['summary'], normal_style))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("<b>Key Strengths:</b>", normal_style))
        for strength in analysis['strengths']:
            elements.append(Paragraph(f"• {strength}", normal_style))
        
        elements.append(Spacer(1, 0.1*inch))
        
        if analysis['weaknesses']:
            elements.append(Paragraph("<b>Areas for Improvement:</b>", normal_style))
            for weakness in analysis['weaknesses']:
                elements.append(Paragraph(f"• {weakness}", normal_style))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Historical Context
        elements.append(Paragraph("Historical Context", heading_style))
        
        context_text = f"""
        <b>{player_name}</b> has played {total_seasons} NBA seasons with an average TUSG% of {career_tusg:.2f}% 
        and PVR of {career_pvr:.2f}. This places them in the 
        {'elite' if career_tusg > 28 else 'high-usage' if career_tusg > 22 else 'moderate-usage'} category 
        for usage rate and the 
        {'exceptional' if career_pvr > 15 else 'above-average' if career_pvr > 10 else 'average'} tier 
        for possession value efficiency.
        """
        
        elements.append(Paragraph(context_text, normal_style))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer = Paragraph(
        f"<i>Generated by Taylor Vector Terminal on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    )
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    return filepath

def generate_markdown_report(player_name, career_stats, peer_comparison, betting_analysis, analysis):
    """Generate markdown report for player deep dive"""
    os.makedirs(MARKDOWN_DIR, exist_ok=True)
    
    safe_name = player_name.replace(' ', '_').lower()
    filename = f"deepdive_{safe_name}_{datetime.now().strftime('%Y%m%d')}.md"
    filepath = os.path.join(MARKDOWN_DIR, filename)
    
    if not career_stats:
        return None
    
    latest = career_stats[-1]
    career_tusg = sum(s['tusg'] for s in career_stats) / len(career_stats)
    career_pvr = sum(s['pvr'] for s in career_stats) / len(career_stats)
    career_ppg = sum(s['pts'] for s in career_stats) / len(career_stats)
    career_apg = sum(s['ast'] for s in career_stats) / len(career_stats)
    
    markdown = f"""# 🏀 TAYLOR VECTOR TERMINAL - Weekly Player Deep Dive

## {player_name}
**Report Date:** {datetime.now().strftime('%A, %B %d, %Y')}

---

## 📊 Career Overview

| Metric | Value |
|--------|-------|
| **Total Seasons** | {len(career_stats)} |
| **Career TUSG%** | {career_tusg:.2f}% |
| **Career PVR** | {career_pvr:.2f} |
| **Career PPG** | {career_ppg:.1f} |
| **Career APG** | {career_apg:.1f} |
| **Latest Season** | {latest['season_str']} ({latest['team']}) |

---

## 📈 Current Season Performance

| Stat | Value |
|------|-------|
| **Games Played** | {latest['games']} |
| **Minutes Per Game** | {latest['min']:.1f} |
| **Points Per Game** | {latest['pts']:.1f} |
| **Assists Per Game** | {latest['ast']:.1f} |
| **Rebounds Per Game** | {latest['reb']:.1f} |
| **TUSG%** | {latest['tusg']:.2f}% |
| **PVR** | {latest['pvr']:.2f} |

---

## 🎯 Strengths & Weaknesses

### 💪 Key Strengths
"""
    
    for strength in analysis['strengths']:
        markdown += f"- {strength}\n"
    
    markdown += "\n### 📉 Areas for Improvement\n"
    
    if analysis['weaknesses']:
        for weakness in analysis['weaknesses']:
            markdown += f"- {weakness}\n"
    else:
        markdown += "- No significant weaknesses identified\n"
    
    markdown += f"\n---\n\n## 🏆 Position Peer Comparison\n\n{peer_comparison['comparison']}\n\n"
    
    markdown += f"""**Rankings:**
- TUSG% Rank: #{peer_comparison.get('tusg_rank', 'N/A')} (Top {peer_comparison.get('tusg_percentile', 0):.0f}%)
- PVR Rank: #{peer_comparison.get('pvr_rank', 'N/A')} (Top {peer_comparison.get('pvr_percentile', 0):.0f}%)
- Total Players Analyzed: {peer_comparison.get('peers_analyzed', 0)}

---

## 💰 Betting Implications

**Summary:** {betting_analysis['summary']}

### Key Betting Insights
"""
    
    for implication in betting_analysis['implications']:
        markdown += f"- {implication}\n"
    
    markdown += f"""
---

## 📅 Season-by-Season Breakdown

| Season | Team | G | MPG | PPG | APG | RPG | TUSG% | PVR |
|--------|------|---|-----|-----|-----|-----|-------|-----|
"""
    
    for season in career_stats:
        markdown += f"| {season['season_str']} | {season['team']} | {season['games']} | {season['min']:.1f} | {season['pts']:.1f} | {season['ast']:.1f} | {season['reb']:.1f} | {season['tusg']:.1f}% | {season['pvr']:.1f} |\n"
    
    markdown += f"""
---

## 🧮 Methodology

**TUSG% (True Usage %)**: Measures the percentage of team possessions used by a player when on the court
- Formula: (FGA + TOV + (FTA × 0.44)) / ((MP/48) × TeamPace) × 100
- Higher = More offensive responsibility

**PVR (Possession Value Rating)**: Measures the value created per possession used
- Formula: [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
- Higher = More efficient production

---

*Generated by Taylor Vector Terminal on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(filepath, 'w') as f:
        f.write(markdown)
    
    return filepath

def generate_video_script(player_name, career_stats, peer_comparison, betting_analysis, analysis):
    """Generate video companion script (bullet points for narration)"""
    os.makedirs(VIDEO_SCRIPTS_DIR, exist_ok=True)
    
    safe_name = player_name.replace(' ', '_').lower()
    filename = f"video_script_{safe_name}_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = os.path.join(VIDEO_SCRIPTS_DIR, filename)
    
    if not career_stats:
        return None
    
    latest = career_stats[-1]
    career_tusg = sum(s['tusg'] for s in career_stats) / len(career_stats)
    career_pvr = sum(s['pvr'] for s in career_stats) / len(career_stats)
    
    script = f"""🎬 VIDEO COMPANION SCRIPT - {player_name} Deep Dive
Generated: {datetime.now().strftime('%A, %B %d, %Y')}

═══════════════════════════════════════════════════════════════

📋 INTRO (0:00-0:30)
═══════════════════════════════════════════════════════════════

• Hook: "Welcome to Taylor Vector Terminal's Weekly Player Deep Dive"
• Today's feature: {player_name}
• Quick tease: "{player_name} is posting a {latest['tusg']:.1f}% TUSG with a {latest['pvr']:.1f} PVR this season"
• What to expect: Career analysis, peer comparison, and betting implications

═══════════════════════════════════════════════════════════════

📊 CAREER OVERVIEW (0:30-1:30)
═══════════════════════════════════════════════════════════════

• {player_name} has been in the league for {len(career_stats)} seasons
• Career averages: {career_tusg:.1f}% TUSG, {career_pvr:.1f} PVR
• Currently with the {latest['team']}
• This season: {latest['pts']:.1f} PPG, {latest['ast']:.1f} APG, {latest['reb']:.1f} RPG

KEY TALKING POINTS:
"""
    
    for strength in analysis['strengths'][:3]:
        script += f"  • {strength}\n"
    
    script += f"""
═══════════════════════════════════════════════════════════════

📈 METRICS DEEP DIVE (1:30-3:00)
═══════════════════════════════════════════════════════════════

TUSG% ANALYSIS:
• Current: {latest['tusg']:.1f}%
• Career Average: {career_tusg:.1f}%
• What this means: {"High usage star" if latest['tusg'] > 28 else "Moderate offensive role" if latest['tusg'] > 20 else "Supporting role"}
• Trend: {"Increasing" if len(career_stats) >= 2 and latest['tusg'] > career_stats[-2]['tusg'] else "Stable" if len(career_stats) >= 2 and abs(latest['tusg'] - career_stats[-2]['tusg']) < 2 else "Decreasing"}

PVR ANALYSIS:
• Current: {latest['pvr']:.1f}
• Career Average: {career_pvr:.1f}
• Efficiency tier: {"Elite" if latest['pvr'] > 15 else "Above Average" if latest['pvr'] > 10 else "Average"}
• Value: {"Exceptional possession value" if latest['pvr'] > 15 else "Solid contributor" if latest['pvr'] > 8 else "Room for improvement"}

═══════════════════════════════════════════════════════════════

🏆 PEER COMPARISON (3:00-4:00)
═══════════════════════════════════════════════════════════════

• TUSG% Rank: #{peer_comparison.get('tusg_rank', 'N/A')} out of {peer_comparison.get('peers_analyzed', 0)} players
• That's Top {peer_comparison.get('tusg_percentile', 0):.0f}% in the league
• PVR Rank: #{peer_comparison.get('pvr_rank', 'N/A')} (Top {peer_comparison.get('pvr_percentile', 0):.0f}%)

VERSUS LEAGUE AVERAGE:
• League Avg TUSG: {peer_comparison.get('avg_tusg', 0):.1f}%
• {player_name}: {latest['tusg']:.1f}% ({'+' if latest['tusg'] > peer_comparison.get('avg_tusg', 0) else ''}{latest['tusg'] - peer_comparison.get('avg_tusg', 0):.1f}%)
• League Avg PVR: {peer_comparison.get('avg_pvr', 0):.1f}
• {player_name}: {latest['pvr']:.1f} ({'+' if latest['pvr'] > peer_comparison.get('avg_pvr', 0) else ''}{latest['pvr'] - peer_comparison.get('avg_pvr', 0):.1f})

═══════════════════════════════════════════════════════════════

💰 BETTING IMPLICATIONS (4:00-5:30)
═══════════════════════════════════════════════════════════════

BETTING PROFILE:
• Usage: {latest['tusg']:.1f}% TUSG
• Efficiency: {latest['pvr']:.1f} PVR
• Consistency: {betting_analysis.get('consistency', 'Unknown')}

KEY BETTING INSIGHTS:
"""
    
    for implication in betting_analysis['implications']:
        script += f"  • {implication}\n"
    
    script += f"""
═══════════════════════════════════════════════════════════════

🎯 CONCLUSION & TAKEAWAYS (5:30-6:00)
═══════════════════════════════════════════════════════════════

SUMMARY POINTS:
• {player_name} is a {
    "high-usage, high-efficiency star" if latest['tusg'] > 28 and latest['pvr'] > 12 
    else "high-usage player with room for efficiency gains" if latest['tusg'] > 28 
    else "efficient role player" if latest['pvr'] > 12 
    else "solid contributor"
}
• Ranks in Top {peer_comparison.get('tusg_percentile', 50):.0f}% for usage
• Best for: {"Prop bets and DFS lineups" if latest['tusg'] > 25 else "Team-based bets and value plays"}

CALL TO ACTION:
• Subscribe for weekly player deep dives
• Check out the full PDF report (link in description)
• Follow Taylor Vector Terminal for daily NBA analytics
• Drop your player requests in the comments!

═══════════════════════════════════════════════════════════════

📝 VISUAL CUE SUGGESTIONS:
═══════════════════════════════════════════════════════════════

• 0:00 - Taylor Vector Terminal intro animation
• 0:30 - Career progression chart (TUSG% & PVR)
• 1:30 - Current season stats overlay
• 3:00 - Peer comparison visualization
• 4:00 - Betting implications graphics
• 5:30 - Summary infographic
• 6:00 - Subscribe/Like/Comment reminder

═══════════════════════════════════════════════════════════════
END OF SCRIPT
═══════════════════════════════════════════════════════════════
"""
    
    with open(filepath, 'w') as f:
        f.write(script)
    
    return filepath

def archive_deep_dive(player_name, pdf_path, markdown_path, video_script_path):
    """Archive all deep dive files to the deepdives archive"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    safe_name = player_name.replace(' ', '_').lower()
    
    archive_data = {
        'player_name': player_name,
        'date_generated': datetime.now().isoformat(),
        'pdf_path': pdf_path,
        'markdown_path': markdown_path,
        'video_script_path': video_script_path
    }
    
    archive_file = os.path.join(ARCHIVE_DIR, f"{safe_name}_{timestamp}.json")
    with open(archive_file, 'w') as f:
        json.dump(archive_data, f, indent=2)
    
    return archive_file

def get_featured_player_of_week():
    """Get featured player for weekly deep dive (rotates through top players)"""
    # Featured players rotation
    featured_players = [
        'LeBron James',
        'Stephen Curry',
        'Kevin Durant',
        'Giannis Antetokounmpo',
        'Nikola Jokić',
        'Luka Dončić',
        'Joel Embiid',
        'Jayson Tatum'
    ]
    
    # Rotate based on week number
    import datetime
    week_num = datetime.datetime.now().isocalendar()[1]
    player_index = week_num % len(featured_players)
    
    return featured_players[player_index]

def generate_complete_deepdive(player_name):
    """Generate complete deep dive with all components"""
    print(f"\n🏀 Generating Complete Deep Dive for: {player_name}")
    print("="*70)
    
    # Fetch career stats
    print("📊 Fetching career statistics...")
    career_stats = fetch_player_career_stats(player_name)
    
    if not career_stats:
        print("❌ No career statistics found")
        return None
    
    print(f"✅ Found {len(career_stats)} seasons of data")
    
    # Perform analysis
    print("🎯 Analyzing strengths and weaknesses...")
    analysis = analyze_strengths_weaknesses(career_stats)
    
    print("🏆 Comparing to position peers...")
    peer_comparison = analyze_position_peer_comparison(career_stats, player_name, 'All')
    
    print("💰 Analyzing betting implications...")
    betting_analysis = analyze_betting_implications(career_stats, player_name)
    
    # Generate all outputs
    print("\n📄 Generating PDF report...")
    pdf_path = generate_player_deepdive_pdf(player_name, career_stats)
    print(f"✅ PDF: {pdf_path}")
    
    print("📝 Generating Markdown report...")
    markdown_path = generate_markdown_report(player_name, career_stats, peer_comparison, betting_analysis, analysis)
    print(f"✅ Markdown: {markdown_path}")
    
    print("🎬 Generating video companion script...")
    video_script_path = generate_video_script(player_name, career_stats, peer_comparison, betting_analysis, analysis)
    print(f"✅ Video Script: {video_script_path}")
    
    print("📁 Archiving deep dive...")
    archive_path = archive_deep_dive(player_name, pdf_path, markdown_path, video_script_path)
    print(f"✅ Archive: {archive_path}")
    
    print("\n" + "="*70)
    print(f"✅ Complete deep dive generated for {player_name}")
    print("="*70)
    
    return {
        'player_name': player_name,
        'career_stats': career_stats,
        'analysis': analysis,
        'peer_comparison': peer_comparison,
        'betting_analysis': betting_analysis,
        'pdf_path': pdf_path,
        'markdown_path': markdown_path,
        'video_script_path': video_script_path,
        'archive_path': archive_path
    }

if __name__ == '__main__':
    print("🏀 TAYLOR VECTOR TERMINAL - Weekly Player Deep Dive Generator")
    print("="*70)
    
    # Get featured player for the week
    featured = get_featured_player_of_week()
    print(f"\n📅 This week's featured player: {featured}")
    
    # Generate complete deep dive
    result = generate_complete_deepdive(featured)
    
    if result:
        print(f"\n🎉 SUCCESS! All components generated:")
        print(f"  • PDF Report: {result['pdf_path']}")
        print(f"  • Markdown: {result['markdown_path']}")
        print(f"  • Video Script: {result['video_script_path']}")
        print(f"  • Archive: {result['archive_path']}")
    else:
        print("❌ Failed to generate deep dive")
