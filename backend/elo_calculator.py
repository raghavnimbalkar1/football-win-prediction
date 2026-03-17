import pandas as pd
import math
from sqlalchemy import text
from app.db import engine # Imports your DB connection

# --- ELO CONFIGURATION ---
# K-Factor dictates how many points are exchanged per match. 20 is standard for football.
K_FACTOR = 20  
# Home teams naturally have an advantage. We artificially boost the home team's 
# rating by 30 points ONLY for the probability calculation.
HOME_ADVANTAGE = 30  
BASE_ELO = 1500.0

def calculate_elo_and_form():
    print("Fetching historical matches from MySQL...")
    
    # 1. Fetch all matches perfectly sorted by date
    query = "SELECT * FROM matches ORDER BY match_date ASC, match_id ASC"
    matches_df = pd.read_sql(query, engine)
    
    if matches_df.empty:
        print("ERROR: No matches found in the database. Run data_ingestion.py first.")
        return

    print(f"Loaded {len(matches_df)} matches. Beginning chronological playback...")

    # 2. Initialize our memory bank for all teams
    teams_state = {}

    def get_team_state(team_name):
        if team_name not in teams_state:
            teams_state[team_name] = {
                "elo": BASE_ELO,
                "goals_scored": [],    # Will hold chronological history of goals scored
                "goals_conceded": []   # Will hold chronological history of goals conceded
            }
        return teams_state[team_name]

    # 3. Loop through the timeline match by match
    for index, row in matches_df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        home_goals = row['home_goals']
        away_goals = row['away_goals']

        # Get current state
        home_state = get_team_state(home_team)
        away_state = get_team_state(away_team)

        current_home_elo = home_state["elo"]
        current_away_elo = away_state["elo"]

        # --- ELO MATH ---
        # Calculate Expected Win Probability 
        # (We add HOME_ADVANTAGE to the home team just for the math part)
        home_prob = 1 / (1 + math.pow(10, ((current_away_elo - (current_home_elo + HOME_ADVANTAGE)) / 400)))
        away_prob = 1 / (1 + math.pow(10, (((current_home_elo + HOME_ADVANTAGE) - current_away_elo) / 400)))

        # Determine actual match result (1 = Win, 0.5 = Draw, 0 = Loss)
        if home_goals > away_goals:
            home_result, away_result = 1, 0
        elif home_goals < away_goals:
            home_result, away_result = 0, 1
        else:
            home_result, away_result = 0.5, 0.5

        # Update Elo Ratings
        new_home_elo = current_home_elo + K_FACTOR * (home_result - home_prob)
        new_away_elo = current_away_elo + K_FACTOR * (away_result - away_prob)

        # Save new Elo back to state
        teams_state[home_team]["elo"] = new_home_elo
        teams_state[away_team]["elo"] = new_away_elo

        # --- FORM MATH ---
        # Append goals to the tracking lists
        teams_state[home_team]["goals_scored"].append(home_goals)
        teams_state[home_team]["goals_conceded"].append(away_goals)
        
        teams_state[away_team]["goals_scored"].append(away_goals)
        teams_state[away_team]["goals_conceded"].append(home_goals)

    # 4. Finalize the metrics for the database
    print("Timeline finished. Compiling final team metrics...")
    final_metrics = []

    for team, stats in teams_state.items():
        # Get the last 5 matches for form (if they have played at least 5)
        recent_scored = stats["goals_scored"][-5:]
        recent_conceded = stats["goals_conceded"][-5:]
        
        avg_scored = sum(recent_scored) / len(recent_scored) if recent_scored else 0.0
        avg_conceded = sum(recent_conceded) / len(recent_conceded) if recent_conceded else 0.0

        final_metrics.append({
            "team_name": team,
            "current_elo": round(stats["elo"], 2),
            "attacking_strength": round(avg_scored, 2),
            "defensive_weakness": round(avg_conceded, 2)
        })

    metrics_df = pd.DataFrame(final_metrics)

    # 5. Push to MySQL
    print("Updating 'team_metrics' table in MySQL...")
    try:
        with engine.begin() as conn:
            # Clear the old metrics first, so we only store the current up-to-date snapshot
            conn.execute(text("DELETE FROM team_metrics"))
            
        # Insert the fresh metrics
        metrics_df.to_sql('team_metrics', con=engine, if_exists='append', index=False)
        print("SUCCESS: Team metrics calculated and saved to database!")
    except Exception as e:
        print(f"ERROR: Failed to update team metrics.\nDetails: {e}")

if __name__ == "__main__":
    calculate_elo_and_form()