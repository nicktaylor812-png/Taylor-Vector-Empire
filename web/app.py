"""
TAYLOR VECTOR TERMINAL - Live Web Dashboard
Real-time betting edge monitoring and metrics visualization
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for, make_response
import sqlite3
import os
import sys
import json
import requests
import time
from datetime import datetime

sys.path.append('..')
sys.path.append('../api')
sys.path.append('../premium')

# Commenting out premium_api import so the Flask app can start without premium package
# from premium_api import api_bp, init_api_database

# consulting_portal may not be installed in some environments. Attempt to import it,
# otherwise provide a minimal stub implementation so routes that reference it
# won't crash the app at import time. This keeps the app runnable in lightweight
# deployments while preserving full functionality when the premium package exists.
try:
    from consulting_portal import ConsultingGroup, BASE_PRICE, PER_MEMBER_PRICE
except Exception:
    class ConsultingGroup:
        def __init__(self):
            pass
        def get_group_by_slug(self, slug):
            return {
                'id': 0,
                'name': 'Demo Group',
                'primary_color': '#1f6feb',
                'secondary_color': '#7dd3fc',
                'slug': slug
            }
        def get_group_by_id(self, id):
            return self.get_group_by_slug('demo')
        def authenticate_member(self, slug, email, password):
            return None
        def get_group_picks(self, group_id, limit=50):
            return []
        def get_group_members(self, group_id):
            return []
        def get_group_chat(self, group_id, limit=100):
            return []
        def get_group_analytics(self, group_id):
            return {}

    BASE_PRICE = 0.0
    PER_MEMBER_PRICE = 0.0

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize API database and register premium API blueprint.
# These are disabled so the app can run without the optional `premium_api` module installed.
# init_api_database()
# app.register_blueprint(api_bp, url_prefix='/api')

DB_FILE = '../taylor_62.db'
LEADERBOARD_FILE = '../leaderboard/data/all_time_tusg.json'
BALLDONTLIE_API_KEY = os.getenv('BALLDONTLIE_API_KEY', 'eada3064-5b46-4fe0-948c-1771738e4021')

TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main dashboard page"""
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.after_request
def add_header(response):
    """Disable caching for static files in development"""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/api/picks')
def get_picks():
    """Get recent picks"""
    conn = get_db_connection()
    picks = conn.execute('''
        SELECT * FROM picks 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(pick) for pick in picks])

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    conn = get_db_connection()
    
    total_picks = conn.execute('SELECT COUNT(*) as count FROM picks').fetchone()['count']
    avg_edge = conn.execute('SELECT AVG(edge) as avg FROM picks').fetchone()['avg']
    highest_edge = conn.execute('SELECT MAX(edge) as max FROM picks').fetchone()['max']
    recent_pick = conn.execute('SELECT * FROM picks ORDER BY timestamp DESC LIMIT 1').fetchone()
    
    conn.close()
    
    return jsonify({
        'total_picks': total_picks,
        'avg_edge': round(avg_edge, 2) if avg_edge else 0,
        'highest_edge': round(highest_edge, 2) if highest_edge else 0,
        'last_updated': recent_pick['timestamp'] if recent_pick else None,
        'status': 'LIVE'
    })

@app.route('/api/live')
def get_live_status():
    """Check if terminal is running"""
    conn = get_db_connection()
    recent = conn.execute('''
        SELECT timestamp FROM picks 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''').fetchone()
    conn.close()
    
    is_live = False
    if recent:
        last_update = datetime.strptime(recent['timestamp'], '%Y-%m-%d %H:%M:%S')
        time_diff = (datetime.now() - last_update).total_seconds()
        is_live = time_diff < 120
    
    return jsonify({'live': is_live})

def calculate_player_tusg(player_stats, team_pace):
    """Calculate TUSG% for a player"""
    mp = player_stats.get('min', 0) or player_stats.get('mpg', 0)
    
    # Handle various minute formats from NBA API (MM:SS, MM:SS:hundredths, HH:MM:SS, or numeric)
    try:
        if isinstance(mp, str) and ':' in mp:
            parts = mp.split(':')
            if len(parts) == 3:
                first = float(parts[0])
                if first > 59:  # True HH:MM:SS format (hours exceed 59)
                    mp = first * 60 + float(parts[1]) + float(parts[2]) / 60
                else:  # MM:SS:hundredths format (e.g., "28:43:00" = 28 min, 43 sec)
                    mp = first + float(parts[1]) / 60 + float(parts[2]) / 3600
            elif len(parts) == 2:  # MM:SS format
                mp = float(parts[0]) + float(parts[1]) / 60
            else:
                mp = 0.0
        else:
            mp = float(mp) if mp else 0.0
    except (ValueError, AttributeError):
        mp = 0.0  # Gracefully handle bad inputs
    
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
    pts = player_stats.get('pts', 0) or player_stats.get('ppg', 0)
    ast = player_stats.get('ast', 0) or player_stats.get('apg', 0)
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

def get_current_players():
    """Fetch current NBA players from API"""
    players = []
    try:
        app.logger.info("get_current_players: start fetching players")
    except Exception:
        print("get_current_players: start fetching players")
    try:
        # Use the free balldontlie players endpoint to populate current roster list
        per_page = 100
        page = 1
        fetched = 0
        bdl_player_ids = []

        while True:
            url = f"https://www.balldontlie.io/api/v1/players?per_page={per_page}&page={page}"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                break
            data = resp.json()
            items = data.get('data', [])
            if not items:
                break

            for p in items:
                pid = p.get('id')
                team = p.get('team') or {}
                team_abbr = team.get('abbreviation') if isinstance(team, dict) else None
                players.append({
                    'bdl_id': pid,
                    'id': f"bdl_{pid}",
                    'name': f"{p.get('first_name', '').strip()} {p.get('last_name', '').strip()}".strip(),
                    'team': team_abbr or (team.get('full_name') if isinstance(team, dict) else 'Unknown'),
                    'is_historical': False,
                    'mpg': 0,
                    'ppg': 0,
                    'apg': 0,
                    'fga': 0,
                    'fta': 0,
                    'tov': 0,
                    'tusg': 0,
                    'pvr': 0
                })
                bdl_player_ids.append(pid)
                fetched += 1
                if fetched >= 500:
                    break

            if fetched >= 500 or not data.get('meta') or page >= data.get('meta', {}).get('total_pages', page):
                break

            page += 1
            time.sleep(0.15)

        # Fetch internal season averages first (preferred), fall back to balldontlie season_averages
        season = int(os.getenv('SEASON_YEAR', datetime.now().year))
        internal_url = os.getenv('INTERNAL_STATS_URL', 'https://api.server.nbaapi.com/api/playertotals')
        internal_map = {}

        try:
            # paginate through internal stats API if reachable
            page = 1
            page_size = 200
            while True:
                resp = requests.get(f"{internal_url}?season={season}&pageSize={page_size}&page={page}", timeout=12)
                if resp.status_code != 200:
                    break
                data = resp.json()
                items = data.get('data', [])
                if not items:
                    break
                for it in items:
                    name = (it.get('playerName') or '').strip().lower()
                    if not name:
                        continue
                    internal_map[name] = it
                if len(items) < page_size:
                    break
                page += 1
                time.sleep(0.2)
        except Exception as e:
            try:
                app.logger.warning(f"get_current_players: internal stats fetch failed: {e}")
            except Exception:
                print(f"get_current_players: internal stats fetch failed: {e}")
            # ignore internal API failures and fallback to balldontlie-only
            internal_map = {}

        # Now fetch balldontlie season averages in batches to fill any remaining players
        bdl_stats_map = {}
        if bdl_player_ids:
            batch_size = 100
            for i in range(0, len(bdl_player_ids), batch_size):
                batch_ids = bdl_player_ids[i:i+batch_size]
                params = [('season', season)] + [(f'player_ids[]', str(x)) for x in batch_ids]
                stats_url = 'https://www.balldontlie.io/api/v1/season_averages'
                try:
                    resp = requests.get(stats_url, params=params, timeout=10)
                    if resp.status_code != 200:
                        continue
                    data = resp.json().get('data', [])
                    for s in data:
                        pid = s.get('player_id')
                        bdl_stats_map[pid] = s
                except Exception:
                    continue

        enriched = 0
        # Merge stats into player objects, preferring internal API by player name, else balldontlie
        for p in players:
            name = p.get('name', '').strip().lower()
            used_stats = None
            # prefer internal mapping by name
            if name and name in internal_map:
                used_stats = internal_map[name]
                # internal API uses different keys; normalize
                mpg = used_stats.get('minutesPg') or used_stats.get('min') or 0
                pts = (used_stats.get('points') or 0)
                ast = (used_stats.get('assists') or 0)
                tov = (used_stats.get('turnovers') or 0)
                fga = (used_stats.get('fieldAttempts') or 0)
                fta = (used_stats.get('ftAttempts') or 0)
                stat_for_calc = {
                    'min': mpg,
                    'fga': fga,
                    'tov': tov,
                    'fta': fta,
                    'pts': pts,
                    'ast': ast
                }
            else:
                # fallback to balldontlie
                pid = p.get('bdl_id')
                s = bdl_stats_map.get(pid)
                if s:
                    stat_for_calc = {
                        'min': s.get('min', 0),
                        'fga': s.get('fga', 0),
                        'tov': s.get('turnovers', 0),
                        'fta': s.get('fta', 0),
                        'pts': s.get('pts', 0),
                        'ast': s.get('ast', 0)
                    }
                else:
                    stat_for_calc = None

            if stat_for_calc:
                try:
                    team_abbr = p.get('team')
                    team_pace = TEAM_PACE.get(team_abbr, 99.5)
                    tusg_val = calculate_player_tusg(stat_for_calc, team_pace)
                except Exception:
                    tusg_val = 0
                try:
                    pvr_val = calculate_player_pvr(stat_for_calc)
                except Exception:
                    pvr_val = 0

                # Populate common fields
                p['mpg'] = stat_for_calc.get('min', 0)
                p['ppg'] = stat_for_calc.get('pts', 0)
                p['apg'] = stat_for_calc.get('ast', 0)
                p['fga'] = stat_for_calc.get('fga', 0)
                p['fta'] = stat_for_calc.get('fta', 0)
                p['tov'] = stat_for_calc.get('tov', 0)
                p['tusg'] = tusg_val
                p['pvr'] = pvr_val
                enriched += 1

        try:
            app.logger.info(f"get_current_players: fetched {len(players)} players, enriched {enriched} with season stats")
        except Exception:
            print(f"get_current_players: fetched {len(players)} players, enriched {enriched} with season stats")

    except Exception as e:
        print(f"Error fetching current players: {e}")

    return players

def get_historical_players():
    """Load historical players from leaderboard data"""
    players = []
    
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
        
        for player in leaderboard:
            players.append({
                'id': f"historical_{player['player'].replace(' ', '_')}_{player['season']}",
                'name': player['player'],
                'team': 'Historical',
                'is_historical': True,
                'season': player['season'],
                'mpg': round(player['mpg'], 1),
                'ppg': round(player['ppg'], 1),
                'apg': round(player['apg'], 1),
                'fga': 0,
                'fgm': 0,
                'fta': 0,
                'tov': 0,
                'tusg': player['tusg'],
                'pvr': player['pvr']
            })
    except Exception as e:
        print(f"Error loading historical players: {e}")
    
    return players

@app.route('/compare')
def compare_page():
    """Player comparison page"""
    return render_template('compare.html')

@app.route('/cross-era')
def cross_era_page():
    """Cross-era PVR comparison tool"""
    return render_template('cross_era.html')

@app.route('/api/cross-era/players')
def get_cross_era_players():
    """Get all historical players with full stats for cross-era comparison"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
        
        return jsonify({
            'players': leaderboard,
            'count': len(leaderboard)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comparison/players')
def get_all_players():
    """Get all players (current + historical) for comparison"""
    try:
        current = get_current_players()
        historical = get_historical_players()
        
        all_players = current + historical
        all_players.sort(key=lambda x: x['name'])
        
        return jsonify({
            'players': all_players,
            'count': len(all_players)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comparison/compare', methods=['POST'])
def compare_players():
    """Compare two players"""
    try:
        data = request.get_json()
        player1_id = data.get('player1_id')
        player2_id = data.get('player2_id')
        
        if not player1_id or not player2_id:
            return jsonify({'error': 'Both player IDs required'}), 400
        
        all_players = get_current_players() + get_historical_players()
        
        player1 = next((p for p in all_players if p['id'] == player1_id), None)
        player2 = next((p for p in all_players if p['id'] == player2_id), None)
        
        if not player1 or not player2:
            return jsonify({'error': 'One or both players not found'}), 404
        
        return jsonify({
            'player1': player1,
            'player2': player2
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/westbrook-rule')
def westbrook_rule():
    """Westbrook Rule Historical Machine page"""
    return send_from_directory('../tools', 'westbrook_rule.html')

@app.route('/westbrook_rule_results.json')
def westbrook_rule_results():
    """Serve Westbrook Rule results JSON"""
    return send_from_directory('../tools', 'westbrook_rule_results.json')

@app.route('/goat-rankings')
def goat_rankings():
    """Positionless GOAT Rankings page"""
    return send_from_directory('../tools', 'goat_rankings.html')

@app.route('/goat_rankings.json')
def goat_rankings_json():
    """Serve GOAT Rankings JSON"""
    return send_from_directory('../tools', 'goat_rankings.json')

@app.route('/draft-predictor')
def draft_predictor():
    """Draft Prospect PVR Predictor page"""
    return send_from_directory('../tools', 'draft_predictor.html')

@app.route('/draft_predictor_examples.json')
def draft_predictor_examples():
    """Serve Draft Predictor examples JSON"""
    return send_from_directory('../tools', 'draft_predictor_examples.json')

@app.route('/draft_predictor_2025.json')
def draft_predictor_2025():
    """Serve 2025 Draft Prospects JSON"""
    return send_from_directory('../tools', 'draft_predictor_2025.json')

@app.route('/trade-calculator')
def trade_calculator():
    """Trade Impact Calculator page"""
    return send_from_directory('../tools', 'trade_calculator.html')

@app.route('/trade_calculator_examples.json')
def trade_calculator_examples():
    """Serve Trade Calculator examples JSON"""
    return send_from_directory('../tools', 'trade_calculator_examples.json')

@app.route('/contract-value')
def contract_value():
    """Contract Value Calculator page"""
    return send_from_directory('../tools', 'contract_value.html')

@app.route('/contract_value_results.json')
def contract_value_results():
    """Serve Contract Value results JSON"""
    return send_from_directory('../tools', 'contract_value_results.json')

@app.route('/metric-customizer')
def metric_customizer():
    """Metric Customizer - Adjust TUSG% and PVR formulas"""
    return send_from_directory('../tools', 'metric_customizer.html')

@app.route('/metric_customizer.js')
def metric_customizer_js():
    """Serve Metric Customizer JavaScript"""
    return send_from_directory('../tools', 'metric_customizer.js')

@app.route('/team-builder')
def team_builder():
    """All-Time Team Builder - Fantasy team constructor"""
    return send_from_directory('../tools', 'team_builder.html')

@app.route('/team_builder_data.json')
def team_builder_data():
    """Serve Team Builder data JSON"""
    return send_from_directory('../tools', 'team_builder_data.json')

@app.route('/fantasy-optimizer')
def fantasy_optimizer():
    """Fantasy Basketball Optimizer - Draft/Trade advice using TUSG%/PVR"""
    return send_from_directory('../tools', 'fantasy_optimizer.html')

@app.route('/instagram-creator')
def instagram_creator():
    """Instagram Metrics Visualizer - Auto-generate TUSG%/PVR graphics"""
    return send_from_directory('../tools', 'instagram_creator.html')

@app.route('/api/instagram/generate-stat-card', methods=['POST'])
def generate_stat_card():
    """Generate player stat card"""
    try:
        import sys
        sys.path.append('../tools')
        from instagram_creator import create_player_stat_card
        
        data = request.get_json()
        player = data.get('player')
        custom_text = data.get('custom_text', '')
        custom_color = data.get('custom_color', None)
        
        filepath = create_player_stat_card(player, custom_text, custom_color)
        
        return jsonify({
            'success': True,
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/instagram/generate-top-performer', methods=['POST'])
def generate_top_performer():
    """Generate top performer card"""
    try:
        import sys
        sys.path.append('../tools')
        from instagram_creator import create_top_performer_card
        
        data = request.get_json()
        player = data.get('player')
        game_info = data.get('game_info', '')
        
        filepath = create_top_performer_card(player, game_info)
        
        return jsonify({
            'success': True,
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/instagram/generate-comparison', methods=['POST'])
def generate_comparison():
    """Generate player comparison card"""
    try:
        import sys
        sys.path.append('../tools')
        from instagram_creator import create_comparison_card
        
        data = request.get_json()
        player1 = data.get('player1')
        player2 = data.get('player2')
        title = data.get('title', 'HEAD TO HEAD')
        
        filepath = create_comparison_card(player1, player2, title)
        
        return jsonify({
            'success': True,
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/instagram/generate-leaderboard', methods=['POST'])
def generate_leaderboard():
    """Generate leaderboard card"""
    try:
        import sys
        sys.path.append('../tools')
        from instagram_creator import create_leaderboard_card
        
        data = request.get_json()
        top_n = data.get('top_n', 10)
        
        filepath = create_leaderboard_card(top_n)
        
        return jsonify({
            'success': True,
            'filepath': filepath
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/instagram/gallery')
def instagram_gallery():
    """Get recent Instagram posts"""
    try:
        import sys
        sys.path.append('../tools')
        from instagram_creator import get_recent_images
        
        images = get_recent_images(12)
        
        return jsonify({
            'images': images,
            'total_count': len(images),
            'last_updated': images[0]['timestamp'] if images else None
        })
    except Exception as e:
        return jsonify({
            'images': [],
            'total_count': 0,
            'last_updated': None,
            'error': str(e)
        }), 500

@app.route('/tools/instagram_output/<path:filename>')
def serve_instagram_image(filename):
    """Serve generated Instagram images"""
    return send_from_directory('../tools/instagram_output', filename)

@app.route('/tiktok-scripts')
def tiktok_scripts():
    """TikTok Script Generator - Auto-generate 60-second metric tutorial scripts"""
    return send_from_directory('../bots', 'tiktok_bot.html')

@app.route('/daily-report')
def daily_report():
    """Daily Edge Report Generator - Premium PDF reports"""
    return render_template('daily_report.html')

@app.route('/api/daily-report/generate', methods=['POST'])
def generate_daily_report():
    """Generate a daily edge report PDF"""
    try:
        import sys
        sys.path.append('../premium')
        from daily_report import generate_pdf_report
        
        data = request.get_json()
        date = data.get('date')
        
        filepath = generate_pdf_report(date=date)
        filename = os.path.basename(filepath)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/daily-report/list')
def list_daily_reports():
    """List recent daily reports"""
    try:
        import sys
        sys.path.append('../premium')
        from daily_report import get_recent_reports
        
        reports = get_recent_reports(limit=20)
        
        return jsonify({
            'reports': reports,
            'count': len(reports)
        })
    except Exception as e:
        return jsonify({
            'reports': [],
            'count': 0,
            'error': str(e)
        }), 500

@app.route('/api/daily-report/view')
def view_daily_report():
    """View a daily report PDF"""
    filepath = request.args.get('path')
    if not filepath:
        return jsonify({'error': 'No filepath provided'}), 400
    
    try:
        directory = os.path.dirname(os.path.abspath(filepath))
        filename = os.path.basename(filepath)
        return send_from_directory(directory, filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-report/download')
def download_daily_report():
    """Download a daily report PDF"""
    filepath = request.args.get('path')
    if not filepath:
        return jsonify({'error': 'No filepath provided'}), 400
    
    try:
        directory = os.path.dirname(os.path.abspath(filepath))
        filename = os.path.basename(filepath)
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-report/email', methods=['POST'])
def email_daily_report():
    """Email a daily report (placeholder for email integration)"""
    try:
        data = request.get_json()
        email = data.get('email')
        filepath = data.get('filepath')
        
        # Placeholder for actual email integration
        # In production, this would use SMTP or an email service API
        
        return jsonify({
            'success': True,
            'message': f'Email functionality is a placeholder. In production, report would be sent to {email}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/player-deepdive')
def player_deepdive():
    """Weekly Player Deep Dive - Premium feature"""
    return render_template('player_deepdive.html')

@app.route('/api/player-deepdive/players')
def get_deepdive_players():
    """Get list of all available players"""
    try:
        import sys
        sys.path.append('../premium')
        from player_deepdive import get_available_players
        
        players = get_available_players()
        
        return jsonify({
            'players': players,
            'count': len(players)
        })
    except Exception as e:
        return jsonify({
            'players': [],
            'count': 0,
            'error': str(e)
        }), 500

@app.route('/api/player-deepdive/featured')
def get_featured_player():
    """Get the featured player of the week"""
    try:
        import sys
        sys.path.append('../premium')
        from player_deepdive import get_featured_player_of_week
        
        featured = get_featured_player_of_week()
        
        return jsonify({
            'player': featured
        })
    except Exception as e:
        return jsonify({
            'player': None,
            'error': str(e)
        }), 500

@app.route('/api/player-deepdive/analyze', methods=['POST'])
def analyze_player():
    """Analyze a player's career and generate deep dive data"""
    try:
        import sys
        sys.path.append('../premium')
        from player_deepdive import fetch_player_career_stats, analyze_strengths_weaknesses
        
        data = request.get_json()
        player_slug = data.get('player_slug')
        
        if not player_slug:
            return jsonify({'error': 'Player slug required'}), 400
        
        career_stats = fetch_player_career_stats(player_slug)
        
        if not career_stats:
            return jsonify({
                'success': False,
                'error': 'No career statistics found for this player'
            }), 404
        
        analysis = analyze_strengths_weaknesses(career_stats)
        
        # Get player name from first season
        player_name = player_slug.replace('_', ' ').title()
        
        return jsonify({
            'success': True,
            'player_name': player_name,
            'career_stats': career_stats,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/player-deepdive/generate-pdf', methods=['POST'])
def generate_player_deepdive_pdf():
    """Generate PDF report for player deep dive"""
    try:
        import sys
        sys.path.append('../premium')
        from player_deepdive import generate_player_deepdive_pdf
        
        data = request.get_json()
        player_name = data.get('player_name')
        career_stats = data.get('career_stats')
        
        if not player_name or not career_stats:
            return jsonify({'error': 'Player name and career stats required'}), 400
        
        filepath = generate_player_deepdive_pdf(player_name, career_stats)
        filename = os.path.basename(filepath)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/player-deepdive/download-pdf')
def download_player_deepdive_pdf():
    """Download a player deep dive PDF"""
    filepath = request.args.get('path')
    if not filepath:
        return jsonify({'error': 'No filepath provided'}), 400
    
    try:
        directory = os.path.dirname(os.path.abspath(filepath))
        filename = os.path.basename(filepath)
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/season-predictions')
def season_predictions():
    """Season Prediction Engine - Premium feature"""
    return render_template('season_predictor.html')

@app.route('/api/season-predictions/generate', methods=['POST'])
def generate_season_predictions():
    """Generate comprehensive season predictions"""
    try:
        import sys
        sys.path.append('../premium')
        from season_predictor import generate_all_predictions, save_predictions
        
        predictions = generate_all_predictions(2025)
        save_predictions(predictions)
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/season-predictions/latest')
def get_latest_predictions():
    """Get latest saved predictions"""
    try:
        import sys
        import os
        sys.path.append('../premium')
        
        predictions_file = '../premium/season_predictions.json'
        
        if os.path.exists(predictions_file):
            with open(predictions_file, 'r') as f:
                import json
                predictions = json.load(f)
            
            return jsonify({
                'success': True,
                'predictions': predictions
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No predictions file found. Generate predictions first.'
            }), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/season-predictions/historical-validation')
def get_historical_validation():
    """Validate predictions against historical data"""
    try:
        import sys
        sys.path.append('../premium')
        from season_predictor import validate_historical_predictions
        
        validation_results = validate_historical_predictions()
        
        return jsonify({
            'success': True,
            'validation': validation_results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/underrated-stars')
def underrated_stars():
    """Underrated PVR Stars Series - Premium feature"""
    return render_template('underrated_stars.html')

@app.route('/api/underrated-stars/featured')
def get_featured_underrated():
    """Get the featured underrated player of the week"""
    try:
        import sys
        sys.path.append('../premium')
        from underrated_stars import get_featured_underrated_player, analyze_why_underrated, get_fantasy_implications, get_betting_implications
        
        featured = get_featured_underrated_player()
        
        if not featured:
            return jsonify({
                'success': False,
                'error': 'No underrated players found'
            }), 404
        
        analysis = {
            'why_underrated': analyze_why_underrated(featured),
            'fantasy_implications': get_fantasy_implications(featured),
            'betting_implications': get_betting_implications(featured)
        }
        
        return jsonify({
            'success': True,
            'featured': featured,
            'analysis': analysis
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/underrated-stars/leaderboard')
def get_underrated_leaderboard():
    """Get top 10 underrated stars leaderboard"""
    try:
        import sys
        sys.path.append('../premium')
        from underrated_stars import get_underrated_stars
        
        top_10 = get_underrated_stars()[:10]
        
        return jsonify({
            'success': True,
            'leaderboard': top_10,
            'count': len(top_10)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/underrated-stars/all')
def get_all_underrated():
    """Get all underrated stars with stats"""
    try:
        import sys
        sys.path.append('../premium')
        from underrated_stars import get_underrated_stars, get_all_underrated_stats
        
        all_underrated = get_underrated_stars()
        stats = get_all_underrated_stats()
        
        return jsonify({
            'success': True,
            'players': all_underrated,
            'stats': stats,
            'count': len(all_underrated)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/underrated-stars/generate-report', methods=['POST'])
def generate_underrated_report():
    """Generate weekly underrated stars report"""
    try:
        import sys
        sys.path.append('../premium')
        from underrated_stars import generate_weekly_report
        
        filepath = generate_weekly_report()
        filename = os.path.basename(filepath)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/westbrook-hall')
@app.route('/westbrook-hof')
def westbrook_hall_of_fame():
    """Westbrook Rule Hall of Fame - Premium historical impact showcase"""
    return send_from_directory('../premium', 'westbrook_hof.html')

@app.route('/api/westbrook-hall/data')
def get_westbrook_hall_data():
    """Get Hall of Fame data"""
    try:
        import sys
        sys.path.append('../premium')
        
        data_file = '../premium/westbrook_hall_data.json'
        
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                import json
                data = json.load(f)
            
            return jsonify(data)
        else:
            # Generate data if it doesn't exist
            from westbrook_hall_of_fame import generate_hall_of_fame
            data = generate_hall_of_fame()
            
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/westbrook-hall/generate', methods=['POST'])
def generate_westbrook_hall():
    """Regenerate Hall of Fame data"""
    try:
        import sys
        sys.path.append('../premium')
        from westbrook_hall_of_fame import save_hall_of_fame
        
        filepath = save_hall_of_fame()
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'message': 'Hall of Fame data regenerated successfully'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api-docs')
def api_docs():
    """Premium API Documentation"""
    return send_from_directory('../api', 'api_docs.html')

@app.route('/api/admin/create-key', methods=['POST'])
def admin_create_api_key():
    """Admin endpoint to create API keys"""
    try:
        from premium_api import create_api_key
        
        data = request.get_json()
        email = data.get('email')
        tier = data.get('tier', 'free')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        key_info = create_api_key(email, tier)
        
        if key_info:
            return jsonify({
                'success': True,
                'key_info': key_info
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create API key'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/key-usage/<api_key>', methods=['GET'])
def admin_get_key_usage(api_key):
    """Admin endpoint to get API key usage stats"""
    try:
        from premium_api import get_api_key_usage
        
        usage_data = get_api_key_usage(api_key)
        
        if usage_data:
            return jsonify(usage_data), 200
        else:
            return jsonify({
                'error': 'API key not found'
            }), 404
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/admin/revoke-key/<api_key>', methods=['POST'])
def admin_revoke_key(api_key):
    """Admin endpoint to revoke an API key"""
    try:
        from premium_api import revoke_api_key
        
        success = revoke_api_key(api_key)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'API key revoked successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'API key not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/newsletter')
def newsletter_dashboard():
    """Newsletter management dashboard"""
    return render_template('newsletter.html')

@app.route('/newsletter/api/stats')
def newsletter_stats():
    """Get newsletter statistics"""
    try:
        sys.path.append('../premium')
        from newsletter_system import get_subscriber_stats
        
        stats = get_subscriber_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/newsletter/api/subscribers')
def newsletter_subscribers():
    """Get subscriber list with filters"""
    try:
        sys.path.append('../premium')
        from newsletter_system import get_all_subscribers
        
        tier = request.args.get('tier')
        status = request.args.get('status', 'active')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        subscribers = get_all_subscribers(tier=tier, status=status, limit=limit, offset=offset)
        return jsonify(subscribers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/newsletter/api/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Add new subscriber"""
    try:
        sys.path.append('../premium')
        from newsletter_system import add_subscriber
        
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')
        tier = data.get('tier', 'free')
        payment_id = data.get('payment_id')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        result = add_subscriber(email, name, tier, payment_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/newsletter/api/send-batch', methods=['POST'])
def newsletter_send_batch():
    """Send newsletter to a batch of subscribers"""
    try:
        sys.path.append('../premium')
        from newsletter_system import send_newsletter_batch
        
        data = request.get_json()
        template = data.get('template')
        tier = data.get('tier')
        extra_context = data.get('context')
        
        if not template:
            return jsonify({'error': 'Template is required'}), 400
        
        if not tier or tier == 'all':
            tier = None
        
        result = send_newsletter_batch(tier, template, extra_context)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/newsletter/unsubscribe/<token>')
def newsletter_unsubscribe(token):
    """Unsubscribe via unique token"""
    try:
        sys.path.append('../premium')
        from newsletter_system import unsubscribe_by_token
        
        result = unsubscribe_by_token(token)
        
        if result.get('success'):
            return f'''
                <html>
                <head><title>Unsubscribed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>✅ Successfully Unsubscribed</h1>
                    <p>You've been removed from the TAYLOR VECTOR newsletter.</p>
                    <p>Email: {result.get('email')}</p>
                    <p><a href="/newsletter">Return to Newsletter</a></p>
                </body>
                </html>
            '''
        else:
            return f'''
                <html>
                <head><title>Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Error</h1>
                    <p>{result.get('error', 'Invalid unsubscribe token')}</p>
                    <p><a href="/newsletter">Return to Newsletter</a></p>
                </body>
                </html>
            ''', 400
    except Exception as e:
        return f'<h1>Error: {str(e)}</h1>', 500

@app.route('/newsletter/manage/<token>')
def newsletter_manage(token):
    """Manage subscription preferences via unique token"""
    return f'''
        <html>
        <head><title>Manage Subscription</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>📧 Manage Your Subscription</h1>
            <p>Token: {token}</p>
            <p>Subscription management interface coming soon!</p>
            <p><a href="/newsletter/unsubscribe/{token}">Unsubscribe</a></p>
            <p><a href="/newsletter">Return to Newsletter</a></p>
        </body>
        </html>
    '''

@app.route('/newsletter/webhook/stripe', methods=['POST'])
def newsletter_webhook_stripe():
    """Handle Stripe webhook events"""
    try:
        sys.path.append('../premium')
        from newsletter_system import process_stripe_webhook
        
        event_data = request.get_json()
        result = process_stripe_webhook(event_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/newsletter/webhook/paypal', methods=['POST'])
def newsletter_webhook_paypal():
    """Handle PayPal webhook events"""
    try:
        sys.path.append('../premium')
        from newsletter_system import process_paypal_webhook
        
        event_data = request.get_json()
        result = process_paypal_webhook(event_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/portal/<slug>')
@app.route('/portal/<slug>/login', methods=['GET', 'POST'])
def portal_login(slug):
    """Portal login page"""
    portal = ConsultingGroup()
    group = portal.get_group_by_slug(slug)
    
    if not group:
        return f'''
            <html>
            <head><title>Group Not Found</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Group Not Found</h1>
                <p>The group "{slug}" does not exist.</p>
                <p><a href="/">Return to Dashboard</a></p>
            </body>
            </html>
        ''', 404
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        member = portal.authenticate_member(slug, email, password)
        
        if member:
            session['member_id'] = member['id']
            session['group_slug'] = slug
            session['member_role'] = member['role']
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': f'/portal/{slug}/dashboard'})
            return redirect(url_for('portal_dashboard', slug=slug))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            error = 'Invalid email or password'
    
    return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - {group['name']}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #070b1f 0%, #0a0e27 100%);
                    color: #ffffff;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .login-container {{
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid #2d3748;
                    border-radius: 15px;
                    padding: 40px;
                    width: 400px;
                    max-width: 90%;
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    margin: 0 auto 20px;
                    background: {group['primary_color']};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 36px;
                    font-weight: bold;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 10px;
                    background: linear-gradient(135deg, {group['primary_color']}, {group['secondary_color']});
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .subtitle {{
                    text-align: center;
                    color: #a0aec0;
                    margin-bottom: 30px;
                    font-size: 14px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                label {{
                    display: block;
                    margin-bottom: 8px;
                    color: #ffffff;
                    font-weight: bold;
                }}
                input {{
                    width: 100%;
                    padding: 12px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid #2d3748;
                    border-radius: 5px;
                    color: #ffffff;
                    font-size: 14px;
                }}
                input:focus {{
                    outline: none;
                    border-color: {group['primary_color']};
                }}
                button {{
                    width: 100%;
                    padding: 12px;
                    background: {group['primary_color']};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 16px;
                    transition: all 0.3s;
                }}
                button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(255, 87, 34, 0.3);
                }}
                .error {{
                    background: rgba(245, 101, 101, 0.2);
                    border-left: 4px solid #f56565;
                    padding: 10px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">{group['name'][0]}</div>
                <h1>{group['name']}</h1>
                <div class="subtitle">TAYLOR VECTOR TERMINAL</div>
                <form method="POST">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
    '''


@app.route('/portal/<slug>/dashboard')
def portal_dashboard(slug):
    """Portal dashboard - requires authentication"""
    if 'member_id' not in session or session.get('group_slug') != slug:
        return redirect(url_for('portal_login', slug=slug))
    
    portal = ConsultingGroup()
    group = portal.get_group_by_id(session.get('group_id')) if session.get('group_id') else portal.get_group_by_slug(slug)
    
    if not group:
        session.clear()
        return redirect(url_for('portal_login', slug=slug))
    
    member_id = session['member_id']
    
    conn = sqlite3.connect('../premium/consulting_groups.db')
    conn.row_factory = sqlite3.Row
    member = conn.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
    conn.close()
    
    if not member:
        session.clear()
        return redirect(url_for('portal_login', slug=slug))
    
    member = dict(member)
    
    picks = portal.get_group_picks(group['id'], limit=50)
    members = portal.get_group_members(group['id'])
    chat_messages = portal.get_group_chat(group['id'], limit=100)
    analytics = portal.get_group_analytics(group['id'])
    
    return render_template('portal_template.html', 
                         group=group, 
                         member=member, 
                         picks=picks, 
                         members=members, 
                         chat_messages=chat_messages, 
                         analytics=analytics,
                         BASE_PRICE=BASE_PRICE,
                         PER_MEMBER_PRICE=PER_MEMBER_PRICE)


@app.route('/portal/<slug>/logout')
def portal_logout(slug):
    """Logout from portal"""
    session.clear()
    return redirect(url_for('portal_login', slug=slug))


@app.route('/portal/<slug>/chat/send', methods=['POST'])
def portal_chat_send(slug):
    """Send chat message"""
    if 'member_id' not in session or session.get('group_slug') != slug:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    portal = ConsultingGroup()
    group = portal.get_group_by_slug(slug)
    
    if not group:
        return jsonify({'success': False, 'error': 'Group not found'}), 404
    
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400
    
    result = portal.post_chat_message(group['id'], session['member_id'], message)
    return jsonify(result)


@app.route('/portal/<slug>/settings/branding', methods=['POST'])
def portal_update_branding(slug):
    """Update group branding (admin only)"""
    if 'member_id' not in session or session.get('group_slug') != slug:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    if session.get('member_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    portal = ConsultingGroup()
    group = portal.get_group_by_slug(slug)
    
    if not group:
        return jsonify({'success': False, 'error': 'Group not found'}), 404
    
    data = request.get_json()
    result = portal.update_group_branding(
        group['id'],
        logo_url=data.get('logo_url'),
        primary_color=data.get('primary_color'),
        secondary_color=data.get('secondary_color'),
        custom_domain=data.get('custom_domain')
    )
    
    return jsonify(result)


@app.route('/portal/<slug>/settings/thresholds', methods=['POST'])
def portal_update_thresholds(slug):
    """Update group metric thresholds (admin only)"""
    if 'member_id' not in session or session.get('group_slug') != slug:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    if session.get('member_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    portal = ConsultingGroup()
    group = portal.get_group_by_slug(slug)
    
    if not group:
        return jsonify({'success': False, 'error': 'Group not found'}), 404
    
    data = request.get_json()
    result = portal.update_group_thresholds(
        group['id'],
        min_tusg=data.get('min_tusg'),
        min_pvr=data.get('min_pvr'),
        min_edge=data.get('min_edge')
    )
    
    return jsonify(result)


@app.route('/portal/<slug>/members/add', methods=['POST'])
def portal_add_member(slug):
    """Add new member to group (admin only)"""
    if 'member_id' not in session or session.get('group_slug') != slug:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    if session.get('member_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    portal = ConsultingGroup()
    group = portal.get_group_by_slug(slug)
    
    if not group:
        return jsonify({'success': False, 'error': 'Group not found'}), 404
    
    data = request.get_json()
    result = portal.add_member(
        group['id'],
        email=data.get('email'),
        password=data.get('password'),
        role=data.get('role', 'member')
    )
    
    return jsonify(result)


@app.route('/partnerships')
def partnerships():
    """Partnership Framework - Main page showing widget previews and integration options"""
    return render_template('partnerships_main.html')


@app.route('/partnerships/docs')
def partnerships_docs():
    """Partnership Documentation page"""
    return send_from_directory('../premium', 'partnership_docs.html')


@app.route('/partnerships/widget/leaderboard')
def partnership_widget_leaderboard():
    """Leaderboard widget for partner embedding"""
    return send_from_directory('../premium/partner_widgets', 'leaderboard_widget.html')


@app.route('/partnerships/widget/comparison')
def partnership_widget_comparison():
    """Comparison widget for partner embedding"""
    return send_from_directory('../premium/partner_widgets', 'comparison_widget.html')


@app.route('/partnerships/widget/edge-feed')
def partnership_widget_edge_feed():
    """Live edge feed widget for partner embedding"""
    return send_from_directory('../premium/partner_widgets', 'edge_feed_widget.html')


@app.route('/partnerships/track', methods=['POST'])
def partnership_track():
    """Track widget views/clicks for revenue sharing"""
    try:
        sys.path.append('../premium')
        from partnership_framework import track_widget_event, get_partner
        
        data = request.get_json()
        partner_key = data.get('partner_key')
        event_type = data.get('event_type')
        widget_type = data.get('widget_type')
        player_name = data.get('player_name')
        
        if not partner_key or not event_type:
            return jsonify({'error': 'Missing required fields'}), 400
        
        partner = get_partner(api_key=partner_key)
        if not partner:
            return jsonify({'error': 'Invalid partner key'}), 401
        
        user_ip = request.remote_addr
        referrer = request.referrer
        
        result = track_widget_event(
            partner['id'], 
            event_type, 
            widget_type=widget_type,
            player_name=player_name,
            user_ip=user_ip,
            referrer=referrer
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/partnerships/apply', methods=['POST'])
def partnership_apply():
    """Submit partnership application"""
    try:
        sys.path.append('../premium')
        from partnership_framework import add_partner
        
        data = request.get_json()
        
        site_name = data.get('site_name')
        site_url = data.get('site_url')
        email = data.get('email')
        integration_type = data.get('integration_type')
        webhook_url = data.get('webhook_url')
        
        if not site_name or not site_url or not email or not integration_type:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        custom_branding = {
            'site_url': site_url,
            'contact_email': email,
            'monthly_traffic': data.get('monthly_traffic', 'Not provided'),
            'message': data.get('message', '')
        }
        
        result = add_partner(
            site_name=site_name,
            api_endpoint=site_url,
            revenue_share=50.0,
            integration_type=integration_type,
            webhook_url=webhook_url,
            custom_branding=custom_branding
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'application_id': result['partner_id'],
            'message': 'Partnership application submitted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/partnerships/export/json')
def partnership_export_json():
    """JSON feed export for partners"""
    try:
        sys.path.append('../premium')
        from partnership_framework import export_json_feed
        
        partner_key = request.args.get('api_key')
        limit = int(request.args.get('limit', 50))
        
        if partner_key:
            from partnership_framework import get_partner
            partner = get_partner(api_key=partner_key)
            if partner:
                feed = export_json_feed(partner_id=partner['id'], limit=limit)
            else:
                feed = export_json_feed(limit=limit)
        else:
            feed = export_json_feed(limit=limit)
        
        return jsonify(feed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/partnerships/export/csv')
def partnership_export_csv():
    """CSV export for partners"""
    try:
        sys.path.append('../premium')
        from partnership_framework import export_csv_data
        from flask import Response
        
        csv_content = export_csv_data()
        
        if csv_content is None:
            return jsonify({'error': 'Failed to generate CSV'}), 500
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=tusg_pvr_data.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/partnerships/analytics/<int:partner_id>')
def partnership_analytics(partner_id):
    """Get analytics for a specific partner"""
    try:
        sys.path.append('../premium')
        from partnership_framework import get_partner_analytics, calculate_revenue_share
        
        days = int(request.args.get('days', 30))
        
        analytics = get_partner_analytics(partner_id, days=days)
        revenue = calculate_revenue_share(partner_id)
        
        return jsonify({
            'analytics': analytics,
            'revenue': revenue
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize newsletter database
    try:
        sys.path.append('../premium')
        from newsletter_system import init_database
        init_database()
        print("✅ Newsletter database initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize newsletter database: {e}")
    
    # Initialize consulting portal database
    try:
        from consulting_portal import init_database as init_portal_db
        init_portal_db()
        print("✅ Consulting portal database initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize consulting portal database: {e}")
    
    # Initialize partnership database
    try:
        sys.path.append('../premium')
        from partnership_framework import init_partnership_database
        init_partnership_database()
        print("✅ Partnership database initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize partnership database: {e}")
    
    # Start the daily report scheduler
    try:
        sys.path.append('../premium')
        from scheduler import start_scheduler
        scheduler = start_scheduler()
        print("✅ Daily report scheduler initialized - Auto-generation at 6:00 AM")
    except Exception as e:
        print(f"⚠️ Warning: Could not start scheduler: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
