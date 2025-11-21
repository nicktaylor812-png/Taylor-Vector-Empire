"""
Discord Community Bot for Taylor Vector Terminal
Provides live terminal feed, metric commands, and edge alerts

Requires Discord Bot Token:
- DISCORD_BOT_TOKEN
- EDGE_ALERTS_CHANNEL_ID (optional, for auto-posting)
"""

import discord
from discord import app_commands
from discord.ext import tasks
import sqlite3
import json
import os
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_FILE = 'taylor_62.db'
LEADERBOARD_FILE = 'leaderboard/data/all_time_tusg.json'
POSTED_PICKS_FILE = 'bots/discord_posted_picks.json'
MIN_EDGE_FOR_ALERT = 65.0

BRAND_CYAN = 0x00d4ff
BRAND_GREEN = 0x00ff88
BRAND_RED = 0xff4444

TEAM_PACE = {
    'ATL': 101.8, 'BOS': 99.3, 'BKN': 100.5, 'CHA': 99.8, 'CHI': 98.5, 'CLE': 97.2,
    'DAL': 99.1, 'DEN': 98.8, 'DET': 100.2, 'GSW': 100.9, 'HOU': 101.2, 'IND': 100.6,
    'LAC': 98.7, 'LAL': 99.4, 'MEM': 97.5, 'MIA': 98.3, 'MIL': 99.7, 'MIN': 99.5,
    'NOP': 100.3, 'NYK': 96.8, 'OKC': 98.9, 'ORL': 99.2, 'PHI': 98.1, 'PHX': 100.4,
    'POR': 99.6, 'SAC': 101.5, 'SAS': 99.0, 'TOR': 98.6, 'UTA': 98.4, 'WAS': 100.1
}

TEAM_NAME_MAPPING = {
    'atlanta': 'ATL', 'hawks': 'ATL', 'boston': 'BOS', 'celtics': 'BOS',
    'brooklyn': 'BKN', 'nets': 'BKN', 'charlotte': 'CHA', 'hornets': 'CHA',
    'chicago': 'CHI', 'bulls': 'CHI', 'cleveland': 'CLE', 'cavaliers': 'CLE', 'cavs': 'CLE',
    'dallas': 'DAL', 'mavericks': 'DAL', 'mavs': 'DAL', 'denver': 'DEN', 'nuggets': 'DEN',
    'detroit': 'DET', 'pistons': 'DET', 'golden state': 'GSW', 'warriors': 'GSW',
    'houston': 'HOU', 'rockets': 'HOU', 'indiana': 'IND', 'pacers': 'IND',
    'la clippers': 'LAC', 'clippers': 'LAC', 'lakers': 'LAL', 'la': 'LAL',
    'memphis': 'MEM', 'grizzlies': 'MEM', 'miami': 'MIA', 'heat': 'MIA',
    'milwaukee': 'MIL', 'bucks': 'MIL', 'minnesota': 'MIN', 'timberwolves': 'MIN', 'wolves': 'MIN',
    'new orleans': 'NOP', 'pelicans': 'NOP', 'new york': 'NYK', 'knicks': 'NYK',
    'oklahoma city': 'OKC', 'thunder': 'OKC', 'orlando': 'ORL', 'magic': 'ORL',
    'philadelphia': 'PHI', '76ers': 'PHI', 'sixers': 'PHI', 'phoenix': 'PHX', 'suns': 'PHX',
    'portland': 'POR', 'blazers': 'POR', 'sacramento': 'SAC', 'kings': 'SAC',
    'san antonio': 'SAS', 'spurs': 'SAS', 'toronto': 'TOR', 'raptors': 'TOR',
    'utah': 'UTA', 'jazz': 'UTA', 'washington': 'WAS', 'wizards': 'WAS'
}


class TaylorVectorBot(discord.Client):
    """Discord bot for Taylor Vector Terminal"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)
        self.posted_picks = self._load_posted_picks()
        self.edge_alerts_channel_id = os.getenv('EDGE_ALERTS_CHANNEL_ID')
        
        self._setup_commands()
    
    def _load_posted_picks(self) -> set:
        """Load already posted pick IDs"""
        if not os.path.exists(POSTED_PICKS_FILE):
            return set()
        
        try:
            with open(POSTED_PICKS_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('posted_ids', []))
        except Exception as e:
            logger.error(f"Error loading posted picks: {e}")
            return set()
    
    def _save_posted_picks(self):
        """Save posted pick IDs"""
        os.makedirs('bots', exist_ok=True)
        with open(POSTED_PICKS_FILE, 'w') as f:
            json.dump({'posted_ids': list(self.posted_picks)}, f, indent=2)
    
    def _get_system_status(self) -> tuple[str, str]:
        """Check if system is LIVE or OFFLINE based on last DB update"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(timestamp) FROM picks')
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                last_update = datetime.fromisoformat(result[0])
                time_diff = datetime.now() - last_update
                
                if time_diff < timedelta(minutes=5):
                    return "🟢 LIVE", f"Last update: {time_diff.seconds // 60}m ago"
                else:
                    return "🔴 OFFLINE", f"Last update: {last_update.strftime('%Y-%m-%d %H:%M')}"
            else:
                return "🔴 OFFLINE", "No data in database"
        except Exception as e:
            logger.error(f"Error checking system status: {e}")
            return "⚠️ UNKNOWN", "Database error"
    
    def _fetch_player_stats(self, player_name: str, season: int = 2025) -> Optional[Dict]:
        """Fetch player stats from nbaStats API"""
        try:
            url = f"https://api.server.nbaapi.com/api/playertotals?season={season}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            players = data.get('data', [])
            
            player_name_lower = player_name.lower()
            
            for player in players:
                full_name = player.get('playerName', '').lower()
                if player_name_lower in full_name or full_name in player_name_lower:
                    games = player.get('games', 0)
                    if games == 0:
                        continue
                    
                    team_abbr = player.get('team', 'UNK')
                    
                    return {
                        'player_name': player.get('playerName'),
                        'team': team_abbr,
                        'games_played': games,
                        'min': player.get('minutesPg', 0),
                        'pts': player.get('points', 0) / games,
                        'ast': player.get('assists', 0) / games,
                        'tov': player.get('turnovers', 0) / games,
                        'fga': player.get('fieldAttempts', 0) / games,
                        'fta': player.get('ftAttempts', 0) / games,
                        'team_pace': TEAM_PACE.get(team_abbr, 99.5)
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return None
    
    def _calculate_tusg(self, stats: Dict) -> float:
        """Calculate TUSG% for a player"""
        mp = stats.get('min', 0)
        fga = stats.get('fga', 0)
        tov = stats.get('tov', 0)
        fta = stats.get('fta', 0)
        team_pace = stats.get('team_pace', 99.5)
        
        if mp == 0 or team_pace == 0:
            return 0.0
        
        numerator = fga + tov + (fta * 0.44)
        denominator = (mp / 48) * team_pace
        
        if denominator == 0:
            return 0.0
        
        tusg = (numerator / denominator) * 100
        return round(tusg, 2)
    
    def _calculate_pvr(self, stats: Dict) -> float:
        """Calculate PVR for a player"""
        pts = stats.get('pts', 0)
        ast = stats.get('ast', 0)
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
    
    def _setup_commands(self):
        """Setup all slash commands"""
        
        @self.tree.command(name="tusg", description="Show player's TUSG% and breakdown")
        @app_commands.describe(player="Player name (e.g., 'LeBron James', 'Curry')")
        async def tusg_command(interaction: discord.Interaction, player: str):
            await interaction.response.defer()
            
            stats = self._fetch_player_stats(player)
            
            if not stats:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Could not find stats for **{player}**. Check spelling or try first/last name only.",
                    color=BRAND_RED
                )
                await interaction.followup.send(embed=embed)
                return
            
            tusg = self._calculate_tusg(stats)
            
            status_emoji, status_text = self._get_system_status()
            
            embed = discord.Embed(
                title=f"📊 TUSG% Analysis: {stats['player_name']}",
                description=f"**{stats['team']}** | {stats['games_played']} GP | {stats['min']:.1f} MPG",
                color=BRAND_CYAN
            )
            
            embed.add_field(
                name="🎯 TUSG% (True Usage)",
                value=f"**{tusg:.2f}%**",
                inline=True
            )
            
            usage_rating = "🔥 Elite" if tusg > 35 else "⭐ High" if tusg > 25 else "✅ Solid" if tusg > 20 else "📊 Role Player"
            embed.add_field(
                name="Rating",
                value=usage_rating,
                inline=True
            )
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(
                name="📈 Per Game Stats",
                value=f"**PTS:** {stats['pts']:.1f}\n**AST:** {stats['ast']:.1f}\n**TOV:** {stats['tov']:.1f}",
                inline=True
            )
            
            embed.add_field(
                name="🏀 Usage Breakdown",
                value=f"**FGA:** {stats['fga']:.1f}\n**FTA:** {stats['fta']:.1f}\n**Team Pace:** {stats['team_pace']:.1f}",
                inline=True
            )
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(
                name="📊 What is TUSG%?",
                value="True Usage measures offensive control relative to team pace.\n"
                      f"Formula: `(FGA + TOV + FTA×0.44) / (MP/48 × Pace) × 100`",
                inline=False
            )
            
            embed.set_footer(text=f"Taylor Vector Terminal {status_emoji} | {status_text}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
        
        @self.tree.command(name="pvr", description="Show player's PVR and efficiency")
        @app_commands.describe(player="Player name (e.g., 'Jokic', 'Kevin Durant')")
        async def pvr_command(interaction: discord.Interaction, player: str):
            await interaction.response.defer()
            
            stats = self._fetch_player_stats(player)
            
            if not stats:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Could not find stats for **{player}**. Check spelling or try first/last name only.",
                    color=BRAND_RED
                )
                await interaction.followup.send(embed=embed)
                return
            
            pvr = self._calculate_pvr(stats)
            
            ast_tov = stats['ast'] / stats['tov'] if stats['tov'] > 0 else stats['ast']
            multiplier = 2.3 if ast_tov > 1.8 else 1.8
            
            status_emoji, status_text = self._get_system_status()
            
            embed = discord.Embed(
                title=f"⚡ PVR Analysis: {stats['player_name']}",
                description=f"**{stats['team']}** | {stats['games_played']} GP | {stats['min']:.1f} MPG",
                color=BRAND_GREEN
            )
            
            embed.add_field(
                name="💎 PVR (Production Value)",
                value=f"**{pvr:.2f}**",
                inline=True
            )
            
            pvr_rating = "🔥 Elite" if pvr > 40 else "⭐ Excellent" if pvr > 25 else "✅ Good" if pvr > 15 else "📊 Average" if pvr > 10 else "⚠️ Inefficient"
            embed.add_field(
                name="Efficiency",
                value=pvr_rating,
                inline=True
            )
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(
                name="📈 Per Game Stats",
                value=f"**PTS:** {stats['pts']:.1f}\n**AST:** {stats['ast']:.1f}\n**TOV:** {stats['tov']:.1f}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Efficiency Metrics",
                value=f"**FGA:** {stats['fga']:.1f}\n**AST/TOV:** {ast_tov:.2f}\n**Multiplier:** {multiplier}x",
                inline=True
            )
            
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            embed.add_field(
                name="📊 What is PVR?",
                value="Production-to-Volume Ratio shows scoring efficiency per possession.\n"
                      f"Formula: `[(PTS + AST×Mult) / (FGA + TOV + FTA×0.44 + AST) - 1] × 100`\n"
                      f"AST/TOV ≥1.8 → 2.3x multiplier, else 1.8x",
                inline=False
            )
            
            embed.set_footer(text=f"Taylor Vector Terminal {status_emoji} | {status_text}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
        
        @self.tree.command(name="compare", description="Quick comparison between two players")
        @app_commands.describe(
            player1="First player name",
            player2="Second player name"
        )
        async def compare_command(interaction: discord.Interaction, player1: str, player2: str):
            await interaction.response.defer()
            
            stats1 = self._fetch_player_stats(player1)
            stats2 = self._fetch_player_stats(player2)
            
            if not stats1 or not stats2:
                missing = []
                if not stats1:
                    missing.append(player1)
                if not stats2:
                    missing.append(player2)
                
                embed = discord.Embed(
                    title="❌ Player(s) Not Found",
                    description=f"Could not find stats for: **{', '.join(missing)}**",
                    color=BRAND_RED
                )
                await interaction.followup.send(embed=embed)
                return
            
            tusg1 = self._calculate_tusg(stats1)
            tusg2 = self._calculate_tusg(stats2)
            pvr1 = self._calculate_pvr(stats1)
            pvr2 = self._calculate_pvr(stats2)
            
            status_emoji, status_text = self._get_system_status()
            
            embed = discord.Embed(
                title="⚔️ Player Comparison",
                description=f"**{stats1['player_name']}** ({stats1['team']}) vs **{stats2['player_name']}** ({stats2['team']})",
                color=BRAND_CYAN
            )
            
            tusg_winner = stats1['player_name'] if tusg1 > tusg2 else stats2['player_name']
            pvr_winner = stats1['player_name'] if pvr1 > pvr2 else stats2['player_name']
            
            embed.add_field(
                name=f"📊 TUSG% - Winner: {tusg_winner}",
                value=f"**{stats1['player_name']}:** {tusg1:.2f}%\n**{stats2['player_name']}:** {tusg2:.2f}%\n**Diff:** {abs(tusg1-tusg2):.2f}%",
                inline=False
            )
            
            embed.add_field(
                name=f"⚡ PVR - Winner: {pvr_winner}",
                value=f"**{stats1['player_name']}:** {pvr1:.2f}\n**{stats2['player_name']}:** {pvr2:.2f}\n**Diff:** {abs(pvr1-pvr2):.2f}",
                inline=False
            )
            
            embed.add_field(
                name=f"🏀 {stats1['player_name']} Stats",
                value=f"**PPG:** {stats1['pts']:.1f} | **APG:** {stats1['ast']:.1f}\n**MPG:** {stats1['min']:.1f} | **GP:** {stats1['games_played']}",
                inline=True
            )
            
            embed.add_field(
                name=f"🏀 {stats2['player_name']} Stats",
                value=f"**PPG:** {stats2['pts']:.1f} | **APG:** {stats2['ast']:.1f}\n**MPG:** {stats2['min']:.1f} | **GP:** {stats2['games_played']}",
                inline=True
            )
            
            embed.set_footer(text=f"Taylor Vector Terminal {status_emoji} | {status_text}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
        
        @self.tree.command(name="edge", description="Show latest betting edges")
        @app_commands.describe(min_edge="Minimum edge % to show (default: 65)")
        async def edge_command(interaction: discord.Interaction, min_edge: Optional[int] = 65):
            await interaction.response.defer()
            
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, game, pick, edge, home_tusg, away_tusg, 
                           home_pvr, away_pvr, spread
                    FROM picks
                    WHERE edge >= ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                ''', (min_edge,))
                
                picks = cursor.fetchall()
                conn.close()
                
                if not picks:
                    embed = discord.Embed(
                        title="📊 No High-Edge Picks",
                        description=f"No picks found with edge ≥{min_edge}%.\n\nTry lowering the threshold or wait for new analysis.",
                        color=BRAND_CYAN
                    )
                    status_emoji, status_text = self._get_system_status()
                    embed.set_footer(text=f"Taylor Vector Terminal {status_emoji} | {status_text}")
                    await interaction.followup.send(embed=embed)
                    return
                
                status_emoji, status_text = self._get_system_status()
                
                embed = discord.Embed(
                    title=f"🔥 Latest Betting Edges (≥{min_edge}%)",
                    description=f"Showing top {len(picks)} picks with highest confidence",
                    color=BRAND_GREEN
                )
                
                for idx, pick in enumerate(picks, 1):
                    timestamp, game, pick_text, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread = pick
                    
                    pick_time = datetime.fromisoformat(timestamp)
                    time_ago = datetime.now() - pick_time
                    hours_ago = time_ago.seconds // 3600
                    mins_ago = (time_ago.seconds % 3600) // 60
                    
                    time_str = f"{hours_ago}h {mins_ago}m ago" if hours_ago > 0 else f"{mins_ago}m ago"
                    
                    edge_emoji = "🔥" if edge >= 75 else "🎯" if edge >= 70 else "✅"
                    
                    embed.add_field(
                        name=f"{edge_emoji} #{idx}: {pick_text} | Edge: {edge:.1f}%",
                        value=f"**Game:** {game}\n"
                              f"**TUSG:** Home {home_tusg:.1f}% vs Away {away_tusg:.1f}%\n"
                              f"**PVR:** Home {home_pvr:.1f} vs Away {away_pvr:.1f}\n"
                              f"**Spread:** {spread:+.1f} | **Found:** {time_str}",
                        inline=False
                    )
                
                embed.set_footer(text=f"Taylor Vector Terminal {status_emoji} | {status_text}")
                embed.timestamp = datetime.now()
                
                await interaction.followup.send(embed=embed)
            
            except Exception as e:
                logger.error(f"Error in edge command: {e}")
                embed = discord.Embed(
                    title="❌ Database Error",
                    description="Could not fetch picks. Check bot logs.",
                    color=BRAND_RED
                )
                await interaction.followup.send(embed=embed)
        
        @self.tree.command(name="leaderboard", description="All-time TUSG% top 10 leaderboard")
        async def leaderboard_command(interaction: discord.Interaction):
            await interaction.response.defer()
            
            try:
                with open(LEADERBOARD_FILE, 'r') as f:
                    leaderboard = json.load(f)
                
                top_10 = leaderboard[:10]
                
                status_emoji, status_text = self._get_system_status()
                
                embed = discord.Embed(
                    title="🏆 All-Time TUSG% Leaderboard",
                    description="The most dominant offensive usage seasons in NBA history",
                    color=BRAND_CYAN
                )
                
                leaderboard_text = ""
                for player in top_10:
                    medal = "🥇" if player['rank'] == 1 else "🥈" if player['rank'] == 2 else "🥉" if player['rank'] == 3 else f"`#{player['rank']}`"
                    leaderboard_text += f"{medal} **{player['player']}** ({player['season']})\n"
                    leaderboard_text += f"   TUSG: **{player['tusg']:.1f}%** | PVR: **{player['pvr']:.2f}** | PPG: {player['ppg']:.1f}\n\n"
                
                embed.add_field(
                    name="📊 Top 10 Seasons",
                    value=leaderboard_text,
                    inline=False
                )
                
                embed.add_field(
                    name="🔥 Notable Leaders",
                    value=f"**Highest TUSG%:** {top_10[0]['player']} - {top_10[0]['tusg']:.1f}%\n"
                          f"**Best PVR in Top 10:** {max(top_10, key=lambda x: x['pvr'])['player']} - {max(top_10, key=lambda x: x['pvr'])['pvr']:.2f}\n"
                          f"**Era-Adjusted:** All stats normalized for pace differences",
                    inline=False
                )
                
                embed.set_footer(text=f"Taylor Vector Terminal {status_emoji} | {status_text}")
                embed.timestamp = datetime.now()
                
                await interaction.followup.send(embed=embed)
            
            except Exception as e:
                logger.error(f"Error in leaderboard command: {e}")
                embed = discord.Embed(
                    title="❌ Error Loading Leaderboard",
                    description="Could not load leaderboard data. Check bot logs.",
                    color=BRAND_RED
                )
                await interaction.followup.send(embed=embed)
    
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        await self.tree.sync()
        logger.info("✅ Commands synced")
        
        if not self.check_edge_alerts.is_running():
            self.check_edge_alerts.start()
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"✅ Logged in as {self.user}")
        logger.info(f"🤖 Bot ID: {self.user.id}")
        logger.info(f"🔗 Invite URL: https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=2048&scope=bot%20applications.commands")
        
        status_emoji, status_text = self._get_system_status()
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"NBA Edges {status_emoji}"
            )
        )
        
        logger.info(f"📊 System Status: {status_emoji} {status_text}")
    
    @tasks.loop(minutes=2)
    async def check_edge_alerts(self):
        """Check for new high-edge picks and post to #edge-alerts"""
        if not self.edge_alerts_channel_id:
            return
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, game, pick, edge, home_tusg, away_tusg, 
                       home_pvr, away_pvr, spread
                FROM picks
                WHERE edge >= ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (MIN_EDGE_FOR_ALERT,))
            
            picks = cursor.fetchall()
            conn.close()
            
            for pick in picks:
                pick_id = pick[0]
                
                if pick_id in self.posted_picks:
                    continue
                
                timestamp, game, pick_text, edge, home_tusg, away_tusg, home_pvr, away_pvr, spread = pick[1:]
                
                try:
                    channel = self.get_channel(int(self.edge_alerts_channel_id))
                    
                    if not channel:
                        logger.warning(f"⚠️ Could not find channel {self.edge_alerts_channel_id}")
                        break
                    
                    embed = discord.Embed(
                        title="🚨 HIGH-EDGE PICK ALERT",
                        description=f"**{pick_text}**",
                        color=BRAND_GREEN if edge >= 70 else BRAND_CYAN
                    )
                    
                    embed.add_field(
                        name="🎯 Edge",
                        value=f"**{edge:.1f}%**",
                        inline=True
                    )
                    
                    confidence = "🔥 VERY HIGH" if edge >= 75 else "🎯 HIGH" if edge >= 70 else "✅ SOLID"
                    embed.add_field(
                        name="Confidence",
                        value=confidence,
                        inline=True
                    )
                    
                    embed.add_field(name="\u200b", value="\u200b", inline=False)
                    
                    embed.add_field(
                        name="📊 Game",
                        value=game,
                        inline=False
                    )
                    
                    embed.add_field(
                        name="🏀 TUSG% Differential",
                        value=f"Home: **{home_tusg:.1f}%**\nAway: **{away_tusg:.1f}%**\nDiff: {abs(home_tusg-away_tusg):.1f}%",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="⚡ PVR Differential",
                        value=f"Home: **{home_pvr:.1f}**\nAway: **{away_pvr:.1f}**\nDiff: {abs(home_pvr-away_pvr):.1f}",
                        inline=True
                    )
                    
                    embed.add_field(name="\u200b", value="\u200b", inline=False)
                    
                    embed.add_field(
                        name="📈 Spread",
                        value=f"**{spread:+.1f}**",
                        inline=False
                    )
                    
                    embed.set_footer(text="Taylor Vector Terminal | Data-driven betting edges")
                    embed.timestamp = datetime.now()
                    
                    await channel.send(embed=embed)
                    
                    self.posted_picks.add(pick_id)
                    self._save_posted_picks()
                    
                    logger.info(f"✅ Posted edge alert: {pick_text} ({edge:.1f}%)")
                    
                    await asyncio.sleep(2)
                
                except Exception as e:
                    logger.error(f"❌ Error posting alert: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error checking edge alerts: {e}")
    
    @check_edge_alerts.before_loop
    async def before_check_edge_alerts(self):
        """Wait until bot is ready before starting edge alerts"""
        await self.wait_until_ready()


def main():
    """Main entry point for Discord bot"""
    logger.info("🚀 Starting Taylor Vector Terminal Discord Bot")
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        logger.error("❌ Missing DISCORD_BOT_TOKEN environment variable")
        logger.info("\n📝 Required environment variables:")
        logger.info("   - DISCORD_BOT_TOKEN (required)")
        logger.info("   - EDGE_ALERTS_CHANNEL_ID (optional, for auto-posting)")
        logger.info("\n🔗 Create a bot at: https://discord.com/developers/applications")
        return
    
    edge_channel = os.getenv('EDGE_ALERTS_CHANNEL_ID')
    if edge_channel:
        logger.info(f"✅ Edge alerts channel configured: {edge_channel}")
    else:
        logger.warning("⚠️ EDGE_ALERTS_CHANNEL_ID not set - auto-posting disabled")
    
    try:
        bot = TaylorVectorBot()
        bot.run(token)
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import asyncio
    main()
