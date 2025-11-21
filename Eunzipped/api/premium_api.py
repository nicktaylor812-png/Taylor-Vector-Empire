"""
TAYLOR VECTOR TERMINAL - Premium API Service
REST API endpoints for developers to access TUSG%/PVR data
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, timedelta
import os
import sys

sys.path.append('..')

api_bp = Blueprint('api', __name__)

DB_FILE = '../taylor_62.db'
LEADERBOARD_FILE = '../leaderboard/data/all_time_tusg.json'

TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

RATE_LIMITS = {
    'free': 100,
    'paid': 1000
}

def init_api_database():
    """Initialize API-specific database tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            user_email TEXT NOT NULL,
            tier TEXT DEFAULT 'free',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            is_active INTEGER DEFAULT 1,
            total_requests INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            response_time REAL,
            status_code INTEGER,
            FOREIGN KEY (api_key) REFERENCES api_keys(api_key)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp 
        ON api_usage(api_key, timestamp)
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_api_key():
    """Generate a unique API key"""
    random_uuid = str(uuid.uuid4())
    timestamp = str(datetime.now().timestamp())
    combined = f"{random_uuid}{timestamp}"
    api_key = hashlib.sha256(combined.encode()).hexdigest()
    return f"tvt_{api_key[:32]}"

def validate_api_key(api_key):
    """Validate API key and return tier info"""
    conn = get_db_connection()
    key_data = conn.execute('''
        SELECT * FROM api_keys 
        WHERE api_key = ? AND is_active = 1
    ''', (api_key,)).fetchone()
    conn.close()
    
    if not key_data:
        return None
    
    return dict(key_data)

def check_rate_limit(api_key, tier):
    """Check if API key has exceeded rate limit"""
    limit = RATE_LIMITS.get(tier, 100)
    
    conn = get_db_connection()
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    usage_count = conn.execute('''
        SELECT COUNT(*) as count FROM api_usage 
        WHERE api_key = ? AND timestamp > ?
    ''', (api_key, one_hour_ago.strftime('%Y-%m-%d %H:%M:%S'))).fetchone()['count']
    
    conn.close()
    
    return usage_count < limit, usage_count, limit

def log_api_usage(api_key, endpoint, response_time, status_code):
    """Log API usage for analytics and billing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO api_usage (api_key, endpoint, response_time, status_code)
        VALUES (?, ?, ?, ?)
    ''', (api_key, endpoint, response_time, status_code))
    
    cursor.execute('''
        UPDATE api_keys 
        SET last_used = CURRENT_TIMESTAMP,
            total_requests = total_requests + 1
        WHERE api_key = ?
    ''', (api_key,))
    
    conn.commit()
    conn.close()

def require_api_key(f):
    """Decorator to require and validate API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.now()
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'Include X-API-Key header or api_key query parameter',
                'docs': '/api-docs'
            }), 401
        
        key_data = validate_api_key(api_key)
        
        if not key_data:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'API key is invalid or has been revoked',
                'docs': '/api-docs'
            }), 401
        
        tier = key_data['tier']
        allowed, current_usage, limit = check_rate_limit(api_key, tier)
        
        if not allowed:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Rate limit of {limit} requests/hour exceeded',
                'current_usage': current_usage,
                'limit': limit,
                'tier': tier,
                'upgrade_info': 'Upgrade to paid tier for 1000 req/hr at /api-docs'
            }), 429
        
        request.api_key = api_key
        request.api_tier = tier
        request.rate_limit_remaining = limit - current_usage
        
        response = f(*args, **kwargs)
        
        response_time = (datetime.now() - start_time).total_seconds()
        status_code = response[1] if isinstance(response, tuple) else 200
        
        log_api_usage(api_key, request.path, response_time, status_code)
        
        if isinstance(response, tuple):
            response_obj, status = response
            if isinstance(response_obj, dict):
                response_obj = jsonify(response_obj)
            return response_obj, status
        
        return response
    
    return decorated_function

def calculate_player_tusg(player_stats, team_pace):
    """Calculate TUSG% for a player"""
    mp = player_stats.get('min', 0) or player_stats.get('mpg', 0)
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

def load_leaderboard_data():
    """Load historical leaderboard data"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return []

@api_bp.route('/v1/player/<player_name>', methods=['GET'])
@require_api_key
def get_player(player_name):
    """
    GET /api/v1/player/{name}
    Get player TUSG% and PVR stats
    """
    try:
        leaderboard = load_leaderboard_data()
        
        player_name_lower = player_name.lower().replace('_', ' ').replace('-', ' ')
        
        player_data = None
        for player in leaderboard:
            if player['player'].lower() == player_name_lower:
                player_data = player
                break
        
        if not player_data:
            return jsonify({
                'error': 'Player not found',
                'message': f'No data found for player: {player_name}',
                'available_players': [p['player'] for p in leaderboard[:10]]
            }), 404
        
        return jsonify({
            'player': player_data['player'],
            'season': player_data['season'],
            'metrics': {
                'tusg': player_data['tusg'],
                'pvr': player_data['pvr']
            },
            'stats': {
                'mpg': player_data['mpg'],
                'ppg': player_data['ppg'],
                'apg': player_data['apg']
            },
            'context': {
                'era_pace': player_data.get('era_pace', 100.0),
                'rank': player_data['rank']
            },
            'api_info': {
                'tier': request.api_tier,
                'rate_limit_remaining': request.rate_limit_remaining
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/v1/leaderboard', methods=['GET'])
@require_api_key
def get_leaderboard():
    """
    GET /api/v1/leaderboard?metric=tusg|pvr&limit=50
    Get rankings leaderboard
    """
    try:
        metric = request.args.get('metric', 'tusg').lower()
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if metric not in ['tusg', 'pvr']:
            return jsonify({
                'error': 'Invalid metric',
                'message': 'Metric must be either "tusg" or "pvr"'
            }), 400
        
        leaderboard = load_leaderboard_data()
        
        sorted_leaderboard = sorted(
            leaderboard, 
            key=lambda x: x[metric], 
            reverse=True
        )[:limit]
        
        return jsonify({
            'metric': metric,
            'limit': limit,
            'count': len(sorted_leaderboard),
            'leaderboard': sorted_leaderboard,
            'api_info': {
                'tier': request.api_tier,
                'rate_limit_remaining': request.rate_limit_remaining
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/v1/edges', methods=['GET'])
@require_api_key
def get_edges():
    """
    GET /api/v1/edges?min_confidence=65
    Get current betting edges
    """
    try:
        min_confidence = float(request.args.get('min_confidence', 65.0))
        
        conn = get_db_connection()
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        picks = conn.execute('''
            SELECT * FROM picks 
            WHERE edge >= ? AND timestamp > ?
            ORDER BY edge DESC
            LIMIT 50
        ''', (min_confidence, one_hour_ago.strftime('%Y-%m-%d %H:%M:%S'))).fetchall()
        
        conn.close()
        
        edges = []
        for pick in picks:
            edges.append({
                'game': pick['game'],
                'pick': pick['pick'],
                'edge': pick['edge'],
                'timestamp': pick['timestamp'],
                'metrics': {
                    'home_tusg': pick['home_tusg'],
                    'away_tusg': pick['away_tusg'],
                    'home_pvr': pick['home_pvr'],
                    'away_pvr': pick['away_pvr']
                },
                'spread': pick['spread']
            })
        
        return jsonify({
            'min_confidence': min_confidence,
            'count': len(edges),
            'edges': edges,
            'last_updated': edges[0]['timestamp'] if edges else None,
            'api_info': {
                'tier': request.api_tier,
                'rate_limit_remaining': request.rate_limit_remaining
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/v1/compare', methods=['GET'])
@require_api_key
def compare_players():
    """
    GET /api/v1/compare?p1={name}&p2={name}
    Compare two players
    """
    try:
        player1_name = request.args.get('p1', '').lower().replace('_', ' ').replace('-', ' ')
        player2_name = request.args.get('p2', '').lower().replace('_', ' ').replace('-', ' ')
        
        if not player1_name or not player2_name:
            return jsonify({
                'error': 'Missing parameters',
                'message': 'Both p1 and p2 parameters are required'
            }), 400
        
        leaderboard = load_leaderboard_data()
        
        player1_data = None
        player2_data = None
        
        for player in leaderboard:
            if player['player'].lower() == player1_name:
                player1_data = player
            if player['player'].lower() == player2_name:
                player2_data = player
        
        if not player1_data:
            return jsonify({
                'error': 'Player 1 not found',
                'message': f'No data found for player: {player1_name}'
            }), 404
        
        if not player2_data:
            return jsonify({
                'error': 'Player 2 not found',
                'message': f'No data found for player: {player2_name}'
            }), 404
        
        comparison = {
            'player1': {
                'name': player1_data['player'],
                'season': player1_data['season'],
                'tusg': player1_data['tusg'],
                'pvr': player1_data['pvr'],
                'mpg': player1_data['mpg'],
                'ppg': player1_data['ppg'],
                'apg': player1_data['apg']
            },
            'player2': {
                'name': player2_data['player'],
                'season': player2_data['season'],
                'tusg': player2_data['tusg'],
                'pvr': player2_data['pvr'],
                'mpg': player2_data['mpg'],
                'ppg': player2_data['ppg'],
                'apg': player2_data['apg']
            },
            'differences': {
                'tusg_diff': round(player1_data['tusg'] - player2_data['tusg'], 2),
                'pvr_diff': round(player1_data['pvr'] - player2_data['pvr'], 2),
                'ppg_diff': round(player1_data['ppg'] - player2_data['ppg'], 2),
                'apg_diff': round(player1_data['apg'] - player2_data['apg'], 2)
            },
            'winner': {
                'tusg': player1_data['player'] if player1_data['tusg'] > player2_data['tusg'] else player2_data['player'],
                'pvr': player1_data['player'] if player1_data['pvr'] > player2_data['pvr'] else player2_data['player']
            }
        }
        
        return jsonify({
            'comparison': comparison,
            'api_info': {
                'tier': request.api_tier,
                'rate_limit_remaining': request.rate_limit_remaining
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/v1/historical/<player_name>/<season>', methods=['GET'])
@require_api_key
def get_historical(player_name, season):
    """
    GET /api/v1/historical/{player}/{season}
    Get historical player data for a specific season
    """
    try:
        player_name_lower = player_name.lower().replace('_', ' ').replace('-', ' ')
        
        leaderboard = load_leaderboard_data()
        
        player_data = None
        for player in leaderboard:
            if (player['player'].lower() == player_name_lower and 
                player['season'] == season):
                player_data = player
                break
        
        if not player_data:
            matching_seasons = [
                p['season'] for p in leaderboard 
                if p['player'].lower() == player_name_lower
            ]
            
            return jsonify({
                'error': 'Data not found',
                'message': f'No data found for {player_name} in {season}',
                'available_seasons': matching_seasons if matching_seasons else None
            }), 404
        
        return jsonify({
            'player': player_data['player'],
            'season': season,
            'metrics': {
                'tusg': player_data['tusg'],
                'pvr': player_data['pvr']
            },
            'stats': {
                'mpg': player_data['mpg'],
                'ppg': player_data['ppg'],
                'apg': player_data['apg']
            },
            'context': {
                'era_pace': player_data.get('era_pace', 100.0),
                'rank': player_data['rank']
            },
            'api_info': {
                'tier': request.api_tier,
                'rate_limit_remaining': request.rate_limit_remaining
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/v1/calculate', methods=['POST'])
@require_api_key
def calculate_custom():
    """
    POST /api/v1/calculate
    Custom TUSG%/PVR calculation with provided stats
    
    Request body:
    {
        "mpg": 36.0,
        "ppg": 28.5,
        "apg": 7.2,
        "fga": 20.5,
        "fta": 8.2,
        "tov": 3.5,
        "team_pace": 100.0
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['mpg', 'ppg', 'apg', 'fga', 'fta', 'tov', 'team_pace']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields,
                'required': required_fields
            }), 400
        
        stats = {
            'min': float(data['mpg']),
            'pts': float(data['ppg']),
            'ast': float(data['apg']),
            'fga': float(data['fga']),
            'fta': float(data['fta']),
            'tov': float(data['tov'])
        }
        
        team_pace = float(data['team_pace'])
        
        tusg = calculate_player_tusg(stats, team_pace)
        pvr = calculate_player_pvr(stats)
        
        return jsonify({
            'input': data,
            'results': {
                'tusg': tusg,
                'pvr': pvr
            },
            'interpretation': {
                'tusg_rating': 'Elite' if tusg > 40 else 'High' if tusg > 35 else 'Above Average' if tusg > 30 else 'Average',
                'pvr_rating': 'Elite' if pvr > 35 else 'High' if pvr > 25 else 'Above Average' if pvr > 15 else 'Average'
            },
            'api_info': {
                'tier': request.api_tier,
                'rate_limit_remaining': request.rate_limit_remaining
            }
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': 'Invalid data types',
            'message': 'All fields must be numeric values'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

def create_api_key(email, tier='free'):
    """Create a new API key"""
    api_key = generate_api_key()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO api_keys (api_key, user_email, tier)
            VALUES (?, ?, ?)
        ''', (api_key, email, tier))
        conn.commit()
        
        return {
            'api_key': api_key,
            'email': email,
            'tier': tier,
            'rate_limit': RATE_LIMITS[tier],
            'created_at': datetime.now().isoformat()
        }
    except Exception as e:
        return None
    finally:
        conn.close()

def revoke_api_key(api_key):
    """Revoke an API key"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE api_keys 
        SET is_active = 0
        WHERE api_key = ?
    ''', (api_key,))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success

def get_api_key_usage(api_key):
    """Get usage statistics for an API key"""
    conn = get_db_connection()
    
    key_info = conn.execute('''
        SELECT * FROM api_keys WHERE api_key = ?
    ''', (api_key,)).fetchone()
    
    if not key_info:
        conn.close()
        return None
    
    recent_usage = conn.execute('''
        SELECT endpoint, COUNT(*) as count, AVG(response_time) as avg_time
        FROM api_usage
        WHERE api_key = ?
        GROUP BY endpoint
        ORDER BY count DESC
    ''', (api_key,)).fetchall()
    
    one_hour_ago = datetime.now() - timedelta(hours=1)
    hourly_usage = conn.execute('''
        SELECT COUNT(*) as count FROM api_usage
        WHERE api_key = ? AND timestamp > ?
    ''', (api_key, one_hour_ago.strftime('%Y-%m-%d %H:%M:%S'))).fetchone()['count']
    
    conn.close()
    
    return {
        'api_key': api_key,
        'email': key_info['user_email'],
        'tier': key_info['tier'],
        'is_active': bool(key_info['is_active']),
        'created_at': key_info['created_at'],
        'last_used': key_info['last_used'],
        'total_requests': key_info['total_requests'],
        'hourly_usage': hourly_usage,
        'rate_limit': RATE_LIMITS[key_info['tier']],
        'rate_limit_remaining': RATE_LIMITS[key_info['tier']] - hourly_usage,
        'endpoint_usage': [dict(row) for row in recent_usage]
    }

init_api_database()
