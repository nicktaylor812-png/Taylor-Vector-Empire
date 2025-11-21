"""
TAYLOR VECTOR TERMINAL - Instagram Daily Automation
Scheduled daily generation of top performer graphics at 9am
"""

import os
import sys
import time
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.append(os.path.dirname(__file__))
from instagram_creator import create_top_performer_card, load_leaderboard_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_daily_top_performer():
    """
    Generate daily top performer image
    Uses the #1 player from all-time leaderboard as example
    In production, this would use actual previous night's data
    """
    try:
        logger.info("🎨 Starting daily top performer generation...")
        
        data = load_leaderboard_data()
        
        if not data:
            logger.error("❌ No leaderboard data available")
            return
        
        top_player = data[0]
        
        game_info = f"Daily Highlight - {datetime.now().strftime('%B %d, %Y')}"
        
        filepath = create_top_performer_card(top_player, game_info)
        
        logger.info(f"✅ Daily top performer generated: {filepath}")
        logger.info(f"   Player: {top_player['player']} ({top_player['season']})")
        logger.info(f"   TUSG%: {top_player['tusg']:.1f}% | PVR: {top_player['pvr']:.1f}")
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Error generating daily top performer: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_scheduler():
    """
    Run the scheduled job at 9:00 AM daily
    """
    logger.info("=" * 70)
    logger.info("🤖 INSTAGRAM DAILY AUTOMATION - SCHEDULER STARTED")
    logger.info("=" * 70)
    logger.info("📅 Schedule: Daily at 9:00 AM")
    logger.info("🎯 Task: Generate top performer Instagram graphic")
    logger.info("=" * 70)
    
    scheduler = BlockingScheduler()
    
    scheduler.add_job(
        generate_daily_top_performer,
        CronTrigger(hour=9, minute=0),
        id='daily_top_performer',
        name='Generate Daily Top Performer',
        replace_existing=True
    )
    
    logger.info("✅ Scheduler configured successfully")
    logger.info(f"⏰ Next run: {scheduler.get_job('daily_top_performer').next_run_time}")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Scheduler stopped")
        scheduler.shutdown()

def run_once():
    """
    Run the job immediately (for testing)
    """
    logger.info("🧪 Running one-time generation (testing mode)")
    generate_daily_top_performer()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Instagram Daily Automation')
    parser.add_argument('--once', action='store_true', 
                       help='Run once immediately instead of scheduling')
    parser.add_argument('--schedule', action='store_true',
                       help='Run on schedule (9am daily)')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    elif args.schedule:
        run_scheduler()
    else:
        logger.info("Usage:")
        logger.info("  --once      : Run immediately (testing)")
        logger.info("  --schedule  : Run on schedule (9am daily)")
        logger.info("\nDefaulting to --once mode...")
        run_once()
