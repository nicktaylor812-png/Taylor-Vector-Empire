"""
TAYLOR VECTOR TERMINAL - Real-Time Edge Notifier
Monitors database for high-edge picks and sends instant notifications via Discord/Telegram
"""

import sqlite3
import time
import os
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_FILE = 'taylor_62.db'
MIN_EDGE = 65.0
POLL_INTERVAL = 10

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
REPLIT_DOMAIN = os.getenv('REPL_SLUG', 'replit.dev')

notified_picks = set()


def get_dashboard_url():
    """Generate dashboard URL"""
    repl_slug = os.getenv('REPL_SLUG', 'taylor-vector-terminal')
    repl_owner = os.getenv('REPL_OWNER', 'user')
    return f"https://{repl_slug}.{repl_owner}.repl.co"


def format_notification_message(pick_data):
    """Format the notification message with all required details"""
    edge = pick_data['edge']
    game = pick_data['game']
    pick = pick_data['pick']
    
    game_parts = game.split(' @ ')
    if len(game_parts) == 2:
        away_team, home_team = game_parts
    else:
        away_team = "Unknown"
        home_team = "Unknown"
    
    pick_team = pick.split(' ')[0] if ' ' in pick else pick
    
    home_tusg = pick_data['home_tusg']
    away_tusg = pick_data['away_tusg']
    home_pvr = pick_data['home_pvr']
    away_pvr = pick_data['away_pvr']
    
    if pick_team in home_team or home_team in pick_team:
        team1_label = home_team
        team1_tusg = home_tusg
        team1_pvr = home_pvr
        team2_label = away_team
        team2_tusg = away_tusg
        team2_pvr = away_pvr
    else:
        team1_label = away_team
        team1_tusg = away_tusg
        team1_pvr = away_pvr
        team2_label = home_team
        team2_tusg = home_tusg
        team2_pvr = home_pvr
    
    dashboard_url = get_dashboard_url()
    
    message = f"""🔥 EDGE DETECTED: {edge:.1f}%

Game: {game}
Pick: {pick}

TUSG%: {team1_label} {team1_tusg:.1f} vs {team2_label} {team2_tusg:.1f}
PVR: {team1_label} {team1_pvr:.1f} vs {team2_label} {team2_pvr:.1f}

{dashboard_url}"""
    
    return message


def send_discord_notification(message):
    """Send notification to Discord webhook"""
    if not DISCORD_WEBHOOK_URL:
        return False
    
    try:
        payload = {
            'content': message,
            'username': 'TAYLOR VECTOR TERMINAL'
        }
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info("✅ Discord notification sent")
            return True
        else:
            logger.error(f"❌ Discord webhook failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Discord error: {e}")
        return False


def send_telegram_notification(message):
    """Send notification to Telegram bot API"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Telegram notification sent")
            return True
        else:
            logger.error(f"❌ Telegram API failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Telegram error: {e}")
        return False


def create_pick_hash(pick_data):
    """Create unique hash for deduplication"""
    return f"{pick_data['game']}|{pick_data['pick']}|{pick_data['edge']:.1f}"


def check_new_picks():
    """Check database for new high-edge picks"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM picks 
            WHERE edge >= ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (MIN_EDGE,))
        
        picks = cursor.fetchall()
        conn.close()
        
        new_picks_found = 0
        
        for pick in picks:
            pick_data = {
                'game': pick['game'],
                'pick': pick['pick'],
                'edge': pick['edge'],
                'home_tusg': pick['home_tusg'],
                'away_tusg': pick['away_tusg'],
                'home_pvr': pick['home_pvr'],
                'away_pvr': pick['away_pvr'],
                'spread': pick['spread'],
                'timestamp': pick['timestamp']
            }
            
            pick_hash = create_pick_hash(pick_data)
            
            if pick_hash not in notified_picks:
                message = format_notification_message(pick_data)
                
                discord_sent = send_discord_notification(message)
                telegram_sent = send_telegram_notification(message)
                
                if discord_sent or telegram_sent:
                    notified_picks.add(pick_hash)
                    new_picks_found += 1
                    logger.info(f"🔥 Notified: {pick_data['pick']} (Edge: {pick_data['edge']:.1f}%)")
        
        if new_picks_found > 0:
            logger.info(f"📤 Sent {new_picks_found} new notification(s)")
        
        if len(notified_picks) > 100:
            oldest = list(notified_picks)[:50]
            for old_pick in oldest:
                notified_picks.remove(old_pick)
            logger.info("🧹 Cleaned up old notifications from memory")
        
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.warning("⏳ Database not ready yet, waiting...")
        else:
            logger.error(f"❌ Database error: {e}")
    except Exception as e:
        logger.error(f"❌ Error checking picks: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main monitoring loop"""
    logger.info("="*70)
    logger.info("🚀 TAYLOR VECTOR TERMINAL - EDGE NOTIFIER")
    logger.info("="*70)
    logger.info(f"📊 Monitoring: {DB_FILE}")
    logger.info(f"🎯 Min Edge: {MIN_EDGE}%")
    logger.info(f"⏱️  Poll Interval: {POLL_INTERVAL}s")
    
    if DISCORD_WEBHOOK_URL:
        logger.info("✅ Discord webhook configured")
    else:
        logger.info("⚠️  Discord webhook not configured (set DISCORD_WEBHOOK_URL)")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        logger.info("✅ Telegram bot configured")
    else:
        logger.info("⚠️  Telegram bot not configured (set TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID)")
    
    if not DISCORD_WEBHOOK_URL and not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        logger.warning("⚠️  No notification channels configured! Set environment variables.")
    
    logger.info("="*70)
    logger.info("👀 Monitoring for high-edge picks...\n")
    
    while True:
        try:
            check_new_picks()
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Edge Notifier shutting down...")
            break
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
