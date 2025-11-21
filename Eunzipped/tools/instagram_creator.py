"""
TAYLOR VECTOR TERMINAL - Instagram Metrics Visualizer
Auto-generates Instagram-ready TUSG%/PVR charts and graphics
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
import json
import os
from datetime import datetime
import io

BRAND_CYAN = '#00d4ff'
BRAND_GREEN = '#00ff88'
WATERMARK = 'TAYLOR VECTOR TERMINAL'

script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(script_dir, 'instagram_output')
LEADERBOARD_FILE = os.path.join(os.path.dirname(script_dir), 'leaderboard', 'data', 'all_time_tusg.json')

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_leaderboard_data():
    """Load historical player data"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading leaderboard: {e}")
        return []

def create_player_stat_card(player_data, custom_text='', custom_color=None):
    """
    Template 1: Player stat card with TUSG%, PVR, stats
    1080x1080 Instagram square format
    """
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    ax.set_xlim(0, 1080)
    ax.set_ylim(0, 1080)
    ax.axis('off')
    
    bg_color = custom_color if custom_color else '#0a0a0a'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    player_name = player_data.get('player', 'Unknown')
    season = player_data.get('season', 'N/A')
    tusg = player_data.get('tusg', 0)
    pvr = player_data.get('pvr', 0)
    ppg = player_data.get('ppg', 0)
    apg = player_data.get('apg', 0)
    mpg = player_data.get('mpg', 0)
    
    ax.text(540, 950, player_name, 
            color=BRAND_CYAN, fontsize=56, weight='bold', 
            ha='center', va='top', family='sans-serif')
    
    ax.text(540, 860, f"{season} Season", 
            color='white', fontsize=32, 
            ha='center', va='top', family='sans-serif')
    
    metric_box_y = 650
    metric_box_height = 180
    
    rect1 = patches.Rectangle((90, metric_box_y), 400, metric_box_height,
                               linewidth=3, edgecolor=BRAND_CYAN, 
                               facecolor='#1a1a1a', alpha=0.9)
    ax.add_patch(rect1)
    
    ax.text(290, metric_box_y + 120, 'TUSG%', 
            color='white', fontsize=28, ha='center', va='center')
    ax.text(290, metric_box_y + 50, f'{tusg:.1f}%', 
            color=BRAND_CYAN, fontsize=52, weight='bold', 
            ha='center', va='center', family='monospace')
    
    rect2 = patches.Rectangle((590, metric_box_y), 400, metric_box_height,
                               linewidth=3, edgecolor=BRAND_GREEN, 
                               facecolor='#1a1a1a', alpha=0.9)
    ax.add_patch(rect2)
    
    ax.text(790, metric_box_y + 120, 'PVR', 
            color='white', fontsize=28, ha='center', va='center')
    ax.text(790, metric_box_y + 50, f'{pvr:.1f}', 
            color=BRAND_GREEN, fontsize=52, weight='bold', 
            ha='center', va='center', family='monospace')
    
    stats_y = 420
    stats = [
        f'{ppg:.1f} PPG',
        f'{apg:.1f} APG',
        f'{mpg:.1f} MPG'
    ]
    
    for i, stat in enumerate(stats):
        ax.text(540, stats_y - (i * 70), stat, 
                color='white', fontsize=36, 
                ha='center', va='center', family='sans-serif')
    
    if custom_text:
        ax.text(540, 180, custom_text, 
                color=BRAND_GREEN, fontsize=28, 
                ha='center', va='center', family='sans-serif',
                style='italic')
    
    ax.text(540, 80, WATERMARK, 
            color='white', fontsize=22, alpha=0.6,
            ha='center', va='center', family='monospace')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"stat_card_{player_name.replace(' ', '_')}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    plt.tight_layout(pad=0)
    plt.savefig(filepath, facecolor=bg_color, dpi=100, bbox_inches='tight')
    plt.close()
    
    return filepath

def create_top_performer_card(player_data, game_info=''):
    """
    Template 2: Daily top performer highlight
    """
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    ax.set_xlim(0, 1080)
    ax.set_ylim(0, 1080)
    ax.axis('off')
    
    bg_color = '#0a0a0a'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    ax.text(540, 980, '🔥 TOP PERFORMER 🔥', 
            color=BRAND_CYAN, fontsize=48, weight='bold', 
            ha='center', va='top', family='sans-serif')
    
    ax.text(540, 890, datetime.now().strftime('%B %d, %Y'), 
            color='white', fontsize=28, alpha=0.8,
            ha='center', va='top', family='sans-serif')
    
    player_name = player_data.get('player', 'Unknown')
    
    ax.text(540, 780, player_name, 
            color=BRAND_GREEN, fontsize=64, weight='bold', 
            ha='center', va='top', family='sans-serif')
    
    season = player_data.get('season', 'N/A')
    ax.text(540, 690, f"{season} Season", 
            color='white', fontsize=32, 
            ha='center', va='top', family='sans-serif')
    
    tusg = player_data.get('tusg', 0)
    pvr = player_data.get('pvr', 0)
    ppg = player_data.get('ppg', 0)
    apg = player_data.get('apg', 0)
    
    metrics_y = 520
    ax.text(270, metrics_y, f'{tusg:.1f}%', 
            color=BRAND_CYAN, fontsize=72, weight='bold', 
            ha='center', va='center', family='monospace')
    ax.text(270, metrics_y - 80, 'TUSG%', 
            color='white', fontsize=28, 
            ha='center', va='center')
    
    ax.text(810, metrics_y, f'{pvr:.1f}', 
            color=BRAND_GREEN, fontsize=72, weight='bold', 
            ha='center', va='center', family='monospace')
    ax.text(810, metrics_y - 80, 'PVR', 
            color='white', fontsize=28, 
            ha='center', va='center')
    
    ax.text(540, 280, f'{ppg:.1f} PPG  •  {apg:.1f} APG', 
            color='white', fontsize=38, 
            ha='center', va='center', family='sans-serif')
    
    if game_info:
        ax.text(540, 180, game_info, 
                color=BRAND_CYAN, fontsize=26, 
                ha='center', va='center', family='sans-serif',
                style='italic')
    
    ax.text(540, 80, WATERMARK, 
            color='white', fontsize=22, alpha=0.6,
            ha='center', va='center', family='monospace')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"top_performer_{player_name.replace(' ', '_')}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    plt.tight_layout(pad=0)
    plt.savefig(filepath, facecolor=bg_color, dpi=100, bbox_inches='tight')
    plt.close()
    
    return filepath

def create_comparison_card(player1_data, player2_data, title='HEAD TO HEAD'):
    """
    Template 3: Player A vs Player B comparison
    """
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    ax.set_xlim(0, 1080)
    ax.set_ylim(0, 1080)
    ax.axis('off')
    
    bg_color = '#0a0a0a'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    ax.text(540, 980, title, 
            color=BRAND_CYAN, fontsize=48, weight='bold', 
            ha='center', va='top', family='sans-serif')
    
    p1_name = player1_data.get('player', 'Player 1')
    p2_name = player2_data.get('player', 'Player 2')
    
    ax.text(270, 860, p1_name, 
            color=BRAND_CYAN, fontsize=38, weight='bold', 
            ha='center', va='top', family='sans-serif')
    ax.text(270, 800, player1_data.get('season', 'N/A'), 
            color='white', fontsize=24, alpha=0.8,
            ha='center', va='top', family='sans-serif')
    
    ax.text(540, 860, 'VS', 
            color='white', fontsize=48, weight='bold', 
            ha='center', va='top', family='sans-serif')
    
    ax.text(810, 860, p2_name, 
            color=BRAND_GREEN, fontsize=38, weight='bold', 
            ha='center', va='top', family='sans-serif')
    ax.text(810, 800, player2_data.get('season', 'N/A'), 
            color='white', fontsize=24, alpha=0.8,
            ha='center', va='top', family='sans-serif')
    
    metrics = [
        ('TUSG%', 'tusg', 680),
        ('PVR', 'pvr', 520),
        ('PPG', 'ppg', 360),
        ('APG', 'apg', 200)
    ]
    
    for label, key, y_pos in metrics:
        ax.text(540, y_pos, label, 
                color='white', fontsize=28, 
                ha='center', va='center', family='sans-serif')
        
        p1_val = player1_data.get(key, 0)
        p2_val = player2_data.get(key, 0)
        
        p1_color = BRAND_CYAN if p1_val > p2_val else 'white'
        p2_color = BRAND_GREEN if p2_val > p1_val else 'white'
        
        ax.text(270, y_pos, f'{p1_val:.1f}', 
                color=p1_color, fontsize=42, weight='bold', 
                ha='center', va='center', family='monospace')
        
        ax.text(810, y_pos, f'{p2_val:.1f}', 
                color=p2_color, fontsize=42, weight='bold', 
                ha='center', va='center', family='monospace')
    
    ax.text(540, 80, WATERMARK, 
            color='white', fontsize=22, alpha=0.6,
            ha='center', va='center', family='monospace')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"comparison_{p1_name.replace(' ', '_')}_vs_{p2_name.replace(' ', '_')}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    plt.tight_layout(pad=0)
    plt.savefig(filepath, facecolor=bg_color, dpi=100, bbox_inches='tight')
    plt.close()
    
    return filepath

def create_leaderboard_card(top_n=10):
    """
    Template 4: All-time TUSG% leaderboard
    """
    leaderboard = load_leaderboard_data()[:top_n]
    
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    ax.set_xlim(0, 1080)
    ax.set_ylim(0, 1080)
    ax.axis('off')
    
    bg_color = '#0a0a0a'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    ax.text(540, 1000, 'ALL-TIME TUSG% LEADERS', 
            color=BRAND_CYAN, fontsize=52, weight='bold', 
            ha='center', va='top', family='sans-serif')
    
    start_y = 900
    row_height = 75
    
    for i, player in enumerate(leaderboard):
        y_pos = start_y - (i * row_height)
        
        rank_color = BRAND_CYAN if i < 3 else 'white'
        
        ax.text(120, y_pos, f"#{i+1}", 
                color=rank_color, fontsize=32, weight='bold', 
                ha='center', va='center', family='sans-serif')
        
        ax.text(250, y_pos, player['player'], 
                color='white', fontsize=28, 
                ha='left', va='center', family='sans-serif')
        
        ax.text(650, y_pos, player['season'], 
                color='white', fontsize=24, alpha=0.7,
                ha='left', va='center', family='sans-serif')
        
        ax.text(870, y_pos, f"{player['tusg']:.1f}%", 
                color=BRAND_GREEN, fontsize=32, weight='bold', 
                ha='right', va='center', family='monospace')
        
        ax.text(940, y_pos, f"{player['pvr']:.1f}", 
                color=BRAND_CYAN, fontsize=26, 
                ha='right', va='center', family='monospace')
    
    ax.text(540, 80, WATERMARK, 
            color='white', fontsize=22, alpha=0.6,
            ha='center', va='center', family='monospace')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"leaderboard_top{top_n}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    plt.tight_layout(pad=0)
    plt.savefig(filepath, facecolor=bg_color, dpi=100, bbox_inches='tight')
    plt.close()
    
    return filepath

def get_recent_images(limit=12):
    """Get list of recently generated images"""
    try:
        files = []
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.png'):
                filepath = os.path.join(OUTPUT_DIR, filename)
                files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'timestamp': os.path.getmtime(filepath)
                })
        
        files.sort(key=lambda x: x['timestamp'], reverse=True)
        return files[:limit]
    except Exception as e:
        print(f"Error getting recent images: {e}")
        return []

if __name__ == '__main__':
    print("🎨 TAYLOR VECTOR TERMINAL - Instagram Creator")
    print("Generating sample images...")
    
    data = load_leaderboard_data()
    
    if data:
        print("\n1. Creating stat card for #1 player...")
        path1 = create_player_stat_card(data[0])
        print(f"   ✅ Saved: {path1}")
        
        print("\n2. Creating top performer card...")
        path2 = create_top_performer_card(data[0], "Historic Performance")
        print(f"   ✅ Saved: {path2}")
        
        if len(data) >= 2:
            print("\n3. Creating comparison card...")
            path3 = create_comparison_card(data[0], data[1])
            print(f"   ✅ Saved: {path3}")
        
        print("\n4. Creating leaderboard card...")
        path4 = create_leaderboard_card(10)
        print(f"   ✅ Saved: {path4}")
        
        print(f"\n✅ All images saved to: {OUTPUT_DIR}")
    else:
        print("❌ No leaderboard data found")
