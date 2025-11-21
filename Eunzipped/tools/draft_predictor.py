"""
TAYLOR VECTOR TERMINAL - Draft Prospect PVR Predictor
Predicts NBA success for college prospects using TUSG% and PVR metrics
"""

import json

COLLEGE_PACE = 70.0

def calculate_college_tusg(stats):
    """
    Calculate TUSG% for college player
    TUSG% = (FGA + TOV + (FTA × 0.44)) / ((MP/48) × Pace) × 100
    """
    mp = stats.get('mpg', 0)
    fga = stats.get('fga', 0)
    tov = stats.get('tov', 0)
    fta = stats.get('fta', 0)
    
    if mp == 0 or COLLEGE_PACE == 0:
        return 0.0
    
    numerator = fga + tov + (fta * 0.44)
    denominator = (mp / 48) * COLLEGE_PACE
    
    if denominator == 0:
        return 0.0
    
    tusg = (numerator / denominator) * 100
    return round(tusg, 2)

def calculate_college_pvr(stats):
    """
    Calculate PVR for college player
    PVR = [(PTS + (AST × Multiplier)) / (FGA + TOV + (0.44 × FTA) + AST) - 1.00] × 100
    Multiplier: AST/TOV ≥ 1.8 → 2.3, else 1.8
    """
    pts = stats.get('ppg', 0)
    ast = stats.get('apg', 0)
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

def apply_pro_adjustments(college_stats):
    """
    Apply pro adjustments to college stats:
    - Usage typically drops 15% (college stars → NBA role players)
    - Efficiency typically improves 8% (better coaching, spacing)
    """
    adjusted_stats = college_stats.copy()
    
    adjusted_stats['fga'] = college_stats['fga'] * 0.85
    adjusted_stats['fta'] = college_stats['fta'] * 0.85
    adjusted_stats['tov'] = college_stats['tov'] * 0.85
    
    adjusted_stats['ppg'] = college_stats['ppg'] * 0.85 * 1.08
    
    return adjusted_stats

def calculate_pro_projections(college_stats):
    """
    Calculate projected NBA TUSG% and PVR
    """
    college_tusg = calculate_college_tusg(college_stats)
    college_pvr = calculate_college_pvr(college_stats)
    
    adjusted_stats = apply_pro_adjustments(college_stats)
    
    nba_pace = 99.5
    mp = adjusted_stats.get('mpg', 0)
    fga = adjusted_stats.get('fga', 0)
    tov = adjusted_stats.get('tov', 0)
    fta = adjusted_stats.get('fta', 0)
    
    if mp == 0:
        projected_tusg = 0.0
    else:
        numerator = fga + tov + (fta * 0.44)
        denominator = (mp / 48) * nba_pace
        projected_tusg = (numerator / denominator) * 100 if denominator > 0 else 0.0
    
    projected_pvr = calculate_college_pvr(adjusted_stats)
    
    return {
        'college_tusg': college_tusg,
        'college_pvr': college_pvr,
        'projected_tusg': round(projected_tusg, 2),
        'projected_pvr': round(projected_pvr, 2)
    }

def calculate_bust_steal_probability(draft_position, projected_tusg, projected_pvr, college_stats):
    """
    Calculate bust/steal probability based on draft position vs projected metrics
    
    Draft Position Expectations:
    - Top 5: TUSG 35%+, PVR 20%+
    - 6-15: TUSG 30%+, PVR 15%+
    - 16-30: TUSG 25%+, PVR 10%+
    - 31-60: TUSG 20%+, PVR 5%+
    
    Risk Factors:
    - AST/TOV < 1.0: High bust risk (+15% bust risk)
    - College PVR > 40: High steal potential (+20% steal potential)
    """
    if draft_position <= 5:
        expected_tusg = 35.0
        expected_pvr = 20.0
    elif draft_position <= 15:
        expected_tusg = 30.0
        expected_pvr = 15.0
    elif draft_position <= 30:
        expected_tusg = 25.0
        expected_pvr = 10.0
    else:
        expected_tusg = 20.0
        expected_pvr = 5.0
    
    tusg_diff = projected_tusg - expected_tusg
    pvr_diff = projected_pvr - expected_pvr
    
    bust_risk = 50.0
    if tusg_diff < -5 or pvr_diff < -5:
        bust_risk = 70.0
    elif tusg_diff < 0 or pvr_diff < 0:
        bust_risk = 60.0
    elif tusg_diff > 5 and pvr_diff > 5:
        bust_risk = 20.0
    elif tusg_diff > 0 and pvr_diff > 0:
        bust_risk = 35.0
    
    steal_potential = 50.0
    if tusg_diff > 10 and pvr_diff > 10:
        steal_potential = 85.0
    elif tusg_diff > 5 and pvr_diff > 5:
        steal_potential = 70.0
    elif tusg_diff > 0 and pvr_diff > 0:
        steal_potential = 60.0
    elif tusg_diff < -5 or pvr_diff < -5:
        steal_potential = 20.0
    
    ast = college_stats.get('apg', 0)
    tov = college_stats.get('tov', 0)
    ast_tov_ratio = ast / tov if tov > 0 else (ast if ast > 0 else 0)
    
    if ast_tov_ratio < 1.0:
        bust_risk = min(bust_risk + 15.0, 95.0)
    
    college_pvr = calculate_college_pvr(college_stats)
    if college_pvr > 40:
        steal_potential = min(steal_potential + 20.0, 95.0)
    
    risk_factors = []
    if ast_tov_ratio < 1.0:
        risk_factors.append('Poor AST/TOV ratio')
    if college_pvr > 40:
        risk_factors.append('Elite college PVR')
    
    return {
        'bust_risk': round(bust_risk, 1),
        'steal_potential': round(steal_potential, 1),
        'risk_factors': risk_factors,
        'ast_tov_ratio': round(ast_tov_ratio, 2)
    }

def predict_prospect(college_stats, draft_position, competition_level='P5'):
    """
    Full prediction pipeline for a draft prospect
    
    Args:
        college_stats: Dict with mpg, ppg, apg, tov, fga, fta
        draft_position: 1-60
        competition_level: 'P5', 'Mid-Major', 'International', 'G-League'
    """
    projections = calculate_pro_projections(college_stats)
    probabilities = calculate_bust_steal_probability(
        draft_position, 
        projections['projected_tusg'],
        projections['projected_pvr'],
        college_stats
    )
    
    return {
        **projections,
        **probabilities,
        'draft_position': draft_position,
        'competition_level': competition_level
    }

HISTORICAL_EXAMPLES = [
    {
        'name': 'Trae Young',
        'draft_year': 2018,
        'draft_position': 5,
        'college': 'Oklahoma',
        'college_stats': {
            'mpg': 35.4,
            'ppg': 27.4,
            'apg': 8.7,
            'tov': 5.2,
            'fga': 21.7,
            'fta': 8.7
        },
        'nba_outcome': {
            'career_avg_tusg': 42.8,
            'career_avg_pvr': 28.5,
            'assessment': 'STEAL - Elite playmaker, exceeded expectations'
        }
    },
    {
        'name': 'Luka Doncic',
        'draft_year': 2018,
        'draft_position': 3,
        'college': 'Real Madrid (EuroLeague)',
        'college_stats': {
            'mpg': 25.4,
            'ppg': 16.0,
            'apg': 4.8,
            'tov': 2.6,
            'fga': 10.5,
            'fta': 5.8
        },
        'nba_outcome': {
            'career_avg_tusg': 38.2,
            'career_avg_pvr': 35.4,
            'assessment': 'SUPERSTAR - Franchise player, MVP-level'
        }
    },
    {
        'name': 'Zion Williamson',
        'draft_year': 2019,
        'draft_position': 1,
        'college': 'Duke',
        'college_stats': {
            'mpg': 30.0,
            'ppg': 22.6,
            'apg': 2.1,
            'tov': 2.1,
            'fga': 13.3,
            'fta': 7.5
        },
        'nba_outcome': {
            'career_avg_tusg': 35.6,
            'career_avg_pvr': 32.8,
            'assessment': 'SOLID - Elite scorer, injury concerns affected ceiling'
        }
    },
    {
        'name': 'Ja Morant',
        'draft_year': 2019,
        'draft_position': 2,
        'college': 'Murray State',
        'college_stats': {
            'mpg': 33.8,
            'ppg': 24.5,
            'apg': 10.0,
            'tov': 3.5,
            'fga': 16.4,
            'fta': 8.0
        },
        'nba_outcome': {
            'career_avg_tusg': 40.5,
            'career_avg_pvr': 30.2,
            'assessment': 'STEAL - Dynamic playmaker, All-NBA caliber'
        }
    },
    {
        'name': 'Anthony Edwards',
        'draft_year': 2020,
        'draft_position': 1,
        'college': 'Georgia',
        'college_stats': {
            'mpg': 33.0,
            'ppg': 19.1,
            'apg': 2.8,
            'tov': 2.6,
            'fga': 15.5,
            'fta': 5.2
        },
        'nba_outcome': {
            'career_avg_tusg': 37.2,
            'career_avg_pvr': 22.8,
            'assessment': 'SOLID - Two-way star,met expectations'
        }
    },
    {
        'name': 'LaMelo Ball',
        'draft_year': 2020,
        'draft_position': 3,
        'college': 'Illawarra Hawks (Australia)',
        'college_stats': {
            'mpg': 31.2,
            'ppg': 17.0,
            'apg': 7.5,
            'tov': 3.8,
            'fga': 13.0,
            'fta': 4.2
        },
        'nba_outcome': {
            'career_avg_tusg': 38.8,
            'career_avg_pvr': 28.9,
            'assessment': 'STEAL - Elite passer, All-Star level'
        }
    },
    {
        'name': 'Cade Cunningham',
        'draft_year': 2021,
        'draft_position': 1,
        'college': 'Oklahoma State',
        'college_stats': {
            'mpg': 35.4,
            'ppg': 20.1,
            'apg': 6.2,
            'tov': 3.5,
            'fga': 15.6,
            'fta': 5.8
        },
        'nba_outcome': {
            'career_avg_tusg': 36.4,
            'career_avg_pvr': 24.6,
            'assessment': 'SOLID - Complete player, steady development'
        }
    },
    {
        'name': 'Paolo Banchero',
        'draft_year': 2022,
        'draft_position': 1,
        'college': 'Duke',
        'college_stats': {
            'mpg': 33.3,
            'ppg': 17.2,
            'apg': 3.2,
            'tov': 2.5,
            'fga': 12.8,
            'fta': 5.8
        },
        'nba_outcome': {
            'career_avg_tusg': 34.8,
            'career_avg_pvr': 20.5,
            'assessment': 'SOLID - ROY winner, versatile forward'
        }
    },
    {
        'name': 'Victor Wembanyama',
        'draft_year': 2023,
        'draft_position': 1,
        'college': 'Metropolitans 92 (France)',
        'college_stats': {
            'mpg': 27.5,
            'ppg': 21.6,
            'apg': 2.4,
            'tov': 2.8,
            'fga': 14.2,
            'fta': 6.5
        },
        'nba_outcome': {
            'career_avg_tusg': 36.2,
            'career_avg_pvr': 28.4,
            'assessment': 'SUPERSTAR - Generational talent, immediate impact'
        }
    },
    {
        'name': 'Markelle Fultz',
        'draft_year': 2017,
        'draft_position': 1,
        'college': 'Washington',
        'college_stats': {
            'mpg': 35.7,
            'ppg': 23.2,
            'apg': 5.7,
            'tov': 3.6,
            'fga': 17.3,
            'fta': 6.2
        },
        'nba_outcome': {
            'career_avg_tusg': 28.4,
            'career_avg_pvr': 12.6,
            'assessment': 'BUST - Injury derailed career, never reached potential'
        }
    },
    {
        'name': 'Devin Booker',
        'draft_year': 2015,
        'draft_position': 13,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 21.5,
            'ppg': 10.0,
            'apg': 1.1,
            'tov': 1.0,
            'fga': 7.3,
            'fta': 2.2
        },
        'nba_outcome': {
            'career_avg_tusg': 40.2,
            'career_avg_pvr': 24.8,
            'assessment': 'STEAL - Elite scorer, All-NBA level'
        }
    },
    {
        'name': 'Jayson Tatum',
        'draft_year': 2017,
        'draft_position': 3,
        'college': 'Duke',
        'college_stats': {
            'mpg': 33.2,
            'ppg': 16.8,
            'apg': 2.1,
            'tov': 1.8,
            'fga': 11.6,
            'fta': 4.5
        },
        'nba_outcome': {
            'career_avg_tusg': 36.8,
            'career_avg_pvr': 22.4,
            'assessment': 'SOLID - MVP candidate, franchise cornerstone'
        }
    },
    {
        'name': 'Donovan Mitchell',
        'draft_year': 2017,
        'draft_position': 13,
        'college': 'Louisville',
        'college_stats': {
            'mpg': 35.1,
            'ppg': 15.6,
            'apg': 2.7,
            'tov': 2.1,
            'fga': 11.5,
            'fta': 3.8
        },
        'nba_outcome': {
            'career_avg_tusg': 39.8,
            'career_avg_pvr': 20.6,
            'assessment': 'STEAL - All-Star, elite scorer'
        }
    },
    {
        'name': 'Karl-Anthony Towns',
        'draft_year': 2015,
        'draft_position': 1,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 21.1,
            'ppg': 10.3,
            'apg': 1.1,
            'tov': 1.4,
            'fga': 7.2,
            'fta': 3.1
        },
        'nba_outcome': {
            'career_avg_tusg': 33.5,
            'career_avg_pvr': 26.8,
            'assessment': 'SOLID - Multiple All-Star, elite big man'
        }
    },
    {
        'name': 'D\'Angelo Russell',
        'draft_year': 2015,
        'draft_position': 2,
        'college': 'Ohio State',
        'college_stats': {
            'mpg': 35.4,
            'ppg': 19.3,
            'apg': 5.0,
            'tov': 2.9,
            'fga': 14.8,
            'fta': 4.9
        },
        'nba_outcome': {
            'career_avg_tusg': 37.2,
            'career_avg_pvr': 18.4,
            'assessment': 'SOLID - All-Star, solid starter'
        }
    },
    {
        'name': 'Jaren Jackson Jr.',
        'draft_year': 2018,
        'draft_position': 4,
        'college': 'Michigan State',
        'college_stats': {
            'mpg': 21.8,
            'ppg': 10.9,
            'apg': 1.0,
            'tov': 1.5,
            'fga': 7.6,
            'fta': 3.3
        },
        'nba_outcome': {
            'career_avg_tusg': 30.2,
            'career_avg_pvr': 18.6,
            'assessment': 'SOLID - DPOY, elite two-way player'
        }
    },
    {
        'name': 'Shai Gilgeous-Alexander',
        'draft_year': 2018,
        'draft_position': 11,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 27.5,
            'ppg': 14.4,
            'apg': 4.1,
            'tov': 2.2,
            'fga': 10.2,
            'fta': 4.5
        },
        'nba_outcome': {
            'career_avg_tusg': 39.4,
            'career_avg_pvr': 32.8,
            'assessment': 'STEAL - MVP candidate, elite two-way guard'
        }
    },
    {
        'name': 'Bam Adebayo',
        'draft_year': 2017,
        'draft_position': 14,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 30.0,
            'ppg': 13.0,
            'apg': 0.8,
            'tov': 1.5,
            'fga': 8.5,
            'fta': 4.2
        },
        'nba_outcome': {
            'career_avg_tusg': 26.8,
            'career_avg_pvr': 22.4,
            'assessment': 'STEAL - Multiple All-Star, elite defender'
        }
    },
    {
        'name': 'De\'Aaron Fox',
        'draft_year': 2017,
        'draft_position': 5,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 30.1,
            'ppg': 16.7,
            'apg': 4.6,
            'tov': 3.0,
            'fga': 12.8,
            'fta': 5.5
        },
        'nba_outcome': {
            'career_avg_tusg': 40.6,
            'career_avg_pvr': 26.2,
            'assessment': 'SOLID - All-NBA, elite speed and playmaking'
        }
    },
    {
        'name': 'Deandre Ayton',
        'draft_year': 2018,
        'draft_position': 1,
        'college': 'Arizona',
        'college_stats': {
            'mpg': 33.6,
            'ppg': 20.1,
            'apg': 1.6,
            'tov': 1.9,
            'fga': 13.8,
            'fta': 5.8
        },
        'nba_outcome': {
            'career_avg_tusg': 28.4,
            'career_avg_pvr': 22.6,
            'assessment': 'SOLID - Solid starter, Finals contributor'
        }
    },
    {
        'name': 'Collin Sexton',
        'draft_year': 2018,
        'draft_position': 8,
        'college': 'Alabama',
        'college_stats': {
            'mpg': 32.8,
            'ppg': 19.2,
            'apg': 3.6,
            'tov': 2.8,
            'fga': 15.5,
            'fta': 6.1
        },
        'nba_outcome': {
            'career_avg_tusg': 38.2,
            'career_avg_pvr': 15.8,
            'assessment': 'SOLID - Quality scorer, solid rotation player'
        }
    },
    {
        'name': 'Brandon Ingram',
        'draft_year': 2016,
        'draft_position': 2,
        'college': 'Duke',
        'college_stats': {
            'mpg': 34.1,
            'ppg': 17.3,
            'apg': 1.9,
            'tov': 1.6,
            'fga': 13.4,
            'fta': 4.8
        },
        'nba_outcome': {
            'career_avg_tusg': 35.4,
            'career_avg_pvr': 20.8,
            'assessment': 'SOLID - All-Star, MIP winner'
        }
    },
    {
        'name': 'Jaylen Brown',
        'draft_year': 2016,
        'draft_position': 3,
        'college': 'California',
        'college_stats': {
            'mpg': 30.4,
            'ppg': 14.6,
            'apg': 1.2,
            'tov': 1.4,
            'fga': 10.8,
            'fta': 4.0
        },
        'nba_outcome': {
            'career_avg_tusg': 34.2,
            'career_avg_pvr': 21.6,
            'assessment': 'SOLID - All-NBA, Finals MVP'
        }
    },
    {
        'name': 'Damian Lillard',
        'draft_year': 2012,
        'draft_position': 6,
        'college': 'Weber State',
        'college_stats': {
            'mpg': 35.6,
            'ppg': 24.5,
            'apg': 5.0,
            'tov': 2.6,
            'fga': 18.3,
            'fta': 6.8
        },
        'nba_outcome': {
            'career_avg_tusg': 42.8,
            'career_avg_pvr': 28.4,
            'assessment': 'STEAL - Multiple All-NBA, elite clutch scorer'
        }
    },
    {
        'name': 'Bradley Beal',
        'draft_year': 2012,
        'draft_position': 3,
        'college': 'Florida',
        'college_stats': {
            'mpg': 31.2,
            'ppg': 14.8,
            'apg': 2.7,
            'tov': 1.8,
            'fga': 11.5,
            'fta': 3.5
        },
        'nba_outcome': {
            'career_avg_tusg': 38.6,
            'career_avg_pvr': 22.2,
            'assessment': 'SOLID - Multiple All-Star, elite scorer'
        }
    },
    {
        'name': 'Kyrie Irving',
        'draft_year': 2011,
        'draft_position': 1,
        'college': 'Duke',
        'college_stats': {
            'mpg': 30.5,
            'ppg': 17.5,
            'apg': 5.4,
            'tov': 3.2,
            'fga': 13.5,
            'fta': 5.1
        },
        'nba_outcome': {
            'career_avg_tusg': 39.8,
            'career_avg_pvr': 30.2,
            'assessment': 'SOLID - Champion, elite ball-handler'
        }
    },
    {
        'name': 'Kawhi Leonard',
        'draft_year': 2011,
        'draft_position': 15,
        'college': 'San Diego State',
        'college_stats': {
            'mpg': 33.0,
            'ppg': 15.5,
            'apg': 2.1,
            'tov': 1.6,
            'fga': 10.8,
            'fta': 4.8
        },
        'nba_outcome': {
            'career_avg_tusg': 34.2,
            'career_avg_pvr': 26.4,
            'assessment': 'STEAL - 2x Finals MVP, elite two-way player'
        }
    },
    {
        'name': 'Jimmy Butler',
        'draft_year': 2011,
        'draft_position': 30,
        'college': 'Marquette',
        'college_stats': {
            'mpg': 30.2,
            'ppg': 15.7,
            'apg': 2.3,
            'tov': 1.4,
            'fga': 10.5,
            'fta': 5.2
        },
        'nba_outcome': {
            'career_avg_tusg': 32.8,
            'career_avg_pvr': 24.6,
            'assessment': 'STEAL - Multiple All-NBA, elite two-way wing'
        }
    },
    {
        'name': 'Paul George',
        'draft_year': 2010,
        'draft_position': 10,
        'college': 'Fresno State',
        'college_stats': {
            'mpg': 32.8,
            'ppg': 16.8,
            'apg': 2.2,
            'tov': 2.0,
            'fga': 12.5,
            'fta': 4.8
        },
        'nba_outcome': {
            'career_avg_tusg': 36.4,
            'career_avg_pvr': 22.8,
            'assessment': 'STEAL - Multiple All-NBA, elite two-way wing'
        }
    },
    {
        'name': 'John Wall',
        'draft_year': 2010,
        'draft_position': 1,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 35.7,
            'ppg': 16.6,
            'apg': 6.5,
            'tov': 3.8,
            'fga': 13.2,
            'fta': 5.1
        },
        'nba_outcome': {
            'career_avg_tusg': 38.2,
            'career_avg_pvr': 24.4,
            'assessment': 'SOLID - Multiple All-Star, elite athleticism'
        }
    },
    {
        'name': 'Joel Embiid',
        'draft_year': 2014,
        'draft_position': 3,
        'college': 'Kansas',
        'college_stats': {
            'mpg': 23.1,
            'ppg': 11.2,
            'apg': 1.4,
            'tov': 2.5,
            'fga': 7.3,
            'fta': 4.1
        },
        'nba_outcome': {
            'career_avg_tusg': 38.6,
            'career_avg_pvr': 32.8,
            'assessment': 'STEAL - MVP, elite two-way center'
        }
    },
    {
        'name': 'Nikola Jokic',
        'draft_year': 2014,
        'draft_position': 41,
        'college': 'Mega Basket (Serbia)',
        'college_stats': {
            'mpg': 22.0,
            'ppg': 11.4,
            'apg': 2.8,
            'tov': 1.8,
            'fga': 7.5,
            'fta': 3.2
        },
        'nba_outcome': {
            'career_avg_tusg': 32.8,
            'career_avg_pvr': 42.6,
            'assessment': 'STEAL - 3x MVP, greatest passing big ever'
        }
    },
    {
        'name': 'Andrew Wiggins',
        'draft_year': 2014,
        'draft_position': 1,
        'college': 'Kansas',
        'college_stats': {
            'mpg': 35.0,
            'ppg': 17.1,
            'apg': 1.5,
            'tov': 1.4,
            'fga': 13.4,
            'fta': 4.4
        },
        'nba_outcome': {
            'career_avg_tusg': 32.4,
            'career_avg_pvr': 16.8,
            'assessment': 'SOLID - Champion, solid two-way wing'
        }
    },
    {
        'name': 'Julius Randle',
        'draft_year': 2014,
        'draft_position': 7,
        'college': 'Kentucky',
        'college_stats': {
            'mpg': 29.4,
            'ppg': 15.0,
            'apg': 1.4,
            'tov': 2.1,
            'fga': 10.6,
            'fta': 4.8
        },
        'nba_outcome': {
            'career_avg_tusg': 33.6,
            'career_avg_pvr': 20.4,
            'assessment': 'SOLID - All-NBA, versatile forward'
        }
    }
]

DRAFT_2025_PROSPECTS = [
    {
        'name': 'Cooper Flagg',
        'projected_position': 1,
        'college': 'Duke',
        'college_stats': {
            'mpg': 32.0,
            'ppg': 18.5,
            'apg': 4.2,
            'tov': 2.1,
            'fga': 12.8,
            'fta': 6.2
        },
        'competition_level': 'P5',
        'scouting_notes': 'Elite two-way wing with high IQ, defensive versatility'
    },
    {
        'name': 'Ace Bailey',
        'projected_position': 2,
        'college': 'Rutgers',
        'college_stats': {
            'mpg': 30.5,
            'ppg': 20.8,
            'apg': 2.8,
            'tov': 2.5,
            'fga': 15.2,
            'fta': 5.4
        },
        'competition_level': 'P5',
        'scouting_notes': 'Elite scorer, explosive athlete, needs playmaking development'
    },
    {
        'name': 'Dylan Harper',
        'projected_position': 3,
        'college': 'Rutgers',
        'college_stats': {
            'mpg': 33.0,
            'ppg': 22.4,
            'apg': 5.8,
            'tov': 3.2,
            'fga': 16.5,
            'fta': 7.1
        },
        'competition_level': 'P5',
        'scouting_notes': 'High-usage guard, advanced playmaking, elite scoring versatility'
    },
    {
        'name': 'Nolan Traore',
        'projected_position': 4,
        'college': 'Saint-Quentin (France)',
        'college_stats': {
            'mpg': 28.0,
            'ppg': 16.2,
            'apg': 6.5,
            'tov': 2.8,
            'fga': 11.5,
            'fta': 4.2
        },
        'competition_level': 'International',
        'scouting_notes': 'Elite passer, high IQ, needs to improve shooting consistency'
    },
    {
        'name': 'VJ Edgecombe',
        'projected_position': 6,
        'college': 'Baylor',
        'college_stats': {
            'mpg': 28.5,
            'ppg': 15.8,
            'apg': 3.2,
            'tov': 2.0,
            'fga': 11.2,
            'fta': 5.8
        },
        'competition_level': 'P5',
        'scouting_notes': 'Elite defender, explosive athlete, developing offensive game'
    },
    {
        'name': 'Egor Demin',
        'projected_position': 7,
        'college': 'BYU',
        'college_stats': {
            'mpg': 30.0,
            'ppg': 17.5,
            'apg': 5.2,
            'tov': 2.5,
            'fga': 13.0,
            'fta': 4.5
        },
        'competition_level': 'P5',
        'scouting_notes': 'Tall playmaker, versatile skillset, needs strength development'
    },
    {
        'name': 'Kasparas Jakucionis',
        'projected_position': 8,
        'college': 'Illinois',
        'college_stats': {
            'mpg': 29.0,
            'ppg': 16.2,
            'apg': 5.8,
            'tov': 2.4,
            'fga': 12.5,
            'fta': 4.8
        },
        'competition_level': 'P5',
        'scouting_notes': 'Smart playmaker, excellent passer, improving athleticism'
    },
    {
        'name': 'Khaman Maluach',
        'projected_position': 9,
        'college': 'Duke',
        'college_stats': {
            'mpg': 24.0,
            'ppg': 12.5,
            'apg': 1.0,
            'tov': 1.8,
            'fga': 8.2,
            'fta': 4.5
        },
        'competition_level': 'P5',
        'scouting_notes': 'Elite rim protector, raw offensively, high upside'
    },
    {
        'name': 'Tre Johnson',
        'projected_position': 10,
        'college': 'Texas',
        'college_stats': {
            'mpg': 31.0,
            'ppg': 19.5,
            'apg': 3.2,
            'tov': 2.2,
            'fga': 14.8,
            'fta': 6.2
        },
        'competition_level': 'P5',
        'scouting_notes': 'Elite scorer, explosive athlete, needs playmaking development'
    }
]

def generate_historical_predictions():
    """
    Generate predictions for historical prospects and compare to actual outcomes
    """
    results = []
    
    for example in HISTORICAL_EXAMPLES:
        comp_level = 'International' if any(x in example['college'] for x in ['Real Madrid', 'Serbia', 'France', 'Australia']) else 'P5'
        
        prediction = predict_prospect(
            example['college_stats'],
            example['draft_position'],
            comp_level
        )
        
        results.append({
            'name': example['name'],
            'draft_year': example['draft_year'],
            'draft_position': example['draft_position'],
            'college': example['college'],
            'prediction': prediction,
            'actual': example['nba_outcome']
        })
    
    return results

def generate_2025_projections():
    """
    Generate projections for 2025 draft prospects
    """
    projections = []
    
    for prospect in DRAFT_2025_PROSPECTS:
        prediction = predict_prospect(
            prospect['college_stats'],
            prospect['projected_position'],
            prospect['competition_level']
        )
        
        projections.append({
            'name': prospect['name'],
            'projected_position': prospect['projected_position'],
            'college': prospect['college'],
            'competition_level': prospect['competition_level'],
            'prediction': prediction,
            'scouting_notes': prospect['scouting_notes']
        })
    
    return projections

def save_historical_predictions(filename='draft_predictor_examples.json'):
    """
    Save historical predictions to JSON file
    """
    predictions = generate_historical_predictions()
    
    with open(filename, 'w') as f:
        json.dump(predictions, f, indent=2)
    
    print(f"✅ Saved {len(predictions)} historical predictions to {filename}")
    return predictions

def save_2025_projections(filename='draft_predictor_2025.json'):
    """
    Save 2025 draft projections to JSON file
    """
    projections = generate_2025_projections()
    
    with open(filename, 'w') as f:
        json.dump(projections, f, indent=2)
    
    print(f"✅ Saved {len(projections)} 2025 draft projections to {filename}")
    return projections

if __name__ == '__main__':
    print("\n" + "=" * 100)
    print("🏀 DRAFT PROSPECT PVR PREDICTOR - TAYLOR VECTOR TERMINAL")
    print("=" * 100)
    
    predictions = save_historical_predictions()
    
    print("\n📊 Historical Examples Analysis")
    print("=" * 100)
    
    for i, pred in enumerate(predictions[:10], 1):
        print(f"\n{i}. {pred['name']} ({pred['draft_year']}, Pick #{pred['draft_position']}) - {pred['college']}")
        print(f"   PREDICTION:")
        print(f"     College TUSG: {pred['prediction']['college_tusg']}% → Projected NBA: {pred['prediction']['projected_tusg']}%")
        print(f"     College PVR: {pred['prediction']['college_pvr']} → Projected NBA: {pred['prediction']['projected_pvr']}")
        print(f"     Bust Risk: {pred['prediction']['bust_risk']}% | Steal: {pred['prediction']['steal_potential']}%")
        if pred['prediction'].get('risk_factors'):
            print(f"     Risk Factors: {', '.join(pred['prediction']['risk_factors'])}")
        
        if 'actual' in pred:
            print(f"   ACTUAL: TUSG {pred['actual']['career_avg_tusg']}% | PVR {pred['actual']['career_avg_pvr']} | {pred['actual']['assessment']}")
    
    print(f"\n... and {len(predictions) - 10} more historical examples")
    
    print("\n" + "=" * 100)
    print("📊 Prediction Accuracy Summary:")
    
    correct_predictions = 0
    for pred in predictions:
        actual_assessment = pred['actual']['assessment']
        predicted_bust = pred['prediction']['bust_risk']
        predicted_steal = pred['prediction']['steal_potential']
        
        if 'BUST' in actual_assessment and predicted_bust > 60:
            correct_predictions += 1
        elif 'STEAL' in actual_assessment and predicted_steal > 60:
            correct_predictions += 1
        elif 'SOLID' in actual_assessment and 40 <= predicted_bust <= 60:
            correct_predictions += 1
        elif 'SUPERSTAR' in actual_assessment and predicted_steal > 65:
            correct_predictions += 1
    
    accuracy = (correct_predictions / len(predictions)) * 100
    print(f"Model correctly predicted {correct_predictions}/{len(predictions)} outcomes ({accuracy:.1f}%)")
    
    print("\n" + "=" * 100)
    print("🎓 2025 DRAFT CLASS PROJECTIONS")
    print("=" * 100)
    
    prospects_2025 = save_2025_projections()
    
    for i, prospect in enumerate(prospects_2025, 1):
        print(f"\n{i}. {prospect['name']} - Projected Pick #{prospect['projected_position']}")
        print(f"   School: {prospect['college']} ({prospect['competition_level']})")
        print(f"   Projected NBA TUSG: {prospect['prediction']['projected_tusg']}% | PVR: {prospect['prediction']['projected_pvr']}")
        print(f"   Bust Risk: {prospect['prediction']['bust_risk']}% | Steal Potential: {prospect['prediction']['steal_potential']}%")
        if prospect['prediction'].get('risk_factors'):
            print(f"   Risk Factors: {', '.join(prospect['prediction']['risk_factors'])}")
        print(f"   Scouting: {prospect['scouting_notes']}")
    
    print("\n" + "=" * 100)
    print("⚠️  DISCLAIMER: Projections based on historical patterns and statistical analysis.")
    print("    Not guaranteed predictions. Educational tool showing TUSG%/PVR translation.")
    print("=" * 100)
