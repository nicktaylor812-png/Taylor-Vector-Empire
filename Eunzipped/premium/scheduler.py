"""
TAYLOR VECTOR TERMINAL - Daily Report Scheduler
Automatically generates daily edge reports at 6:00 AM
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from premium.daily_edge_report import generate_pdf_report as generate_edge_report
from premium.daily_report import generate_pdf_report
from premium.player_deepdive import get_featured_player_of_week, fetch_player_career_stats, generate_player_deepdive_pdf
from premium.underrated_stars import generate_weekly_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_daily_edge_report_job():
    """
    Job that runs daily at 8am to generate the daily edge report with email
    Task #19 - Enhanced report with charts and email delivery
    """
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🕐 Starting scheduled daily edge report generation for {yesterday}")
        
        filepath = generate_edge_report(date=yesterday, send_email=True)
        
        logger.info(f"✅ Daily edge report generated and emailed successfully: {filepath}")
        
        return filepath
    except Exception as e:
        logger.error(f"❌ Error generating daily edge report: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_daily_report_job():
    """
    Job that runs daily to generate the previous day's report (legacy)
    """
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🕐 Starting scheduled daily report generation for {yesterday}")
        
        filepath = generate_pdf_report(date=yesterday)
        
        logger.info(f"✅ Daily report generated successfully: {filepath}")
        
        return filepath
    except Exception as e:
        logger.error(f"❌ Error generating daily report: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_weekly_player_deepdive_job():
    """
    Job that runs every Monday to generate the featured player deep dive
    """
    try:
        logger.info(f"🕐 Starting scheduled weekly player deep dive generation")
        
        # Get featured player of the week
        featured_player = get_featured_player_of_week()
        
        logger.info(f"📊 Featured player this week: {featured_player}")
        
        # Fetch career stats
        career_stats = fetch_player_career_stats(featured_player)
        
        if not career_stats:
            logger.warning(f"⚠️ No career statistics found for {featured_player}")
            return None
        
        logger.info(f"✅ Found {len(career_stats)} seasons of data for {featured_player}")
        
        # Generate PDF
        filepath = generate_player_deepdive_pdf(featured_player, career_stats)
        
        logger.info(f"✅ Weekly player deep dive generated successfully: {filepath}")
        
        return filepath
    except Exception as e:
        logger.error(f"❌ Error generating weekly player deep dive: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_weekly_underrated_stars_job():
    """
    Job that runs every Thursday to generate the underrated stars report
    """
    try:
        logger.info(f"🕐 Starting scheduled weekly underrated stars report generation")
        
        # Generate report
        filepath = generate_weekly_report()
        
        logger.info(f"✅ Weekly underrated stars report generated successfully: {filepath}")
        
        return filepath
    except Exception as e:
        logger.error(f"❌ Error generating weekly underrated stars report: {e}")
        import traceback
        traceback.print_exc()
        return None

def start_scheduler():
    """
    Start the APScheduler background scheduler
    """
    scheduler = BackgroundScheduler()
    
    # Schedule daily edge report generation at 8:00 AM every day (Task #19)
    scheduler.add_job(
        generate_daily_edge_report_job,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_edge_report_8am',
        name='Daily Edge Report Generation (Enhanced)',
        replace_existing=True
    )
    
    # Schedule legacy daily report generation at 6:00 AM every day
    scheduler.add_job(
        generate_daily_report_job,
        trigger=CronTrigger(hour=6, minute=0),
        id='daily_report_6am',
        name='Daily Report Generation (Legacy)',
        replace_existing=True
    )
    
    # Schedule weekly player deep dive generation every Monday at 9:00 AM
    scheduler.add_job(
        generate_weekly_player_deepdive_job,
        trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_player_deepdive_monday',
        name='Weekly Player Deep Dive Generation',
        replace_existing=True
    )
    
    # Schedule weekly underrated stars report every Friday at 10:00 AM
    scheduler.add_job(
        generate_weekly_underrated_stars_job,
        trigger=CronTrigger(day_of_week='fri', hour=10, minute=0),
        id='weekly_underrated_stars_friday',
        name='Weekly Underrated Stars Report Generation',
        replace_existing=True
    )
    
    scheduler.start()
    
    logger.info("⏰ Schedulers started:")
    logger.info("   - Daily Edge Report (Enhanced): 8:00 AM daily")
    logger.info("   - Daily Report (Legacy): 6:00 AM daily")
    logger.info("   - Weekly Player Deep Dive: 9:00 AM every Monday")
    logger.info("   - Weekly Underrated Stars Report: 10:00 AM every Friday")
    
    return scheduler

def stop_scheduler(scheduler):
    """
    Stop the scheduler gracefully
    """
    if scheduler:
        scheduler.shutdown()
        logger.info("⏹️ Daily report scheduler stopped")

if __name__ == '__main__':
    # Test the scheduler
    logger.info("Testing daily edge report scheduler...")
    
    # Test immediate generation
    logger.info("Running test generation...")
    generate_daily_edge_report_job()
    
    # Start scheduler
    scheduler = start_scheduler()
    
    try:
        # Keep running
        import time
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        stop_scheduler(scheduler)
