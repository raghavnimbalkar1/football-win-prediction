#!/usr/bin/env python3
"""
Add test teams to database for API testing
"""
import sys
sys.path.insert(0, '/Users/raghavnimbalkar/Desktop/live-win-probability/backend')

import logging
from app.db import engine, SessionLocal
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_test_teams():
    """Add test teams with Elo ratings and form metrics to the database"""
    
    test_teams = [
        {
            'team_name': 'Bayern Munich',
            'current_elo': 1850.0,
            'attacking_strength': 2.5,
            'defensive_weakness': 0.8
        },
        {
            'team_name': 'Borussia Dortmund',
            'current_elo': 1720.0,
            'attacking_strength': 2.2,
            'defensive_weakness': 1.1
        },
        {
            'team_name': 'Bayer Leverkusen',
            'current_elo': 1650.0,
            'attacking_strength': 2.0,
            'defensive_weakness': 1.0
        },
        {
            'team_name': 'RB Leipzig',
            'current_elo': 1620.0,
            'attacking_strength': 1.9,
            'defensive_weakness': 1.2
        },
        {
            'team_name': 'Eintracht Frankfurt',
            'current_elo': 1550.0,
            'attacking_strength': 1.7,
            'defensive_weakness': 1.3
        },
        {
            'team_name': 'VfB Stuttgart',
            'current_elo': 1580.0,
            'attacking_strength': 1.8,
            'defensive_weakness': 1.2
        }
    ]
    
    # Create a dataframe and insert into database
    df = pd.DataFrame(test_teams)
    
    try:
        # Replace existing test data (if any)
        df.to_sql('team_metrics', engine, if_exists='append', index=False)
        logger.info(f"✓ Added {len(test_teams)} test teams to database")
        
        # Verify
        result = pd.read_sql("SELECT team_name, current_elo FROM team_metrics", engine)
        logger.info(f"\nTeams in database:\n{result.to_string()}")
        return True
        
    except Exception as e:
        if "Duplicate entry" in str(e):
            logger.warning("⚠️  Teams already exist in database")
            return True
        logger.error(f"Error adding test teams: {e}")
        return False

if __name__ == "__main__":
    logger.info("Adding test teams to database...")
    add_test_teams()
