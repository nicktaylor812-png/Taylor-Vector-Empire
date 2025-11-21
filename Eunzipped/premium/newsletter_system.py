"""
TAYLOR VECTOR TERMINAL - Newsletter System
Subscriber management and premium content delivery platform
Task #25 - Paid newsletter with free/paid tiers
"""

import sqlite3
import os
import smtplib
import hashlib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWSLETTER_DB = os.path.join(SCRIPT_DIR, 'newsletter.db')
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, 'newsletter_templates')

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER)
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

TIER_PRICING = {
    'free': 0,
    'paid': 29
}

TIER_BENEFITS = {
    'free': ['Weekly highlights email', 'Basic stats and insights', 'Community access'],
    'paid': ['Daily edge reports', 'Weekly player deep dives', 'Exclusive analysis', 'Priority support', 'Advanced analytics']
}

def init_database():
    """Initialize newsletter subscriber database"""
    conn = sqlite3.connect(NEWSLETTER_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            tier TEXT NOT NULL DEFAULT 'free',
            status TEXT NOT NULL DEFAULT 'active',
            join_date TEXT NOT NULL,
            last_email_sent TEXT,
            unsubscribe_token TEXT UNIQUE NOT NULL,
            payment_id TEXT,
            payment_status TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER NOT NULL,
            template TEXT NOT NULL,
            subject TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payment_provider TEXT NOT NULL,
            subscriber_email TEXT NOT NULL,
            amount REAL,
            currency TEXT,
            payment_id TEXT,
            raw_data TEXT,
            processed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Newsletter database initialized")

def generate_unsubscribe_token():
    """Generate unique unsubscribe token"""
    return secrets.token_urlsafe(32)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(NEWSLETTER_DB)
    conn.row_factory = sqlite3.Row
    return conn

def add_subscriber(email, name=None, tier='free', payment_id=None):
    """
    Add new subscriber to newsletter
    
    Args:
        email: Subscriber email address
        name: Subscriber name (optional)
        tier: 'free' or 'paid'
        payment_id: Payment transaction ID for paid subscribers
    
    Returns:
        dict with subscriber info or error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        existing = cursor.execute('SELECT * FROM subscribers WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.close()
            return {'error': 'Email already subscribed', 'subscriber': dict(existing)}
        
        unsubscribe_token = generate_unsubscribe_token()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO subscribers (email, name, tier, status, join_date, unsubscribe_token, payment_id, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?)
        ''', (email, name, tier, now, unsubscribe_token, payment_id, now, now))
        
        subscriber_id = cursor.lastrowid
        conn.commit()
        
        subscriber = cursor.execute('SELECT * FROM subscribers WHERE id = ?', (subscriber_id,)).fetchone()
        conn.close()
        
        welcome_template = 'welcome_paid.html' if tier == 'paid' else 'welcome_free.html'
        send_newsletter(subscriber_id, welcome_template)
        
        return {'success': True, 'subscriber': dict(subscriber)}
    
    except Exception as e:
        return {'error': str(e)}

def upgrade_to_paid(email, payment_id):
    """
    Upgrade subscriber from free to paid tier
    
    Args:
        email: Subscriber email
        payment_id: Payment transaction ID
    
    Returns:
        dict with success/error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        subscriber = cursor.execute('SELECT * FROM subscribers WHERE email = ?', (email,)).fetchone()
        if not subscriber:
            conn.close()
            return {'error': 'Subscriber not found'}
        
        if subscriber['tier'] == 'paid':
            conn.close()
            return {'error': 'Already a paid subscriber'}
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE subscribers 
            SET tier = 'paid', payment_id = ?, payment_status = 'active', updated_at = ?
            WHERE email = ?
        ''', (payment_id, now, email))
        
        conn.commit()
        conn.close()
        
        send_newsletter(subscriber['id'], 'welcome_paid.html')
        
        return {'success': True, 'message': f'Upgraded {email} to paid tier'}
    
    except Exception as e:
        return {'error': str(e)}

def cancel_subscription(email, reason=None):
    """
    Cancel subscriber subscription
    
    Args:
        email: Subscriber email
        reason: Optional cancellation reason
    
    Returns:
        dict with success/error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        subscriber = cursor.execute('SELECT * FROM subscribers WHERE email = ?', (email,)).fetchone()
        if not subscriber:
            conn.close()
            return {'error': 'Subscriber not found'}
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE subscribers 
            SET status = 'cancelled', payment_status = 'cancelled', updated_at = ?
            WHERE email = ?
        ''', (now, email))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Cancelled subscription for {email}'}
    
    except Exception as e:
        return {'error': str(e)}

def unsubscribe_by_token(token):
    """
    Unsubscribe using unique token from email
    
    Args:
        token: Unsubscribe token
    
    Returns:
        dict with success/error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        subscriber = cursor.execute('SELECT * FROM subscribers WHERE unsubscribe_token = ?', (token,)).fetchone()
        if not subscriber:
            conn.close()
            return {'error': 'Invalid unsubscribe token'}
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE subscribers 
            SET status = 'unsubscribed', updated_at = ?
            WHERE unsubscribe_token = ?
        ''', (now, token))
        
        conn.commit()
        conn.close()
        
        send_newsletter(subscriber['id'], 'unsubscribe_confirm.html')
        
        return {'success': True, 'email': subscriber['email']}
    
    except Exception as e:
        return {'error': str(e)}

def get_subscriber_stats():
    """
    Get newsletter statistics
    
    Returns:
        dict with stats
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total = cursor.execute('SELECT COUNT(*) as count FROM subscribers').fetchone()['count']
        active = cursor.execute('SELECT COUNT(*) as count FROM subscribers WHERE status = "active"').fetchone()['count']
        free = cursor.execute('SELECT COUNT(*) as count FROM subscribers WHERE tier = "free" AND status = "active"').fetchone()['count']
        paid = cursor.execute('SELECT COUNT(*) as count FROM subscribers WHERE tier = "paid" AND status = "active"').fetchone()['count']
        
        monthly_revenue = paid * TIER_PRICING['paid']
        annual_revenue = monthly_revenue * 12
        
        recent = cursor.execute('''
            SELECT DATE(join_date) as date, COUNT(*) as count 
            FROM subscribers 
            WHERE join_date >= date('now', '-30 days')
            GROUP BY DATE(join_date)
            ORDER BY date DESC
        ''').fetchall()
        
        conn.close()
        
        return {
            'total_subscribers': total,
            'active_subscribers': active,
            'free_subscribers': free,
            'paid_subscribers': paid,
            'monthly_revenue': monthly_revenue,
            'annual_revenue': annual_revenue,
            'avg_revenue_per_user': monthly_revenue / active if active > 0 else 0,
            'conversion_rate': (paid / total * 100) if total > 0 else 0,
            'recent_signups': [dict(r) for r in recent]
        }
    
    except Exception as e:
        return {'error': str(e)}

def get_all_subscribers(tier=None, status=None, limit=100, offset=0):
    """
    Get list of subscribers with filters
    
    Args:
        tier: Filter by tier ('free', 'paid', or None for all)
        status: Filter by status ('active', 'cancelled', 'unsubscribed', or None for all)
        limit: Max number of results
        offset: Pagination offset
    
    Returns:
        List of subscribers
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM subscribers WHERE 1=1'
        params = []
        
        if tier:
            query += ' AND tier = ?'
            params.append(tier)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY join_date DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        subscribers = cursor.execute(query, params).fetchall()
        conn.close()
        
        return [dict(s) for s in subscribers]
    
    except Exception as e:
        return {'error': str(e)}

def send_newsletter(subscriber_id, template_name, extra_context=None, retry_count=3):
    """
    Send newsletter email to subscriber with retry logic
    
    Args:
        subscriber_id: Subscriber ID
        template_name: Template filename (e.g., 'free_weekly.html')
        extra_context: Additional context for template rendering
        retry_count: Number of retry attempts on failure
    
    Returns:
        dict with success/error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        subscriber = cursor.execute('SELECT * FROM subscribers WHERE id = ?', (subscriber_id,)).fetchone()
        if not subscriber:
            conn.close()
            return {'error': 'Subscriber not found'}
        
        if subscriber['status'] not in ['active']:
            conn.close()
            return {'error': f'Subscriber is {subscriber["status"]}'}
        
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template(template_name)
        
        context = {
            'subscriber_name': subscriber['name'] or 'Subscriber',
            'subscriber_email': subscriber['email'],
            'subscriber_tier': subscriber['tier'],
            'tier_benefits': TIER_BENEFITS[subscriber['tier']],
            'unsubscribe_url': f"{BASE_URL}/newsletter/unsubscribe/{subscriber['unsubscribe_token']}",
            'manage_url': f"{BASE_URL}/newsletter/manage/{subscriber['unsubscribe_token']}",
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'year': datetime.now().year
        }
        
        if extra_context:
            context.update(extra_context)
        
        html_content = template.render(**context)
        
        subject_map = {
            'free_weekly.html': '📊 Your Weekly TAYLOR VECTOR Highlights',
            'paid_daily.html': '⚡ Daily Edge Report - TAYLOR VECTOR TERMINAL',
            'paid_deepdive.html': '🎯 Weekly Player Deep Dive - Premium Analysis',
            'welcome_free.html': '🎉 Welcome to TAYLOR VECTOR!',
            'welcome_paid.html': '🔥 Welcome to TAYLOR VECTOR Premium!',
            'unsubscribe_confirm.html': 'Unsubscribe Confirmation'
        }
        
        subject = subject_map.get(template_name, 'TAYLOR VECTOR Newsletter')
        
        for attempt in range(retry_count):
            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = FROM_EMAIL
                msg['To'] = subscriber['email']
                msg['Subject'] = subject
                
                msg.attach(MIMEText(html_content, 'html'))
                
                if SMTP_USER and SMTP_PASSWORD:
                    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                    server.quit()
                else:
                    print(f"⚠️ Email sending disabled - no SMTP credentials")
                    print(f"Would send to: {subscriber['email']}")
                    print(f"Subject: {subject}")
                
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO email_log (subscriber_id, template, subject, sent_at, status)
                    VALUES (?, ?, ?, ?, 'sent')
                ''', (subscriber_id, template_name, subject, now))
                
                cursor.execute('''
                    UPDATE subscribers 
                    SET last_email_sent = ?, updated_at = ?
                    WHERE id = ?
                ''', (now, now, subscriber_id))
                
                conn.commit()
                conn.close()
                
                return {'success': True, 'email': subscriber['email'], 'template': template_name}
            
            except Exception as email_error:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO email_log (subscriber_id, template, subject, sent_at, status, error_message)
                        VALUES (?, ?, ?, ?, 'failed', ?)
                    ''', (subscriber_id, template_name, subject, now, str(email_error)))
                    
                    conn.commit()
                    conn.close()
                    
                    return {'error': f'Failed to send email after {retry_count} attempts: {str(email_error)}'}
    
    except Exception as e:
        return {'error': str(e)}

def send_newsletter_batch(tier, template_name, extra_context=None):
    """
    Send newsletter to all active subscribers of a specific tier
    
    Args:
        tier: 'free' or 'paid'
        template_name: Template to send
        extra_context: Additional template context
    
    Returns:
        dict with results
    """
    try:
        subscribers = get_all_subscribers(tier=tier, status='active', limit=10000)
        
        results = {
            'total': len(subscribers),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for subscriber in subscribers:
            result = send_newsletter(subscriber['id'], template_name, extra_context)
            
            if result.get('success'):
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'email': subscriber['email'],
                    'error': result.get('error')
                })
            
            time.sleep(0.5)
        
        return results
    
    except Exception as e:
        return {'error': str(e)}

def process_stripe_webhook(event_data):
    """
    Process Stripe webhook event
    
    Args:
        event_data: Stripe event data
    
    Returns:
        dict with processing result
    """
    try:
        event_type = event_data.get('type')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO payment_webhooks (event_type, payment_provider, subscriber_email, raw_data, created_at)
            VALUES (?, 'stripe', ?, ?, ?)
        ''', (event_type, '', str(event_data), now))
        
        webhook_id = cursor.lastrowid
        
        if event_type == 'checkout.session.completed':
            session = event_data.get('data', {}).get('object', {})
            customer_email = session.get('customer_email')
            payment_id = session.get('payment_intent')
            
            if customer_email:
                result = add_subscriber(customer_email, tier='paid', payment_id=payment_id)
                
                cursor.execute('UPDATE payment_webhooks SET processed = 1, subscriber_email = ? WHERE id = ?', 
                             (customer_email, webhook_id))
        
        elif event_type == 'customer.subscription.deleted':
            subscription = event_data.get('data', {}).get('object', {})
            customer_email = subscription.get('customer_email')
            
            if customer_email:
                cancel_subscription(customer_email)
                
                cursor.execute('UPDATE payment_webhooks SET processed = 1, subscriber_email = ? WHERE id = ?',
                             (customer_email, webhook_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'event_type': event_type}
    
    except Exception as e:
        return {'error': str(e)}

def process_paypal_webhook(event_data):
    """
    Process PayPal webhook event
    
    Args:
        event_data: PayPal event data
    
    Returns:
        dict with processing result
    """
    try:
        event_type = event_data.get('event_type')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO payment_webhooks (event_type, payment_provider, subscriber_email, raw_data, created_at)
            VALUES (?, 'paypal', ?, ?, ?)
        ''', (event_type, '', str(event_data), now))
        
        webhook_id = cursor.lastrowid
        
        if event_type == 'PAYMENT.SALE.COMPLETED':
            resource = event_data.get('resource', {})
            payer_email = resource.get('payer', {}).get('payer_info', {}).get('email')
            payment_id = resource.get('id')
            
            if payer_email:
                result = add_subscriber(payer_email, tier='paid', payment_id=payment_id)
                
                cursor.execute('UPDATE payment_webhooks SET processed = 1, subscriber_email = ? WHERE id = ?',
                             (payer_email, webhook_id))
        
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            resource = event_data.get('resource', {})
            subscriber_email = resource.get('subscriber', {}).get('email_address')
            
            if subscriber_email:
                cancel_subscription(subscriber_email)
                
                cursor.execute('UPDATE payment_webhooks SET processed = 1, subscriber_email = ? WHERE id = ?',
                             (subscriber_email, webhook_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'event_type': event_type}
    
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    init_database()
    
    print("\n=== TAYLOR VECTOR Newsletter System ===\n")
    print("Database initialized successfully!")
    print(f"Database location: {NEWSLETTER_DB}")
    print(f"Templates directory: {TEMPLATES_DIR}")
    print(f"\nTier Pricing:")
    print(f"  - Free: ${TIER_PRICING['free']}/month")
    print(f"  - Paid: ${TIER_PRICING['paid']}/month")
