"""
TikTok Explanation Bot
Auto-generates 60-second metric tutorial scripts with timestamps
Designed for TikTok content creation about TUSG%, PVR, and NBA analytics
"""

import json
import os
from datetime import datetime
from typing import Dict, List

SCRIPTS_DIR = 'bots/tiktok_scripts'

SCRIPT_TEMPLATES = {
    'tusg_basics': {
        'title': "TUSG% in 60 seconds: Stop using USG% wrong",
        'topic': 'TUSG% Basics',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "You've been using Usage % wrong this whole time. Let me show you why TUSG% is better.\n\n[On-screen text: \"TRADITIONAL USG% IS BROKEN 🚨\"]\n\nTraditional Usage % ignores pace. A player in 1962 played at 126 possessions per game. Today? 99. That's broken math."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "TUSG% fixes this. True Usage % = how much a player controls the offense, adjusted for team pace.\n\n[Show formula graphic: (FGA + TOV + FTA×0.44) / (MIN/48 × Pace) × 100]\n\nIt answers: 'If this player was on ANY team, how much would they dominate the ball?'\n\nNow we can compare Wilt to Harden. Modern stars to '80s legends. Fair math."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Russell Westbrook 2017: 48.1% TUSG - highest EVER. He controlled nearly HALF his team's possessions.\n\n[Show graphic: Westbrook 48.1% > League Average 20%]\n\nThat's why he averaged a triple-double. Pure ball dominance."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Follow for more NBA metrics that actually make sense. Link in bio for the full TUSG% leaderboard.\n\n[End screen: \"TUSG% > USG%\" + \"Link in bio 🔗\"]"
        },
        'sounds': [
            "original sound (trending audio for sports content)",
            "Storytelling beat (medium tempo)",
            "Upbeat sports commentary audio"
        ],
        'hashtags': "#NBA #Basketball #Analytics #Stats #TUSG #Usage #NBAStats #HoopsAnalytics #BasketballIQ #NBATikTok"
    },
    
    'pvr_basics': {
        'title': "What is PVR? The efficiency metric that predicted Jokić's MVP",
        'topic': 'PVR Basics',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "This metric predicted Nikola Jokić's MVP 3 years before anyone else saw it coming.\n\n[On-screen: \"THE METRIC THAT KNEW 🏆\"]\n\nIt's called PVR. And it's about to change how you watch basketball."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "PVR = Production-to-Volume Ratio. How many points you GENERATE per possession you USE.\n\n[Show formula: (PTS + AST×Mult) / (FGA + TOV + FTA×0.44 + AST) - 1] × 100\n\nTS% only counts your own scoring. PVR counts assists - the points you CREATE for teammates.\n\nHigh PVR = elite efficiency. You're not just scoring, you're making everyone better."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Jokić 2021-22: 44.54 PVR - HIGHEST in the top 15 all-time.\n\n[Show: Curry 40.27, Magic 44.03, Jokić 44.54]\n\nHe scored 27 PPG + 8 APG with zero wasted possessions. That's MVP-level efficiency."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Want to see your favorite player's PVR? Link in bio. Follow for more analytics that actually matter.\n\n[End screen: \"PVR = TRUE EFFICIENCY\" + emoji]"
        },
        'sounds': [
            "Suspenseful reveal audio",
            "Upbeat analytical content music",
            "Sports highlight reel sound"
        ],
        'hashtags': "#NBA #Basketball #PVR #Efficiency #Analytics #Jokic #MVP #Stats #NBAStats #NBAAnalytics"
    },
    
    'westbrook_rule': {
        'title': "Why Russell Westbrook breaks PVR formulas",
        'topic': 'The Westbrook Rule',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "Russell Westbrook broke basketball so bad, we had to create a new rule just for him.\n\n[On-screen: \"THE WESTBROOK PARADOX 🤯\"]\n\nHere's the stat that makes NO sense..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "Westbrook 2017: 48.1% TUSG (highest ever) + 25.11 PVR (really good).\n\nBut here's the problem - he had 5.4 turnovers per game. That should KILL his PVR.\n\n[Show graphic: AST/TOV ratio affects multiplier]\n\nNormal players: AST/TOV < 1.8 = 1.8x assist multiplier\nElite playmakers: AST/TOV > 1.8 = 2.3x assist multiplier\n\nWestbrook's 10.4 assists with 5.4 TOV = 1.93 ratio. Just barely elite."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "That's The Westbrook Rule: obscene usage + high assists + high turnovers = still works.\n\n[Show: 31.6 PPG + 10.4 APG > 5.4 TOV]\n\nThe volume was SO high, the efficiency still mattered. Pure math magic."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Follow for more stats that break your brain. Link in bio for the Westbrook Rule calculator.\n\n[End screen: \"VOLUME > EFFICIENCY?\" + thinking emoji]"
        },
        'sounds': [
            "Mind-blown audio effect",
            "Dramatic reveal music",
            "Energetic sports content beat"
        ],
        'hashtags': "#NBA #Basketball #Westbrook #Analytics #Stats #TripleDouble #Thunder #TUSG #PVR #NBAHistory"
    },
    
    'jokic_mvp': {
        'title': "The metric that predicted Jokić's MVP before anyone else",
        'topic': 'Jokić MVP Prediction',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "In 2019, this metric said Nikola Jokić was the most efficient star in the NBA. Everyone laughed.\n\n[On-screen: \"THEY CALLED IT CRAZY 😂\"]\n\nThree MVPs later... who's laughing now?"
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "PVR = Production Value Ratio. It measures points created (scoring + assists) per possession used.\n\n[Show 2019 stats: Jokić 42.3 PVR vs League Average ~15]\n\nEveryone saw 20 PPG, 7 APG. Good, not MVP.\n\nPVR saw: elite efficiency, zero wasted possessions, perfect playmaking. MVP-caliber impact.\n\nThe difference? PVR counts BOTH scoring AND creating for others."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "2022 MVP season: 27.1 PPG, 7.9 APG, 44.54 PVR.\n\n[Show comparison: Embiid 35.2 PVR, Giannis 38.1 PVR, Jokić 44.54 PVR]\n\nHighest PVR in the top 15 all-time. The metric was right all along."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Want to see next year's MVP before the media? Follow for analytics that predict the future. Link in bio.\n\n[End screen: \"PVR KNOWS 🔮\"]"
        },
        'sounds': [
            "Dramatic prediction reveal",
            "Inspirational sports music",
            "I told you so audio"
        ],
        'hashtags': "#NBA #Basketball #Jokic #MVP #Analytics #Nuggets #NBAStats #PVR #Efficiency #NBATikTok"
    },
    
    'curry_efficiency': {
        'title': "Steph Curry's 2016 season was UNFAIR (by the numbers)",
        'topic': 'Curry 2016 Efficiency',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "Steph Curry's 2016 season wasn't just good. It was mathematically ILLEGAL.\n\n[On-screen: \"73-9 + UNANIMOUS MVP 🐐\"]\n\nHere's the stat that proves it..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "40.27 PVR. For context:\n- League average: ~15 PVR\n- All-Stars: 20-30 PVR\n- MVPs: 30-40 PVR\n- Curry: 40.27 PVR\n\n[Show graphic with tiers]\n\nHe scored 30.1 PPG on absurd efficiency WHILE creating for teammates. Every possession was productive.\n\nAnd his TUSG%? Only 36.87%. He wasn't even dominating the ball like Westbrook."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Translation: Lower usage than Harden, higher efficiency than anyone.\n\n[Show: 402 threes + 67 wins + 40.27 PVR = UNSTOPPABLE]\n\nThat's why it's the greatest offensive season ever. Pure math dominance."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Follow for more stats that prove what your eyes see. Link in bio for all-time PVR leaders.\n\n[End screen: \"CURRY '16 = BROKEN 🎯\"]"
        },
        'sounds': [
            "Epic sports moment audio",
            "Triumphant victory music",
            "Celebration crowd noise"
        ],
        'hashtags': "#NBA #Basketball #StephenCurry #Curry #Warriors #Analytics #73Wins #MVP #Splash #NBAStats"
    },
    
    'usage_vs_efficiency': {
        'title': "High usage vs high efficiency: Which matters more?",
        'topic': 'Usage vs Efficiency',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "LeBron or Curry? Westbrook or Jokić? The eternal debate.\n\n[On-screen: \"VOLUME VS EFFICIENCY ⚔️\"]\n\nHere's what the math actually says..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "TUSG% = Volume (how much you dominate the ball)\nPVR = Efficiency (how well you use each possession)\n\n[Show quadrant chart]\n\nTop right = High usage + High efficiency (MVP tier)\nTop left = High efficiency, low usage (role player/system player)\nBottom right = High usage, low efficiency (volume scorer)\nBottom left = You're getting traded.\n\nThe BEST players? Both high. Curry 2016: 36.9 TUSG + 40.3 PVR."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Compare:\n- Harden 2019: 45.7 TUSG, 18.6 PVR (elite volume, good efficiency)\n- Jokić 2022: 33.7 TUSG, 44.5 PVR (good volume, ELITE efficiency)\n\n[Show: Both won MVP - different paths]\n\nBoth won MVP. Math says: either path works if you're elite."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Want to plot your favorite player? Link in bio. Follow for daily NBA analytics.\n\n[End screen: \"BOTH MATTER ⚖️\"]"
        },
        'sounds': [
            "Debate-style music",
            "Analytical content beat",
            "Sports discussion audio"
        ],
        'hashtags': "#NBA #Basketball #Analytics #Stats #NBAStats #HoopsAnalytics #BasketballIQ #NBATikTok #Efficiency #Usage"
    },
    
    'mj_vs_lebron': {
        'title': "MJ vs LeBron: The metrics finally settle it",
        'topic': 'GOAT Debate - Analytics Edition',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "The GOAT debate: Michael Jordan vs LeBron James. Forget the eye test.\n\n[On-screen: \"LET THE MATH DECIDE 🐐\"]\n\nHere's what TUSG% and PVR actually say..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "MJ 1987-88: 40.13 TUSG%, 15.54 PVR (35 PPG in a fast-paced era)\nLeBron 2012-13: 31.03 TUSG%, 39.21 PVR (27 PPG, elite efficiency)\n\n[Show comparison graphic]\n\nMJ = Higher volume, dominated the ball more\nLeBron = Lower volume, INSANE efficiency, better playmaking\n\nDifferent eras, different styles. MJ's peak usage vs LeBron's peak efficiency."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Translation: MJ took over games with scoring. LeBron elevated everyone.\n\n[Show: MJ's 35 PPG vs LeBron's 27 PPG + 7.3 APG]\n\nBoth are top 15 all-time in their respective metrics. The math says: they're BOTH the GOAT."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Still think there's one answer? Link in bio for the full cross-era rankings. Follow for more debates settled by data.\n\n[End screen: \"BOTH GOATS 🐐🐐\"]"
        },
        'sounds': [
            "Epic GOAT debate audio",
            "Dramatic comparison music",
            "Sports argument audio"
        ],
        'hashtags': "#NBA #MichaelJordan #LeBronJames #GOAT #GOATDebate #Basketball #NBAHistory #Analytics #MJvsLeBron #NBALegends"
    },
    
    'game_prediction': {
        'title': "How I predict NBA games with 65%+ accuracy",
        'topic': 'Game Prediction System',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "I've been predicting NBA games at 65%+ accuracy. No gut feelings, no hot takes.\n\n[On-screen: \"PURE MATH WINS 🎯\"]\n\nHere's the exact system I use..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "Step 1: Calculate each team's average TUSG% (offensive control)\nStep 2: Calculate each team's PVR (efficiency)\nStep 3: Factor in pace adjustments\nStep 4: Compare vs Vegas spread\n\n[Show formula: Edge = 50 + (Home TUSG - Away TUSG) + (Home PVR - Away PVR) × 0.5]\n\nWhen my model shows 65%+ edge AND disagrees with Vegas? That's a pick."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Example: Team A has 42 TUSG + 25 PVR. Team B has 38 TUSG + 18 PVR.\n\n[Show calculation: Edge = 50 + 4 + 3.5 = 57.5%]\n\nVegas has it even? My model says Team A wins 65% of the time. That's value."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Want today's picks? Link in bio for live predictions. Follow for the system that beats Vegas.\n\n[End screen: \"MATH > FEELINGS 📊\"]"
        },
        'sounds': [
            "Money/betting audio",
            "Analytical explanation music",
            "Sports betting content sound"
        ],
        'hashtags': "#NBA #NBABetting #SportsBetting #Analytics #NBAStats #Gambling #BettingTips #Basketball #DataScience #Vegas"
    },
    
    'era_adjusted': {
        'title': "Why comparing Wilt to Giannis is actually fair now",
        'topic': 'Era-Adjusted Metrics',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "\"You can't compare players from different eras!\" \n\n[On-screen: \"YES YOU CAN 🔥\"]\n\nWrong. TUSG% makes it possible. Here's how..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "1962: Teams averaged 126 possessions per game (Wilt's era)\n2020: Teams averaged 99.5 possessions per game (Giannis' era)\n\n[Show pace comparison chart]\n\nTUSG% adjusts for this. It asks: 'If both played at the SAME pace, who dominated more?'\n\nWilt 1962: 44.73 TUSG% (50 PPG adjusted for pace)\nGiannis 2020: 43.51 TUSG% (29.5 PPG adjusted for pace)\n\nNow it's fair. Same math, different eras."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "The result? Wilt edges Giannis in usage, but it's CLOSE.\n\n[Show: #3 Wilt vs #4 Giannis all-time]\n\nWithout pace adjustment? Not even comparable. With TUSG%? Legitimate debate."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Want to see how your favorite legend ranks? Link in bio for cross-era leaderboards. Follow for fair comparisons.\n\n[End screen: \"FAIR MATH = FAIR DEBATE ⚖️\"]"
        },
        'sounds': [
            "Educational explainer audio",
            "History/nostalgia music",
            "Analytical sports content beat"
        ],
        'hashtags': "#NBA #NBAHistory #Basketball #Wilt #Giannis #Analytics #CrossEra #Vintage #NBAStats #BasketballHistory"
    },
    
    'hidden_gems': {
        'title': "This metric finds All-Stars BEFORE they blow up",
        'topic': 'Finding Hidden Gems with Analytics',
        'hook': {
            'timestamp': '0:00-0:15',
            'text': "What if you could spot the next All-Star before anyone else?\n\n[On-screen: \"FIND STARS EARLY 💎\"]\n\nThis is how I do it with PVR..."
        },
        'explanation': {
            'timestamp': '0:15-0:40',
            'text': "Look for: High PVR (30+) + Low TUSG% (<25%) = Hidden gem\n\nWhy? They're EFFICIENT but underused.\n\n[Show quadrant: High PVR, Low Usage = Breakout Candidate]\n\nThese players produce at elite levels WITHOUT the ball. Give them more usage? They explode.\n\nExamples: Jokić before his MVP, Jimmy Butler pre-Chicago, Kawhi pre-Spurs Finals."
        },
        'example': {
            'timestamp': '0:40-0:50',
            'text': "Current example: Player with 32 PVR, 22 TUSG on limited minutes.\n\n[Show: League average = 15 PVR, 20 TUSG]\n\nThey're doing MORE with LESS. That's your next breakout star."
        },
        'cta': {
            'timestamp': '0:50-0:60',
            'text': "Want this season's hidden gems list? Link in bio. Follow to spot stars before the hype.\n\n[End screen: \"ANALYTICS SEE THE FUTURE 🔮\"]"
        },
        'sounds': [
            "Discovery/revelation audio",
            "Inspirational sports music",
            "Underdog story sound"
        ],
        'hashtags': "#NBA #Fantasy #NBAFantasy #HiddenGems #Analytics #Sleepers #BreakoutPlayers #Basketball #DraftKings #FanDuel"
    }
}

TRENDING_SOUNDS = [
    "original sound (use trending audio from FYP)",
    "Storytelling beat - medium tempo",
    "Upbeat sports commentary music",
    "Dramatic reveal audio",
    "Suspenseful music for analytics",
    "Epic sports highlight music",
    "Energetic explainer content beat",
    "Educational TikTok trending audio"
]


def generate_script(topic_key: str) -> Dict:
    """Generate a TikTok script for the given topic"""
    if topic_key not in SCRIPT_TEMPLATES:
        return {'error': f'Topic "{topic_key}" not found'}
    
    template = SCRIPT_TEMPLATES[topic_key]
    
    script = {
        'title': template['title'],
        'topic': template['topic'],
        'generated_at': datetime.now().isoformat(),
        'total_duration': '60 seconds',
        'sections': {
            'hook': {
                'timestamp': template['hook']['timestamp'],
                'duration': '15 seconds',
                'text': template['hook']['text']
            },
            'explanation': {
                'timestamp': template['explanation']['timestamp'],
                'duration': '25 seconds',
                'text': template['explanation']['text']
            },
            'example': {
                'timestamp': template['example']['timestamp'],
                'duration': '10 seconds',
                'text': template['example']['text']
            },
            'cta': {
                'timestamp': template['cta']['timestamp'],
                'duration': '10 seconds',
                'text': template['cta']['text']
            }
        },
        'recommended_sounds': template['sounds'],
        'trending_sounds': TRENDING_SOUNDS,
        'hashtags': template['hashtags'],
        'tips': [
            "Use text overlays for key stats and formulas",
            "Show graphics/charts during explanation section",
            "Keep energy high - fast cuts, dynamic visuals",
            "Use captions for accessibility",
            "Test different hooks for best performance"
        ]
    }
    
    return script


def save_script(topic_key: str, script: Dict) -> str:
    """Save generated script to file"""
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{topic_key}_{timestamp}.json"
    filepath = os.path.join(SCRIPTS_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(script, f, indent=2)
    
    return filepath


def generate_all_example_scripts():
    """Generate all example scripts and save to directory"""
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    generated_files = []
    
    for topic_key in SCRIPT_TEMPLATES.keys():
        script = generate_script(topic_key)
        filepath = save_script(topic_key, script)
        generated_files.append(filepath)
        print(f"✅ Generated: {filepath}")
    
    return generated_files


def get_available_topics() -> List[Dict]:
    """Get list of available script topics"""
    topics = []
    for key, template in SCRIPT_TEMPLATES.items():
        topics.append({
            'key': key,
            'title': template['title'],
            'topic': template['topic']
        })
    return topics


def format_script_for_display(script: Dict) -> str:
    """Format script as readable text for copying"""
    if 'error' in script:
        return script['error']
    
    output = f"🎬 {script['title']}\n"
    output += f"📊 {script['topic']}\n"
    output += f"⏱️ Total Duration: {script['total_duration']}\n"
    output += "=" * 60 + "\n\n"
    
    sections = script['sections']
    
    output += f"🎣 HOOK ({sections['hook']['timestamp']})\n"
    output += f"{sections['hook']['text']}\n\n"
    
    output += f"📚 EXPLANATION ({sections['explanation']['timestamp']})\n"
    output += f"{sections['explanation']['text']}\n\n"
    
    output += f"💡 EXAMPLE ({sections['example']['timestamp']})\n"
    output += f"{sections['example']['text']}\n\n"
    
    output += f"📢 CALL TO ACTION ({sections['cta']['timestamp']})\n"
    output += f"{sections['cta']['text']}\n\n"
    
    output += "=" * 60 + "\n"
    output += "🎵 RECOMMENDED SOUNDS:\n"
    for sound in script['recommended_sounds']:
        output += f"  • {sound}\n"
    
    output += "\n#️⃣ HASHTAGS:\n"
    output += f"  {script['hashtags']}\n"
    
    output += "\n💡 PRODUCTION TIPS:\n"
    for tip in script['tips']:
        output += f"  • {tip}\n"
    
    return output


if __name__ == '__main__':
    print("🚀 TikTok Script Generator - Taylor Vector Terminal")
    print("=" * 70)
    print("\n📝 Generating example scripts for all topics...\n")
    
    files = generate_all_example_scripts()
    
    print(f"\n✅ Generated {len(files)} scripts!")
    print(f"📁 Saved to: {SCRIPTS_DIR}/")
    print("\n🎬 Available Topics:")
    
    topics = get_available_topics()
    for topic in topics:
        print(f"  • {topic['topic']}: {topic['title']}")
    
    print("\n🎯 Use the web interface at /tiktok-scripts to generate custom scripts!")
