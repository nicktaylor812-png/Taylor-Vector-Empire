"""
TAYLOR VECTOR TERMINAL - Injury Comeback Tracker
Track player metrics before/after major injuries
Educational tool showing resilience or decline
"""

import json
from datetime import datetime

INJURY_DATABASE = [
    {
        'player': 'Kevin Durant',
        'injury_type': 'Achilles Tear',
        'injury_date': '2019-06-10',
        'injury_season': '2018-19',
        'pre_injury': {
            'season': '2018-19',
            'tusg': 34.2,
            'pvr': 26.8,
            'ppg': 26.0,
            'apg': 5.9,
            'mpg': 34.6
        },
        'post_injury_1yr': {
            'season': '2020-21',
            'tusg': 31.5,
            'pvr': 24.1,
            'ppg': 26.9,
            'apg': 5.6,
            'mpg': 33.1,
            'games': 35
        },
        'post_injury_2yr': {
            'season': '2021-22',
            'tusg': 32.8,
            'pvr': 25.9,
            'ppg': 29.9,
            'apg': 6.4,
            'mpg': 37.2,
            'games': 55
        },
        'recovery_notes': 'Elite comeback, maintained 85%+ of pre-injury PVR by year 2'
    },
    {
        'player': 'Klay Thompson',
        'injury_type': 'ACL Tear',
        'injury_date': '2019-06-13',
        'injury_season': '2018-19',
        'pre_injury': {
            'season': '2018-19',
            'tusg': 33.1,
            'pvr': 18.4,
            'ppg': 21.5,
            'apg': 2.4,
            'mpg': 34.0
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2021-22',
            'tusg': 29.8,
            'pvr': 14.2,
            'ppg': 20.4,
            'apg': 2.8,
            'mpg': 29.4,
            'games': 32
        },
        'recovery_notes': 'Struggled initially (77% of pre-injury PVR), improving gradually'
    },
    {
        'player': 'Derrick Rose',
        'injury_type': 'ACL Tear',
        'injury_date': '2012-04-28',
        'injury_season': '2011-12',
        'pre_injury': {
            'season': '2011-12',
            'tusg': 38.5,
            'pvr': 21.7,
            'ppg': 21.8,
            'apg': 7.9,
            'mpg': 35.3
        },
        'post_injury_1yr': {
            'season': '2013-14',
            'tusg': 32.1,
            'pvr': 14.8,
            'ppg': 15.9,
            'apg': 4.3,
            'mpg': 31.8,
            'games': 10
        },
        'post_injury_2yr': {
            'season': '2014-15',
            'tusg': 30.4,
            'pvr': 13.2,
            'ppg': 17.7,
            'apg': 4.9,
            'mpg': 31.2,
            'games': 51
        },
        'recovery_notes': 'Significant decline, never regained MVP form (60% of pre-injury PVR)'
    },
    {
        'player': 'Paul George',
        'injury_type': 'Leg Fracture',
        'injury_date': '2014-08-01',
        'injury_season': '2013-14',
        'pre_injury': {
            'season': '2013-14',
            'tusg': 35.8,
            'pvr': 20.1,
            'ppg': 21.7,
            'apg': 3.5,
            'mpg': 36.2
        },
        'post_injury_1yr': {
            'season': '2015-16',
            'tusg': 33.9,
            'pvr': 19.4,
            'ppg': 23.1,
            'apg': 4.1,
            'mpg': 34.3,
            'games': 81
        },
        'post_injury_2yr': {
            'season': '2016-17',
            'tusg': 34.7,
            'pvr': 20.8,
            'ppg': 23.7,
            'apg': 3.3,
            'mpg': 33.9,
            'games': 75
        },
        'recovery_notes': 'Excellent recovery, returned to All-Star form (96%+ of pre-injury)'
    },
    {
        'player': 'Kobe Bryant',
        'injury_type': 'Achilles Tear',
        'injury_date': '2013-04-12',
        'injury_season': '2012-13',
        'pre_injury': {
            'season': '2012-13',
            'tusg': 41.2,
            'pvr': 15.3,
            'ppg': 27.3,
            'apg': 6.0,
            'mpg': 38.6
        },
        'post_injury_1yr': {
            'season': '2013-14',
            'tusg': 36.8,
            'pvr': 8.4,
            'ppg': 13.8,
            'apg': 6.3,
            'mpg': 29.5,
            'games': 6
        },
        'post_injury_2yr': {
            'season': '2014-15',
            'tusg': 34.1,
            'pvr': 9.8,
            'ppg': 22.3,
            'apg': 5.7,
            'mpg': 34.5,
            'games': 35
        },
        'recovery_notes': 'Never fully recovered at age 35+, PVR dropped to 64% of pre-injury'
    },
    {
        'player': 'John Wall',
        'injury_type': 'Achilles Tear',
        'injury_date': '2019-01-29',
        'injury_season': '2018-19',
        'pre_injury': {
            'season': '2016-17',
            'tusg': 37.4,
            'pvr': 22.8,
            'ppg': 23.1,
            'apg': 10.7,
            'mpg': 36.4
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2020-21',
            'tusg': 33.2,
            'pvr': 16.1,
            'ppg': 20.6,
            'apg': 6.9,
            'mpg': 32.2,
            'games': 40
        },
        'recovery_notes': 'Declined significantly, lost explosiveness (71% of pre-injury PVR)'
    },
    {
        'player': 'DeMarcus Cousins',
        'injury_type': 'Achilles Tear',
        'injury_date': '2018-01-26',
        'injury_season': '2017-18',
        'pre_injury': {
            'season': '2017-18',
            'tusg': 36.9,
            'pvr': 18.5,
            'ppg': 25.2,
            'apg': 5.4,
            'mpg': 36.2
        },
        'post_injury_1yr': {
            'season': '2018-19',
            'tusg': 30.4,
            'pvr': 11.2,
            'ppg': 16.3,
            'apg': 3.6,
            'mpg': 25.7,
            'games': 30
        },
        'post_injury_2yr': {
            'season': '2019-20',
            'tusg': 27.8,
            'pvr': 8.9,
            'ppg': 8.9,
            'apg': 1.4,
            'mpg': 16.3,
            'games': 25
        },
        'recovery_notes': 'Career effectively ended, only 48% of pre-injury PVR by year 2'
    },
    {
        'player': 'Gordon Hayward',
        'injury_type': 'Ankle Fracture',
        'injury_date': '2017-10-17',
        'injury_season': '2017-18',
        'pre_injury': {
            'season': '2016-17',
            'tusg': 34.3,
            'pvr': 22.4,
            'ppg': 21.9,
            'apg': 3.5,
            'mpg': 34.5
        },
        'post_injury_1yr': {
            'season': '2018-19',
            'tusg': 29.1,
            'pvr': 15.8,
            'ppg': 11.5,
            'apg': 3.4,
            'mpg': 25.9,
            'games': 72
        },
        'post_injury_2yr': {
            'season': '2019-20',
            'tusg': 31.4,
            'pvr': 19.2,
            'ppg': 17.5,
            'apg': 4.1,
            'mpg': 33.5,
            'games': 52
        },
        'recovery_notes': 'Good recovery trajectory, reached 86% of pre-injury PVR by year 2'
    },
    {
        'player': 'Zach LaVine',
        'injury_type': 'ACL Tear',
        'injury_date': '2017-02-03',
        'injury_season': '2016-17',
        'pre_injury': {
            'season': '2016-17',
            'tusg': 35.2,
            'pvr': 16.8,
            'ppg': 18.9,
            'apg': 3.4,
            'mpg': 37.2
        },
        'post_injury_1yr': {
            'season': '2017-18',
            'tusg': 36.8,
            'pvr': 18.2,
            'ppg': 16.7,
            'apg': 3.9,
            'mpg': 31.8,
            'games': 24
        },
        'post_injury_2yr': {
            'season': '2018-19',
            'tusg': 38.4,
            'pvr': 19.6,
            'ppg': 23.7,
            'apg': 4.7,
            'mpg': 34.5,
            'games': 63
        },
        'recovery_notes': 'Excellent recovery, exceeded pre-injury levels (117% of pre-injury PVR)'
    },
    {
        'player': 'Kristaps Porzingis',
        'injury_type': 'ACL Tear',
        'injury_date': '2018-02-06',
        'injury_season': '2017-18',
        'pre_injury': {
            'season': '2017-18',
            'tusg': 35.6,
            'pvr': 17.9,
            'ppg': 22.7,
            'apg': 1.2,
            'mpg': 32.2
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2019-20',
            'tusg': 31.2,
            'pvr': 14.8,
            'ppg': 20.4,
            'apg': 1.5,
            'mpg': 31.8,
            'games': 57
        },
        'recovery_notes': 'Moderate recovery, mobility affected (83% of pre-injury PVR)'
    },
    {
        'player': 'Jamal Murray',
        'injury_type': 'ACL Tear',
        'injury_date': '2021-04-12',
        'injury_season': '2020-21',
        'pre_injury': {
            'season': '2020-21',
            'tusg': 37.8,
            'pvr': 21.4,
            'ppg': 21.2,
            'apg': 4.8,
            'mpg': 36.2
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2022-23',
            'tusg': 35.6,
            'pvr': 20.8,
            'ppg': 20.0,
            'apg': 4.0,
            'mpg': 32.7,
            'games': 65
        },
        'recovery_notes': 'Strong recovery, near pre-injury form (97% of pre-injury PVR)'
    },
    {
        'player': 'Victor Oladipo',
        'injury_type': 'Quad Rupture',
        'injury_date': '2019-01-23',
        'injury_season': '2018-19',
        'pre_injury': {
            'season': '2017-18',
            'tusg': 37.2,
            'pvr': 23.1,
            'ppg': 23.1,
            'apg': 4.3,
            'mpg': 34.0
        },
        'post_injury_1yr': {
            'season': '2019-20',
            'tusg': 31.8,
            'pvr': 14.7,
            'ppg': 14.5,
            'apg': 2.9,
            'mpg': 28.8,
            'games': 19
        },
        'post_injury_2yr': {
            'season': '2020-21',
            'tusg': 29.4,
            'pvr': 12.8,
            'ppg': 19.8,
            'apg': 4.8,
            'mpg': 31.4,
            'games': 33
        },
        'recovery_notes': 'Struggled to return to All-Star form (55% of pre-injury PVR)'
    },
    {
        'player': 'Kawhi Leonard',
        'injury_type': 'Quad Tendinopathy',
        'injury_date': '2017-12-18',
        'injury_season': '2017-18',
        'pre_injury': {
            'season': '2016-17',
            'tusg': 34.8,
            'pvr': 24.6,
            'ppg': 25.5,
            'apg': 3.5,
            'mpg': 33.4
        },
        'post_injury_1yr': {
            'season': '2018-19',
            'tusg': 33.9,
            'pvr': 23.8,
            'ppg': 26.6,
            'apg': 3.3,
            'mpg': 34.0,
            'games': 60
        },
        'post_injury_2yr': {
            'season': '2019-20',
            'tusg': 34.5,
            'pvr': 24.2,
            'ppg': 27.1,
            'apg': 4.9,
            'mpg': 32.1,
            'games': 57
        },
        'recovery_notes': 'Elite recovery with load management, 98% of pre-injury PVR'
    },
    {
        'player': 'Blake Griffin',
        'injury_type': 'Multiple Knee Surgeries',
        'injury_date': '2015-12-26',
        'injury_season': '2015-16',
        'pre_injury': {
            'season': '2013-14',
            'tusg': 36.4,
            'pvr': 20.8,
            'ppg': 24.1,
            'apg': 3.9,
            'mpg': 35.8
        },
        'post_injury_1yr': {
            'season': '2016-17',
            'tusg': 34.2,
            'pvr': 18.9,
            'ppg': 21.6,
            'apg': 4.9,
            'mpg': 33.5,
            'games': 61
        },
        'post_injury_2yr': {
            'season': '2017-18',
            'tusg': 33.8,
            'pvr': 19.4,
            'ppg': 22.3,
            'apg': 5.4,
            'mpg': 34.0,
            'games': 58
        },
        'recovery_notes': 'Adapted game style, maintained 91-93% of pre-injury PVR'
    },
    {
        'player': 'Isaiah Thomas',
        'injury_type': 'Hip Injury',
        'injury_date': '2017-05-02',
        'injury_season': '2016-17',
        'pre_injury': {
            'season': '2016-17',
            'tusg': 42.1,
            'pvr': 24.3,
            'ppg': 28.9,
            'apg': 5.9,
            'mpg': 33.8
        },
        'post_injury_1yr': {
            'season': '2017-18',
            'tusg': 35.2,
            'pvr': 12.6,
            'ppg': 15.2,
            'apg': 5.0,
            'mpg': 27.9,
            'games': 32
        },
        'post_injury_2yr': {
            'season': '2018-19',
            'tusg': 32.4,
            'pvr': 10.8,
            'ppg': 8.1,
            'apg': 1.9,
            'mpg': 15.2,
            'games': 12
        },
        'recovery_notes': 'Career derailed, never regained All-Star form (44% of pre-injury PVR)'
    },
    {
        'player': 'Brandon Roy',
        'injury_type': 'Multiple Knee Surgeries',
        'injury_date': '2010-05-08',
        'injury_season': '2009-10',
        'pre_injury': {
            'season': '2008-09',
            'tusg': 37.8,
            'pvr': 22.6,
            'ppg': 22.6,
            'apg': 5.1,
            'mpg': 37.2
        },
        'post_injury_1yr': {
            'season': '2010-11',
            'tusg': 33.5,
            'pvr': 17.2,
            'ppg': 12.2,
            'apg': 2.6,
            'mpg': 23.4,
            'games': 47
        },
        'post_injury_2yr': None,
        'recovery_notes': 'Career ended prematurely, retired at 27 (76% of pre-injury PVR before retirement)'
    },
    {
        'player': 'Shaun Livingston',
        'injury_type': 'Knee Dislocation',
        'injury_date': '2007-02-26',
        'injury_season': '2006-07',
        'pre_injury': {
            'season': '2006-07',
            'tusg': 34.6,
            'pvr': 16.4,
            'ppg': 9.3,
            'apg': 5.3,
            'mpg': 30.2
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2008-09',
            'tusg': 28.9,
            'pvr': 11.2,
            'ppg': 4.4,
            'apg': 3.1,
            'mpg': 18.8,
            'games': 4
        },
        'recovery_notes': 'Miraculous comeback after career-threatening injury, became valuable role player (68% of pre-injury PVR)'
    },
    {
        'player': 'Grant Hill',
        'injury_type': 'Ankle Fracture',
        'injury_date': '2000-03-14',
        'injury_season': '1999-00',
        'pre_injury': {
            'season': '1999-00',
            'tusg': 36.2,
            'pvr': 24.1,
            'ppg': 25.8,
            'apg': 5.2,
            'mpg': 38.9
        },
        'post_injury_1yr': {
            'season': '2000-01',
            'tusg': 32.8,
            'pvr': 16.8,
            'ppg': 11.9,
            'apg': 3.2,
            'mpg': 26.7,
            'games': 4
        },
        'post_injury_2yr': None,
        'recovery_notes': 'Multiple complications, missed several seasons, eventually reinvented himself (70% of pre-injury PVR)'
    },
    {
        'player': 'Penny Hardaway',
        'injury_type': 'Multiple Knee Surgeries',
        'injury_date': '1997-11-10',
        'injury_season': '1997-98',
        'pre_injury': {
            'season': '1996-97',
            'tusg': 37.5,
            'pvr': 23.8,
            'ppg': 20.5,
            'apg': 5.3,
            'mpg': 37.1
        },
        'post_injury_1yr': {
            'season': '1998-99',
            'tusg': 34.1,
            'pvr': 18.9,
            'ppg': 15.8,
            'apg': 4.2,
            'mpg': 31.5,
            'games': 50
        },
        'post_injury_2yr': {
            'season': '1999-00',
            'tusg': 32.6,
            'pvr': 17.4,
            'ppg': 16.9,
            'apg': 5.4,
            'mpg': 33.6,
            'games': 59
        },
        'recovery_notes': 'Lost explosiveness, never returned to All-NBA level (73% of pre-injury PVR)'
    },
    {
        'player': 'Joel Embiid',
        'injury_type': 'Multiple Foot Surgeries',
        'injury_date': '2014-06-20',
        'injury_season': '2014-15',
        'pre_injury': {
            'season': 'College',
            'tusg': 38.2,
            'pvr': 25.1,
            'ppg': 11.2,
            'apg': 1.4,
            'mpg': 23.1
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2016-17',
            'tusg': 36.8,
            'pvr': 23.4,
            'ppg': 20.2,
            'apg': 2.1,
            'mpg': 25.4,
            'games': 31
        },
        'recovery_notes': 'Dominated after recovery, became MVP-caliber center (93% of pre-injury PVR projection)'
    },
    {
        'player': 'Andrew Bynum',
        'injury_type': 'Multiple Knee Injuries',
        'injury_date': '2012-07-24',
        'injury_season': '2012-13',
        'pre_injury': {
            'season': '2011-12',
            'tusg': 33.1,
            'pvr': 18.7,
            'ppg': 18.7,
            'apg': 1.4,
            'mpg': 35.2
        },
        'post_injury_1yr': None,
        'post_injury_2yr': {
            'season': '2013-14',
            'tusg': 27.4,
            'pvr': 9.2,
            'ppg': 8.4,
            'apg': 0.4,
            'mpg': 20.4,
            'games': 26
        },
        'recovery_notes': 'Career effectively ended at 26, never recovered form (49% of pre-injury PVR)'
    },
    {
        'player': 'Yao Ming',
        'injury_type': 'Multiple Foot/Ankle Injuries',
        'injury_date': '2009-05-10',
        'injury_season': '2008-09',
        'pre_injury': {
            'season': '2006-07',
            'tusg': 34.5,
            'pvr': 21.3,
            'ppg': 25.0,
            'apg': 2.0,
            'mpg': 37.0
        },
        'post_injury_1yr': {
            'season': '2009-10',
            'tusg': 31.8,
            'pvr': 18.6,
            'ppg': 19.0,
            'apg': 1.8,
            'mpg': 26.9,
            'games': 5
        },
        'post_injury_2yr': {
            'season': '2010-11',
            'tusg': 30.2,
            'pvr': 16.1,
            'ppg': 10.2,
            'apg': 1.4,
            'mpg': 21.4,
            'games': 5
        },
        'recovery_notes': 'Chronic foot issues forced early retirement at 30 (76% of pre-injury PVR)'
    }
]

CURRENT_INJURY_WATCH = [
    {
        'player': 'Ja Morant',
        'injury_type': 'Shoulder Labral Tear',
        'injury_date': '2024-11-06',
        'expected_return': '2025-02-15',
        'pre_injury_current': {
            'season': '2023-24',
            'tusg': 39.2,
            'pvr': 23.8,
            'ppg': 25.1,
            'apg': 8.1,
            'mpg': 35.4
        },
        'projected_impact': 'Moderate',
        'notes': 'Expected 90-95% recovery, minimal long-term impact for guards'
    },
    {
        'player': 'Kawhi Leonard',
        'injury_type': 'Knee Inflammation (Chronic)',
        'injury_date': '2024-04-25',
        'expected_return': '2025-01-10',
        'pre_injury_current': {
            'season': '2023-24',
            'tusg': 33.8,
            'pvr': 23.4,
            'ppg': 23.7,
            'apg': 3.6,
            'mpg': 32.1
        },
        'projected_impact': 'Moderate',
        'notes': 'Ongoing load management, projected 95%+ with rest'
    },
    {
        'player': 'Joel Embiid',
        'injury_type': 'Knee Meniscus',
        'injury_date': '2024-10-15',
        'expected_return': '2025-01-05',
        'pre_injury_current': {
            'season': '2023-24',
            'tusg': 36.1,
            'pvr': 28.2,
            'ppg': 34.7,
            'apg': 5.6,
            'mpg': 34.3
        },
        'projected_impact': 'Low-Moderate',
        'notes': 'Minor meniscus repair, expected 95%+ recovery within 3 months'
    }
]

INJURY_TYPE_STATS = {
    'ACL Tear': {
        'avg_recovery_time_months': 12,
        'expected_pvr_retention_1yr': 0.75,
        'expected_pvr_retention_2yr': 0.88,
        'expected_tusg_retention_1yr': 0.82,
        'expected_tusg_retention_2yr': 0.91,
        'severity': 'High'
    },
    'Achilles Tear': {
        'avg_recovery_time_months': 12,
        'expected_pvr_retention_1yr': 0.65,
        'expected_pvr_retention_2yr': 0.75,
        'expected_tusg_retention_1yr': 0.78,
        'expected_tusg_retention_2yr': 0.85,
        'severity': 'Very High'
    },
    'Leg Fracture': {
        'avg_recovery_time_months': 10,
        'expected_pvr_retention_1yr': 0.88,
        'expected_pvr_retention_2yr': 0.96,
        'expected_tusg_retention_1yr': 0.90,
        'expected_tusg_retention_2yr': 0.97,
        'severity': 'High'
    },
    'Ankle Fracture': {
        'avg_recovery_time_months': 8,
        'expected_pvr_retention_1yr': 0.80,
        'expected_pvr_retention_2yr': 0.90,
        'expected_tusg_retention_1yr': 0.85,
        'expected_tusg_retention_2yr': 0.92,
        'severity': 'Moderate'
    },
    'Quad Rupture': {
        'avg_recovery_time_months': 9,
        'expected_pvr_retention_1yr': 0.68,
        'expected_pvr_retention_2yr': 0.78,
        'expected_tusg_retention_1yr': 0.80,
        'expected_tusg_retention_2yr': 0.87,
        'severity': 'High'
    },
    'Quad Tendinopathy': {
        'avg_recovery_time_months': 6,
        'expected_pvr_retention_1yr': 0.92,
        'expected_pvr_retention_2yr': 0.98,
        'expected_tusg_retention_1yr': 0.95,
        'expected_tusg_retention_2yr': 0.99,
        'severity': 'Moderate'
    },
    'Multiple Knee Surgeries': {
        'avg_recovery_time_months': 10,
        'expected_pvr_retention_1yr': 0.85,
        'expected_pvr_retention_2yr': 0.91,
        'expected_tusg_retention_1yr': 0.88,
        'expected_tusg_retention_2yr': 0.93,
        'severity': 'High'
    },
    'Hip Injury': {
        'avg_recovery_time_months': 8,
        'expected_pvr_retention_1yr': 0.60,
        'expected_pvr_retention_2yr': 0.68,
        'expected_tusg_retention_1yr': 0.75,
        'expected_tusg_retention_2yr': 0.82,
        'severity': 'Very High'
    },
    'Knee Dislocation': {
        'avg_recovery_time_months': 15,
        'expected_pvr_retention_1yr': 0.55,
        'expected_pvr_retention_2yr': 0.70,
        'expected_tusg_retention_1yr': 0.72,
        'expected_tusg_retention_2yr': 0.83,
        'severity': 'Very High'
    },
    'Multiple Foot/Ankle Injuries': {
        'avg_recovery_time_months': 12,
        'expected_pvr_retention_1yr': 0.82,
        'expected_pvr_retention_2yr': 0.88,
        'expected_tusg_retention_1yr': 0.87,
        'expected_tusg_retention_2yr': 0.91,
        'severity': 'High'
    },
    'Multiple Foot Surgeries': {
        'avg_recovery_time_months': 24,
        'expected_pvr_retention_1yr': 0.78,
        'expected_pvr_retention_2yr': 0.90,
        'expected_tusg_retention_1yr': 0.85,
        'expected_tusg_retention_2yr': 0.93,
        'severity': 'High'
    },
    'Multiple Knee Injuries': {
        'avg_recovery_time_months': 12,
        'expected_pvr_retention_1yr': 0.70,
        'expected_pvr_retention_2yr': 0.78,
        'expected_tusg_retention_1yr': 0.80,
        'expected_tusg_retention_2yr': 0.87,
        'severity': 'High'
    },
    'Shoulder Labral Tear': {
        'avg_recovery_time_months': 4,
        'expected_pvr_retention_1yr': 0.93,
        'expected_pvr_retention_2yr': 0.97,
        'expected_tusg_retention_1yr': 0.95,
        'expected_tusg_retention_2yr': 0.98,
        'severity': 'Low-Moderate'
    },
    'Knee Inflammation (Chronic)': {
        'avg_recovery_time_months': 3,
        'expected_pvr_retention_1yr': 0.95,
        'expected_pvr_retention_2yr': 0.97,
        'expected_tusg_retention_1yr': 0.96,
        'expected_tusg_retention_2yr': 0.98,
        'severity': 'Low-Moderate'
    },
    'Knee Meniscus': {
        'avg_recovery_time_months': 3,
        'expected_pvr_retention_1yr': 0.96,
        'expected_pvr_retention_2yr': 0.98,
        'expected_tusg_retention_1yr': 0.97,
        'expected_tusg_retention_2yr': 0.99,
        'severity': 'Low'
    }
}

def calculate_recovery_projection(injury_type, pre_tusg, pre_pvr):
    """Project recovery metrics based on injury type and historical averages"""
    injury_stats = INJURY_TYPE_STATS.get(injury_type, {
        'avg_recovery_time_months': 9,
        'expected_pvr_retention_1yr': 0.80,
        'expected_pvr_retention_2yr': 0.88,
        'expected_tusg_retention_1yr': 0.85,
        'expected_tusg_retention_2yr': 0.92,
        'severity': 'Moderate'
    })
    
    return {
        'recovery_time_months': injury_stats['avg_recovery_time_months'],
        'projected_1yr_tusg': round(pre_tusg * injury_stats['expected_tusg_retention_1yr'], 2),
        'projected_1yr_pvr': round(pre_pvr * injury_stats['expected_pvr_retention_1yr'], 2),
        'projected_2yr_tusg': round(pre_tusg * injury_stats['expected_tusg_retention_2yr'], 2),
        'projected_2yr_pvr': round(pre_pvr * injury_stats['expected_pvr_retention_2yr'], 2),
        'severity': injury_stats['severity']
    }

def calculate_actual_recovery(pre_metrics, post_metrics):
    """Calculate actual recovery percentages"""
    if not post_metrics:
        return None
    
    tusg_retention = (post_metrics['tusg'] / pre_metrics['tusg']) * 100 if pre_metrics['tusg'] > 0 else 0
    pvr_retention = (post_metrics['pvr'] / pre_metrics['pvr']) * 100 if pre_metrics['pvr'] > 0 else 0
    
    return {
        'tusg_retention': round(tusg_retention, 1),
        'pvr_retention': round(pvr_retention, 1),
        'tusg_delta': round(post_metrics['tusg'] - pre_metrics['tusg'], 2),
        'pvr_delta': round(post_metrics['pvr'] - pre_metrics['pvr'], 2)
    }

def analyze_injury_type_trends():
    """Analyze recovery trends by injury type"""
    injury_trends = {}
    
    for injury in INJURY_DATABASE:
        injury_type = injury['injury_type']
        
        if injury_type not in injury_trends:
            injury_trends[injury_type] = {
                'count': 0,
                'tusg_drops_1yr': [],
                'pvr_drops_1yr': [],
                'tusg_drops_2yr': [],
                'pvr_drops_2yr': []
            }
        
        injury_trends[injury_type]['count'] += 1
        
        if injury['post_injury_1yr']:
            recovery_1yr = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_1yr'])
            injury_trends[injury_type]['tusg_drops_1yr'].append(recovery_1yr['tusg_delta'])
            injury_trends[injury_type]['pvr_drops_1yr'].append(recovery_1yr['pvr_delta'])
        
        if injury['post_injury_2yr']:
            recovery_2yr = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_2yr'])
            injury_trends[injury_type]['tusg_drops_2yr'].append(recovery_2yr['tusg_delta'])
            injury_trends[injury_type]['pvr_drops_2yr'].append(recovery_2yr['pvr_delta'])
    
    summary = {}
    for injury_type, data in injury_trends.items():
        summary[injury_type] = {
            'cases': data['count'],
            'avg_tusg_drop_1yr': round(sum(data['tusg_drops_1yr']) / len(data['tusg_drops_1yr']), 2) if data['tusg_drops_1yr'] else 'N/A',
            'avg_pvr_drop_1yr': round(sum(data['pvr_drops_1yr']) / len(data['pvr_drops_1yr']), 2) if data['pvr_drops_1yr'] else 'N/A',
            'avg_tusg_drop_2yr': round(sum(data['tusg_drops_2yr']) / len(data['tusg_drops_2yr']), 2) if data['tusg_drops_2yr'] else 'N/A',
            'avg_pvr_drop_2yr': round(sum(data['pvr_drops_2yr']) / len(data['pvr_drops_2yr']), 2) if data['pvr_drops_2yr'] else 'N/A'
        }
    
    return summary

def generate_insights():
    """Generate educational insights from injury data"""
    insights = []
    
    for injury in INJURY_DATABASE:
        player = injury['player']
        injury_type = injury['injury_type']
        
        if injury['post_injury_2yr']:
            recovery_2yr = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_2yr'])
            insights.append({
                'player': player,
                'injury_type': injury_type,
                'insight': f"{player} maintained {recovery_2yr['pvr_retention']:.0f}% of pre-injury PVR 2 years post-{injury_type}",
                'tusg_retention': recovery_2yr['tusg_retention'],
                'pvr_retention': recovery_2yr['pvr_retention']
            })
        elif injury['post_injury_1yr']:
            recovery_1yr = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_1yr'])
            insights.append({
                'player': player,
                'injury_type': injury_type,
                'insight': f"{player} at {recovery_1yr['pvr_retention']:.0f}% of pre-injury PVR 1 year post-{injury_type}",
                'tusg_retention': recovery_1yr['tusg_retention'],
                'pvr_retention': recovery_1yr['pvr_retention']
            })
    
    insights.sort(key=lambda x: x['pvr_retention'], reverse=True)
    return insights

def export_injury_data():
    """Export comprehensive injury tracking data to JSON"""
    analyzed_injuries = []
    
    for injury in INJURY_DATABASE:
        projection = calculate_recovery_projection(
            injury['injury_type'],
            injury['pre_injury']['tusg'],
            injury['pre_injury']['pvr']
        )
        
        recovery_1yr = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_1yr']) if injury['post_injury_1yr'] else None
        recovery_2yr = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_2yr']) if injury['post_injury_2yr'] else None
        
        analyzed_injuries.append({
            **injury,
            'projection': projection,
            'recovery_1yr': recovery_1yr,
            'recovery_2yr': recovery_2yr
        })
    
    current_injuries_with_projections = []
    for current_injury in CURRENT_INJURY_WATCH:
        projection = calculate_recovery_projection(
            current_injury['injury_type'],
            current_injury['pre_injury_current']['tusg'],
            current_injury['pre_injury_current']['pvr']
        )
        
        from datetime import datetime as dt
        injury_date = dt.fromisoformat(current_injury['injury_date'])
        expected_return = dt.fromisoformat(current_injury['expected_return'])
        days_out = (expected_return - dt.now()).days
        
        current_injuries_with_projections.append({
            **current_injury,
            'projection': projection,
            'days_until_return': max(0, days_out)
        })
    
    injury_trends = analyze_injury_type_trends()
    insights = generate_insights()
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_injuries_tracked': len(INJURY_DATABASE),
        'current_injuries': len(CURRENT_INJURY_WATCH),
        'injuries': analyzed_injuries,
        'current_injury_watch': current_injuries_with_projections,
        'injury_type_stats': INJURY_TYPE_STATS,
        'injury_trends': injury_trends,
        'insights': insights
    }
    
    with open('injury_tracker_data.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Exported {len(INJURY_DATABASE)} injury records to injury_tracker_data.json")
    print(f"✅ Tracking {len(CURRENT_INJURY_WATCH)} current injuries")
    return output

def print_injury_report():
    """Print comprehensive injury recovery report"""
    print("=" * 100)
    print("🏀 NBA INJURY COMEBACK TRACKER - TAYLOR VECTOR TERMINAL")
    print("=" * 100)
    print(f"\n📊 Tracking {len(INJURY_DATABASE)} Major NBA Injuries\n")
    
    print("🏥 INJURY RECOVERY OVERVIEW")
    print("-" * 100)
    print(f"{'Player':<25} {'Injury Type':<25} {'Pre-PVR':<10} {'2Yr PVR':<10} {'Recovery %':<12}")
    print("-" * 100)
    
    for injury in INJURY_DATABASE:
        player = injury['player']
        injury_type = injury['injury_type']
        pre_pvr = injury['pre_injury']['pvr']
        
        if injury['post_injury_2yr']:
            post_pvr = injury['post_injury_2yr']['pvr']
            recovery = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_2yr'])
            recovery_pct = f"{recovery['pvr_retention']:.1f}%"
        elif injury['post_injury_1yr']:
            post_pvr = injury['post_injury_1yr']['pvr']
            recovery = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_1yr'])
            recovery_pct = f"{recovery['pvr_retention']:.1f}% (1yr)"
        else:
            post_pvr = "N/A"
            recovery_pct = "TBD"
        
        print(f"{player:<25} {injury_type:<25} {pre_pvr:<10.1f} {str(post_pvr):<10} {recovery_pct:<12}")
    
    print("\n\n📈 INJURY TYPE STATISTICS")
    print("-" * 100)
    trends = analyze_injury_type_trends()
    
    for injury_type, stats in trends.items():
        print(f"\n{injury_type}:")
        print(f"  Cases Tracked: {stats['cases']}")
        print(f"  Avg TUSG% drop (1yr): {stats['avg_tusg_drop_1yr']}")
        print(f"  Avg PVR drop (1yr): {stats['avg_pvr_drop_1yr']}")
        print(f"  Avg TUSG% drop (2yr): {stats['avg_tusg_drop_2yr']}")
        print(f"  Avg PVR drop (2yr): {stats['avg_pvr_drop_2yr']}")
    
    print("\n\n💡 KEY INSIGHTS")
    print("-" * 100)
    insights = generate_insights()
    
    for idx, insight in enumerate(insights[:8], 1):
        print(f"{idx}. {insight['insight']}")
    
    print("\n\n🎯 BEST RECOVERIES (2-Year)")
    print("-" * 100)
    best_recoveries = [i for i in INJURY_DATABASE if i['post_injury_2yr']]
    best_recoveries.sort(key=lambda x: calculate_actual_recovery(x['pre_injury'], x['post_injury_2yr'])['pvr_retention'], reverse=True)
    
    for idx, injury in enumerate(best_recoveries[:5], 1):
        recovery = calculate_actual_recovery(injury['pre_injury'], injury['post_injury_2yr'])
        print(f"{idx}. {injury['player']} - {recovery['pvr_retention']:.1f}% PVR retention ({injury['injury_type']})")
    
    print("\n" + "=" * 100)

if __name__ == '__main__':
    print_injury_report()
    export_injury_data()
