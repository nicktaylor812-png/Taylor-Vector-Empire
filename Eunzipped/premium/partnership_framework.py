"""
TAYLOR VECTOR TERMINAL - Partnership Framework
Integration system for partnering with basketball analytics sites
"""

import sqlite3
import json
import csv
import hashlib
import requests
from datetime import datetime, timedelta
from io import StringIO
import os

DB_FILE = '../taylor_62.db'
LEADERBOARD_FILE = '../leaderboard/data/all_time_tusg.json'

INTEGRATION_TYPES = ['json_feed', 'csv_export', 'widget_embed', 'api_access', 'full_integration']
PARTNER_STATUS = ['pending', 'active', 'suspended', 'inactive']

def init_partnership_database():
    """Initialize partnership database tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT UNIQUE NOT NULL,
            api_endpoint TEXT,
            revenue_share REAL DEFAULT 50.0,
            integration_type TEXT DEFAULT 'widget_embed',
            status TEXT DEFAULT 'pending',
            api_key TEXT UNIQUE,
            custom_branding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_sync DATETIME,
            total_views INTEGER DEFAULT 0,
            total_clicks INTEGER DEFAULT 0,
            total_revenue REAL DEFAULT 0.0,
            webhook_url TEXT,
            webhook_secret TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partner_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_ip TEXT,
            widget_type TEXT,
            player_name TEXT,
            referrer TEXT,
            FOREIGN KEY (partner_id) REFERENCES partners(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            payload TEXT,
            response_code INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            success INTEGER DEFAULT 0,
            error_message TEXT,
            FOREIGN KEY (partner_id) REFERENCES partners(id)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_partner_analytics_partner 
        ON partner_analytics(partner_id, timestamp)
    ''')
    
    conn.commit()
    conn.close()

def generate_partner_api_key(site_name):
    """Generate unique API key for partner"""
    timestamp = str(datetime.now().timestamp())
    combined = f"{site_name}{timestamp}"
    api_key = hashlib.sha256(combined.encode()).hexdigest()
    return f"tvt_partner_{api_key[:24]}"

def generate_webhook_secret(site_name):
    """Generate webhook secret for partner"""
    timestamp = str(datetime.now().timestamp())
    combined = f"{site_name}_webhook_{timestamp}"
    secret = hashlib.sha256(combined.encode()).hexdigest()
    return secret[:32]

def add_partner(site_name, api_endpoint=None, revenue_share=50.0, 
                integration_type='widget_embed', webhook_url=None, custom_branding=None):
    """Add new partner to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        api_key = generate_partner_api_key(site_name)
        webhook_secret = generate_webhook_secret(site_name) if webhook_url else None
        
        branding_json = json.dumps(custom_branding) if custom_branding else None
        
        cursor.execute('''
            INSERT INTO partners (
                site_name, api_endpoint, revenue_share, integration_type, 
                status, api_key, webhook_url, webhook_secret, custom_branding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (site_name, api_endpoint, revenue_share, integration_type, 
              'pending', api_key, webhook_url, webhook_secret, branding_json))
        
        partner_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'partner_id': partner_id,
            'site_name': site_name,
            'api_key': api_key,
            'webhook_secret': webhook_secret,
            'status': 'pending'
        }
    except sqlite3.IntegrityError:
        return {'error': 'Partner already exists'}
    except Exception as e:
        return {'error': str(e)}

def get_partner(partner_id=None, api_key=None):
    """Get partner information"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    if partner_id:
        partner = conn.execute(
            'SELECT * FROM partners WHERE id = ?', (partner_id,)
        ).fetchone()
    elif api_key:
        partner = conn.execute(
            'SELECT * FROM partners WHERE api_key = ?', (api_key,)
        ).fetchone()
    else:
        conn.close()
        return None
    
    conn.close()
    
    if partner:
        partner_dict = dict(partner)
        if partner_dict.get('custom_branding'):
            partner_dict['custom_branding'] = json.loads(partner_dict['custom_branding'])
        return partner_dict
    return None

def get_all_partners(status=None):
    """Get all partners, optionally filtered by status"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    if status:
        partners = conn.execute(
            'SELECT * FROM partners WHERE status = ? ORDER BY created_at DESC', (status,)
        ).fetchall()
    else:
        partners = conn.execute(
            'SELECT * FROM partners ORDER BY created_at DESC'
        ).fetchall()
    
    conn.close()
    
    partner_list = []
    for partner in partners:
        partner_dict = dict(partner)
        if partner_dict.get('custom_branding'):
            partner_dict['custom_branding'] = json.loads(partner_dict['custom_branding'])
        partner_list.append(partner_dict)
    
    return partner_list

def update_partner_status(partner_id, status):
    """Update partner status"""
    if status not in PARTNER_STATUS:
        return {'error': 'Invalid status'}
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE partners SET status = ? WHERE id = ?', (status, partner_id)
    )
    
    conn.commit()
    conn.close()
    
    return {'success': True, 'partner_id': partner_id, 'status': status}

def export_json_feed(partner_id=None, limit=50):
    """Export real-time TUSG%/PVR data as JSON feed"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
        
        limited_data = leaderboard[:limit] if limit else leaderboard
        
        feed = {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'TAYLOR VECTOR TERMINAL',
            'metrics': ['TUSG%', 'PVR'],
            'count': len(limited_data),
            'players': limited_data
        }
        
        if partner_id:
            partner = get_partner(partner_id=partner_id)
            if partner:
                feed['partner'] = partner['site_name']
                feed['attribution'] = 'Data provided by TAYLOR VECTOR TERMINAL'
        
        return feed
    except Exception as e:
        return {'error': str(e)}

def export_csv_data(partner_id=None):
    """Export historical data as CSV"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'rank', 'player', 'season', 'tusg', 'pvr', 'mpg', 'ppg', 'apg', 'era_pace'
        ])
        
        writer.writeheader()
        for player in leaderboard:
            writer.writerow(player)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    except Exception as e:
        return None

def generate_widget_embed_code(widget_type, partner_id=None, custom_params=None):
    """Generate iframe embed code for widgets"""
    base_url = os.getenv('REPL_SLUG', 'https://taylor-vector-terminal.replit.app')
    
    widget_urls = {
        'leaderboard': f'{base_url}/partnerships/widget/leaderboard',
        'comparison': f'{base_url}/partnerships/widget/comparison',
        'edge_feed': f'{base_url}/partnerships/widget/edge-feed'
    }
    
    if widget_type not in widget_urls:
        return None
    
    widget_url = widget_urls[widget_type]
    
    params = []
    if partner_id:
        partner = get_partner(partner_id=partner_id)
        if partner and partner.get('api_key'):
            params.append(f"partner={partner['api_key']}")
    
    if custom_params:
        branding = custom_params.get('branding', {})
        if branding.get('primary_color'):
            params.append(f"color={branding['primary_color'].replace('#', '')}")
        if branding.get('logo_url'):
            params.append(f"logo={branding['logo_url']}")
        if custom_params.get('limit'):
            params.append(f"limit={custom_params['limit']}")
    
    if params:
        widget_url += '?' + '&'.join(params)
    
    embed_code = f'''<iframe 
    src="{widget_url}" 
    width="100%" 
    height="600" 
    frameborder="0" 
    scrolling="auto"
    style="border: 1px solid #ddd; border-radius: 8px;">
</iframe>'''
    
    return {
        'widget_type': widget_type,
        'embed_code': embed_code,
        'direct_url': widget_url,
        'width': '100%',
        'height': '600px'
    }

def track_widget_event(partner_id, event_type, widget_type=None, 
                       player_name=None, user_ip=None, referrer=None):
    """Track widget views/clicks for revenue share calculations"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO partner_analytics (
                partner_id, event_type, widget_type, player_name, user_ip, referrer
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (partner_id, event_type, widget_type, player_name, user_ip, referrer))
        
        if event_type == 'view':
            cursor.execute(
                'UPDATE partners SET total_views = total_views + 1 WHERE id = ?',
                (partner_id,)
            )
        elif event_type == 'click':
            cursor.execute(
                'UPDATE partners SET total_clicks = total_clicks + 1 WHERE id = ?',
                (partner_id,)
            )
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}

def calculate_revenue_share(partner_id, base_revenue_per_view=0.01, base_revenue_per_click=0.05):
    """Calculate revenue share for partner based on views/clicks"""
    partner = get_partner(partner_id=partner_id)
    if not partner:
        return {'error': 'Partner not found'}
    
    total_views = partner.get('total_views', 0)
    total_clicks = partner.get('total_clicks', 0)
    revenue_share_pct = partner.get('revenue_share', 50.0)
    
    view_revenue = total_views * base_revenue_per_view
    click_revenue = total_clicks * base_revenue_per_click
    total_revenue = view_revenue + click_revenue
    
    partner_share = total_revenue * (revenue_share_pct / 100)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE partners SET total_revenue = ? WHERE id = ?',
        (partner_share, partner_id)
    )
    conn.commit()
    conn.close()
    
    return {
        'partner_id': partner_id,
        'site_name': partner['site_name'],
        'total_views': total_views,
        'total_clicks': total_clicks,
        'view_revenue': round(view_revenue, 2),
        'click_revenue': round(click_revenue, 2),
        'total_revenue': round(total_revenue, 2),
        'revenue_share_pct': revenue_share_pct,
        'partner_share': round(partner_share, 2)
    }

def send_webhook_update(partner_id, event_type, data):
    """Send webhook notification to partner site"""
    partner = get_partner(partner_id=partner_id)
    if not partner or not partner.get('webhook_url'):
        return {'error': 'Partner webhook not configured'}
    
    webhook_url = partner['webhook_url']
    webhook_secret = partner.get('webhook_secret')
    
    payload = {
        'event': event_type,
        'timestamp': datetime.now().isoformat(),
        'data': data,
        'source': 'TAYLOR VECTOR TERMINAL'
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': webhook_secret
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        success = response.status_code == 200
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO webhook_logs (
                partner_id, endpoint, payload, response_code, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (partner_id, webhook_url, json.dumps(payload), 
              response.status_code, 1 if success else 0, 
              None if success else response.text))
        conn.commit()
        conn.close()
        
        return {
            'success': success,
            'status_code': response.status_code,
            'response': response.text
        }
    except Exception as e:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO webhook_logs (
                partner_id, endpoint, payload, response_code, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (partner_id, webhook_url, json.dumps(payload), 0, 0, str(e)))
        conn.commit()
        conn.close()
        
        return {'success': False, 'error': str(e)}

def get_partner_analytics(partner_id, days=30):
    """Get analytics for a specific partner"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    start_date = datetime.now() - timedelta(days=days)
    
    analytics = conn.execute('''
        SELECT 
            event_type,
            widget_type,
            COUNT(*) as count,
            DATE(timestamp) as date
        FROM partner_analytics
        WHERE partner_id = ? AND timestamp >= ?
        GROUP BY event_type, widget_type, DATE(timestamp)
        ORDER BY date DESC
    ''', (partner_id, start_date.strftime('%Y-%m-%d'))).fetchall()
    
    conn.close()
    
    return [dict(row) for row in analytics]

def get_webhook_logs(partner_id, limit=50):
    """Get webhook delivery logs for partner"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    
    logs = conn.execute('''
        SELECT * FROM webhook_logs
        WHERE partner_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (partner_id, limit)).fetchall()
    
    conn.close()
    
    return [dict(row) for row in logs]

if __name__ == '__main__':
    init_partnership_database()
    print("✅ Partnership database initialized")
    
    demo_partner = add_partner(
        site_name='Basketball Index',
        api_endpoint='https://basketballindex.com/api/v1/tusg',
        revenue_share=50.0,
        integration_type='full_integration',
        webhook_url='https://basketballindex.com/webhooks/tusg-update',
        custom_branding={
            'primary_color': '#FF6B35',
            'logo_url': 'https://basketballindex.com/logo.png',
            'site_url': 'https://basketballindex.com'
        }
    )
    
    print(f"✅ Demo partner created: {demo_partner}")
