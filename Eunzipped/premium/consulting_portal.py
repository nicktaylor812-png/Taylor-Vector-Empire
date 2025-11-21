"""
TAYLOR VECTOR TERMINAL - Betting Group Consulting Portal
White-labeled multi-tenant portal for betting groups with premium features

Pricing: $499/month per group (10 members), $99 for each additional member
"""

import sqlite3
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, 'consulting_groups.db')

# Role definitions
ROLE_ADMIN = 'admin'
ROLE_ANALYST = 'analyst'
ROLE_MEMBER = 'member'

ROLES = {
    ROLE_ADMIN: {
        'name': 'Admin',
        'permissions': ['manage_group', 'manage_members', 'manage_branding', 'view_picks', 'post_chat', 'view_analytics', 'manage_thresholds']
    },
    ROLE_ANALYST: {
        'name': 'Analyst',
        'permissions': ['view_picks', 'post_chat', 'view_analytics']
    },
    ROLE_MEMBER: {
        'name': 'Member',
        'permissions': ['view_picks', 'post_chat']
    }
}

# Pricing
BASE_PRICE = 499  # $499/month for 10 members
PER_MEMBER_PRICE = 99  # $99 per additional member


def init_database():
    """Initialize consulting portal database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1,
            member_count INTEGER DEFAULT 0,
            monthly_price REAL DEFAULT 499.00,
            
            -- White-label branding
            logo_url TEXT,
            primary_color TEXT DEFAULT '#FF5722',
            secondary_color TEXT DEFAULT '#FFC107',
            custom_domain TEXT,
            
            -- Custom thresholds
            min_tusg REAL DEFAULT 55.0,
            min_pvr REAL DEFAULT 15.0,
            min_edge REAL DEFAULT 65.0,
            
            -- Performance tracking
            total_picks INTEGER DEFAULT 0,
            successful_picks INTEGER DEFAULT 0,
            accuracy_rate REAL DEFAULT 0.0,
            total_roi REAL DEFAULT 0.0
        )
    ''')
    
    # Members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME,
            active BOOLEAN DEFAULT 1,
            FOREIGN KEY (group_id) REFERENCES groups (id),
            UNIQUE(group_id, email)
        )
    ''')
    
    # Group picks table (filtered picks for each group based on thresholds)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            game TEXT NOT NULL,
            pick TEXT NOT NULL,
            edge REAL NOT NULL,
            home_tusg REAL,
            away_tusg REAL,
            home_pvr REAL,
            away_pvr REAL,
            spread REAL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            posted_by TEXT,
            FOREIGN KEY (group_id) REFERENCES groups (id),
            FOREIGN KEY (posted_by) REFERENCES members (id)
        )
    ''')
    
    # Group chat table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            member_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            edited BOOLEAN DEFAULT 0,
            FOREIGN KEY (group_id) REFERENCES groups (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
    ''')
    
    # Activity log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            member_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
    ''')
    
    conn.commit()
    conn.close()


def generate_id(prefix: str = '') -> str:
    """Generate unique ID"""
    return f"{prefix}{secrets.token_urlsafe(16)}"


def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash


def calculate_group_price(member_count: int) -> float:
    """Calculate monthly price for group based on member count"""
    if member_count <= 10:
        return BASE_PRICE
    else:
        additional_members = member_count - 10
        return BASE_PRICE + (additional_members * PER_MEMBER_PRICE)


class ConsultingGroup:
    """Manages betting group operations"""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_group(self, name: str, slug: str, admin_email: str, admin_password: str,
                     primary_color: str = '#FF5722', secondary_color: str = '#FFC107') -> Dict[str, Any]:
        """Create new betting group with admin user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if slug already exists
            existing = cursor.execute('SELECT id FROM groups WHERE slug = ?', (slug,)).fetchone()
            if existing:
                return {'success': False, 'error': 'Group slug already exists'}
            
            # Create group
            group_id = generate_id('grp_')
            cursor.execute('''
                INSERT INTO groups (id, name, slug, primary_color, secondary_color, member_count, monthly_price)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            ''', (group_id, name, slug, primary_color, secondary_color, BASE_PRICE))
            
            # Create admin user
            member_id = generate_id('mem_')
            username = admin_email.split('@')[0]
            password_hash = hash_password(admin_password)
            
            cursor.execute('''
                INSERT INTO members (id, group_id, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (member_id, group_id, username, admin_email, password_hash, ROLE_ADMIN))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_log (group_id, member_id, action, details)
                VALUES (?, ?, ?, ?)
            ''', (group_id, member_id, 'group_created', f'Group "{name}" created'))
            
            conn.commit()
            
            return {
                'success': True,
                'group_id': group_id,
                'slug': slug,
                'admin_id': member_id
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_group_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get group details by slug"""
        conn = self._get_connection()
        group = conn.execute('SELECT * FROM groups WHERE slug = ? AND active = 1', (slug,)).fetchone()
        conn.close()
        
        if group:
            return dict(group)
        return None
    
    def get_group_by_id(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group details by ID"""
        conn = self._get_connection()
        group = conn.execute('SELECT * FROM groups WHERE id = ? AND active = 1', (group_id,)).fetchone()
        conn.close()
        
        if group:
            return dict(group)
        return None
    
    def update_group_branding(self, group_id: str, logo_url: str = None,
                             primary_color: str = None, secondary_color: str = None,
                             custom_domain: str = None) -> Dict[str, Any]:
        """Update group branding settings"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if logo_url:
            updates.append('logo_url = ?')
            params.append(logo_url)
        if primary_color:
            updates.append('primary_color = ?')
            params.append(primary_color)
        if secondary_color:
            updates.append('secondary_color = ?')
            params.append(secondary_color)
        if custom_domain:
            updates.append('custom_domain = ?')
            params.append(custom_domain)
        
        if not updates:
            return {'success': False, 'error': 'No updates provided'}
        
        params.append(group_id)
        query = f"UPDATE groups SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def update_group_thresholds(self, group_id: str, min_tusg: float = None,
                                min_pvr: float = None, min_edge: float = None) -> Dict[str, Any]:
        """Update group's custom metric thresholds"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if min_tusg is not None:
            updates.append('min_tusg = ?')
            params.append(min_tusg)
        if min_pvr is not None:
            updates.append('min_pvr = ?')
            params.append(min_pvr)
        if min_edge is not None:
            updates.append('min_edge = ?')
            params.append(min_edge)
        
        if not updates:
            return {'success': False, 'error': 'No thresholds provided'}
        
        params.append(group_id)
        query = f"UPDATE groups SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def add_member(self, group_id: str, email: str, password: str, role: str = ROLE_MEMBER) -> Dict[str, Any]:
        """Add new member to group"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if member already exists
            existing = cursor.execute(
                'SELECT id FROM members WHERE group_id = ? AND email = ?',
                (group_id, email)
            ).fetchone()
            
            if existing:
                return {'success': False, 'error': 'Member already exists in this group'}
            
            # Create member
            member_id = generate_id('mem_')
            username = email.split('@')[0]
            password_hash = hash_password(password)
            
            cursor.execute('''
                INSERT INTO members (id, group_id, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (member_id, group_id, username, email, password_hash, role))
            
            # Update group member count and price
            current_count = cursor.execute(
                'SELECT member_count FROM groups WHERE id = ?',
                (group_id,)
            ).fetchone()['member_count']
            
            new_count = current_count + 1
            new_price = calculate_group_price(new_count)
            
            cursor.execute('''
                UPDATE groups SET member_count = ?, monthly_price = ?
                WHERE id = ?
            ''', (new_count, new_price, group_id))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_log (group_id, member_id, action, details)
                VALUES (?, ?, ?, ?)
            ''', (group_id, member_id, 'member_added', f'New {role} added: {email}'))
            
            conn.commit()
            
            return {
                'success': True,
                'member_id': member_id,
                'new_member_count': new_count,
                'new_monthly_price': new_price
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def remove_member(self, group_id: str, member_id: str) -> Dict[str, Any]:
        """Remove member from group"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if member is the only admin
            admins = cursor.execute(
                'SELECT COUNT(*) as count FROM members WHERE group_id = ? AND role = ? AND active = 1',
                (group_id, ROLE_ADMIN)
            ).fetchone()['count']
            
            member = cursor.execute(
                'SELECT role FROM members WHERE id = ?',
                (member_id,)
            ).fetchone()
            
            if member and member['role'] == ROLE_ADMIN and admins <= 1:
                return {'success': False, 'error': 'Cannot remove the only admin'}
            
            # Deactivate member
            cursor.execute('UPDATE members SET active = 0 WHERE id = ?', (member_id,))
            
            # Update group member count and price
            current_count = cursor.execute(
                'SELECT member_count FROM groups WHERE id = ?',
                (group_id,)
            ).fetchone()['member_count']
            
            new_count = max(current_count - 1, 1)
            new_price = calculate_group_price(new_count)
            
            cursor.execute('''
                UPDATE groups SET member_count = ?, monthly_price = ?
                WHERE id = ?
            ''', (new_count, new_price, group_id))
            
            # Log activity
            cursor.execute('''
                INSERT INTO activity_log (group_id, member_id, action, details)
                VALUES (?, ?, ?, ?)
            ''', (group_id, member_id, 'member_removed', f'Member {member_id} removed'))
            
            conn.commit()
            
            return {
                'success': True,
                'new_member_count': new_count,
                'new_monthly_price': new_price
            }
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def update_member_role(self, member_id: str, new_role: str) -> Dict[str, Any]:
        """Update member role"""
        if new_role not in ROLES:
            return {'success': False, 'error': 'Invalid role'}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE members SET role = ? WHERE id = ?', (new_role, member_id))
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def authenticate_member(self, group_slug: str, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate member login"""
        conn = self._get_connection()
        
        member = conn.execute('''
            SELECT m.*, g.slug as group_slug, g.name as group_name
            FROM members m
            JOIN groups g ON m.group_id = g.id
            WHERE g.slug = ? AND m.email = ? AND m.active = 1 AND g.active = 1
        ''', (group_slug, email)).fetchone()
        
        conn.close()
        
        if member and verify_password(password, member['password_hash']):
            return dict(member)
        return None
    
    def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """Get all active members of a group"""
        conn = self._get_connection()
        
        members = conn.execute('''
            SELECT id, username, email, role, joined_at, last_active
            FROM members
            WHERE group_id = ? AND active = 1
            ORDER BY joined_at
        ''', (group_id,)).fetchall()
        
        conn.close()
        
        return [dict(m) for m in members]
    
    def add_group_pick(self, group_id: str, game: str, pick: str, edge: float,
                      home_tusg: float, away_tusg: float, home_pvr: float, away_pvr: float,
                      spread: float, posted_by: str = None) -> Dict[str, Any]:
        """Add pick to group's feed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO group_picks 
            (group_id, game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread, posted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (group_id, game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread, posted_by))
        
        pick_id = cursor.lastrowid
        
        # Update group total picks
        cursor.execute('''
            UPDATE groups SET total_picks = total_picks + 1
            WHERE id = ?
        ''', (group_id,))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'pick_id': pick_id}
    
    def get_group_picks(self, group_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get group's picks feed"""
        conn = self._get_connection()
        
        picks = conn.execute('''
            SELECT p.*, m.username as posted_by_username
            FROM group_picks p
            LEFT JOIN members m ON p.posted_by = m.id
            WHERE p.group_id = ?
            ORDER BY p.timestamp DESC
            LIMIT ?
        ''', (group_id, limit)).fetchall()
        
        conn.close()
        
        return [dict(p) for p in picks]
    
    def update_pick_result(self, pick_id: int, result: str, status: str = 'completed') -> Dict[str, Any]:
        """Update pick result (win/loss)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get pick details
        pick = cursor.execute('SELECT * FROM group_picks WHERE id = ?', (pick_id,)).fetchone()
        
        if not pick:
            conn.close()
            return {'success': False, 'error': 'Pick not found'}
        
        group_id = pick['group_id']
        
        # Update pick
        cursor.execute('''
            UPDATE group_picks SET status = ?, result = ?
            WHERE id = ?
        ''', (status, result, pick_id))
        
        # Update group performance if result is win
        if result == 'win':
            cursor.execute('''
                UPDATE groups SET successful_picks = successful_picks + 1
                WHERE id = ?
            ''', (group_id,))
        
        # Recalculate accuracy
        stats = cursor.execute('''
            SELECT total_picks, successful_picks FROM groups WHERE id = ?
        ''', (group_id,)).fetchone()
        
        if stats['total_picks'] > 0:
            accuracy = (stats['successful_picks'] / stats['total_picks']) * 100
            cursor.execute('UPDATE groups SET accuracy_rate = ? WHERE id = ?', (accuracy, group_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    
    def post_chat_message(self, group_id: str, member_id: str, message: str) -> Dict[str, Any]:
        """Post message to group chat"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO group_chat (group_id, member_id, message)
            VALUES (?, ?, ?)
        ''', (group_id, member_id, message))
        
        message_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message_id': message_id}
    
    def get_group_chat(self, group_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get group chat messages"""
        conn = self._get_connection()
        
        messages = conn.execute('''
            SELECT c.*, m.username, m.role
            FROM group_chat c
            JOIN members m ON c.member_id = m.id
            WHERE c.group_id = ?
            ORDER BY c.timestamp DESC
            LIMIT ?
        ''', (group_id, limit)).fetchall()
        
        conn.close()
        
        return [dict(m) for m in messages]
    
    def get_group_analytics(self, group_id: str) -> Dict[str, Any]:
        """Get comprehensive group analytics"""
        conn = self._get_connection()
        
        # Group stats
        group = conn.execute('SELECT * FROM groups WHERE id = ?', (group_id,)).fetchone()
        
        # Pick statistics
        pick_stats = conn.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(edge) as avg_edge,
                MAX(edge) as max_edge,
                COUNT(CASE WHEN result = 'win' THEN 1 END) as wins,
                COUNT(CASE WHEN result = 'loss' THEN 1 END) as losses
            FROM group_picks
            WHERE group_id = ?
        ''', (group_id,)).fetchone()
        
        # Recent activity
        recent_picks = conn.execute('''
            SELECT timestamp, edge, result
            FROM group_picks
            WHERE group_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (group_id,)).fetchall()
        
        # Member activity
        active_members = conn.execute('''
            SELECT COUNT(*) as count
            FROM members
            WHERE group_id = ? AND active = 1 AND last_active > datetime('now', '-7 days')
        ''', (group_id,)).fetchone()
        
        conn.close()
        
        return {
            'group': dict(group) if group else {},
            'picks': dict(pick_stats) if pick_stats else {},
            'recent_picks': [dict(p) for p in recent_picks],
            'active_members_7d': active_members['count'] if active_members else 0
        }
    
    def get_activity_log(self, group_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get group activity log"""
        conn = self._get_connection()
        
        logs = conn.execute('''
            SELECT a.*, m.username
            FROM activity_log a
            LEFT JOIN members m ON a.member_id = m.id
            WHERE a.group_id = ?
            ORDER BY a.timestamp DESC
            LIMIT ?
        ''', (group_id, limit)).fetchall()
        
        conn.close()
        
        return [dict(log) for log in logs]


# Demo data generation
def create_demo_group():
    """Create demo group with sample data"""
    portal = ConsultingGroup()
    
    # Create demo group
    result = portal.create_group(
        name='Elite Bettors Syndicate',
        slug='demo',
        admin_email='admin@demo.com',
        admin_password='demo123',
        primary_color='#1E88E5',
        secondary_color='#FFC107'
    )
    
    if not result['success']:
        print(f"Demo group already exists or error: {result.get('error')}")
        # Get existing demo group
        demo_group = portal.get_group_by_slug('demo')
        if demo_group:
            group_id = demo_group['id']
        else:
            return
    else:
        group_id = result['group_id']
    
    # Add demo members
    portal.add_member(group_id, 'analyst@demo.com', 'demo123', ROLE_ANALYST)
    portal.add_member(group_id, 'member1@demo.com', 'demo123', ROLE_MEMBER)
    portal.add_member(group_id, 'member2@demo.com', 'demo123', ROLE_MEMBER)
    
    # Add demo picks
    demo_picks = [
        ('Lakers @ Celtics', 'Celtics -4.5', 72.3, 58.2, 52.1, 18.5, 14.2, -4.5),
        ('Warriors @ Nuggets', 'Nuggets -2.5', 68.7, 56.8, 54.2, 16.8, 15.9, -2.5),
        ('Heat @ Bucks', 'Bucks -6.0', 71.5, 59.1, 51.3, 19.2, 13.8, -6.0),
        ('Suns @ Mavs', 'Mavs -3.5', 69.8, 57.4, 53.6, 17.5, 15.2, -3.5),
        ('76ers @ Knicks', 'Knicks -1.5', 67.2, 55.9, 54.1, 16.1, 15.8, -1.5),
    ]
    
    for game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread in demo_picks:
        portal.add_group_pick(group_id, game, pick, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread)
    
    # Add demo chat messages
    members = portal.get_group_members(group_id)
    if members:
        portal.post_chat_message(group_id, members[0]['id'], 'Welcome to the Elite Bettors Syndicate! 🎯')
        portal.post_chat_message(group_id, members[1]['id'], 'Loving these picks! That Celtics edge looks solid.')
        portal.post_chat_message(group_id, members[2]['id'], 'Great to be part of this group!')
    
    print(f"✅ Demo group created successfully! Access at /portal/demo")
    print(f"   Admin login: admin@demo.com / demo123")
    print(f"   Analyst login: analyst@demo.com / demo123")
    print(f"   Member login: member1@demo.com / demo123")


if __name__ == '__main__':
    create_demo_group()
