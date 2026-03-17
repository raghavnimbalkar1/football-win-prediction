import math
import pandas as pd
from app.db import engine

# --- CONFIGURATION ---
HOME_ADVANTAGE_ELO = 30
MAX_GOALS = 7 # We calculate probabilities up to 6 goals per team. 7+ is statistically negligible.

# 1. The Core Math Formula
def poisson_probability(lmbda, k):
    """
    Calculates the probability of scoring 'k' goals given an expected goals of 'lmbda'.
    Math: P(k) = (lambda^k * e^-lambda) / k!
    """
    return ((lmbda ** k) * math.exp(-lmbda)) / math.factorial(k)

def get_team_metrics(team_name):
    """Fetches the latest Elo and Form data from MySQL for a specific team."""
    query = f"SELECT * FROM team_metrics WHERE team_name = '{team_name}'"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        raise ValueError(f"❌ ERROR: Team '{team_name}' not found in the database. Check your spelling.")
    
    # Return the first row as a dictionary
    return df.iloc[0].to_dict()

def predict_match(home_team, away_team):
    print(f"Fetching live metrics for {home_team} (Home) vs {away_team} (Away)...")
    
    try:
        home_metrics = get_team_metrics(home_team)
        away_metrics = get_team_metrics(away_team)
    except ValueError as e:
        print(e)
        return

    home_elo = home_metrics['current_elo']
    away_elo = away_metrics['current_elo']
    
    # 2. Calculate Expected Goals (Lambda / xG)
    # We blend their recent form (goals scored/conceded) to get a baseline expectation
    base_home_xg = (home_metrics['attacking_strength'] + away_metrics['defensive_weakness']) / 2
    base_away_xg = (away_metrics['attacking_strength'] + home_metrics['defensive_weakness']) / 2
    
    # We set a floor of 0.1 so the math doesn't break if a team has 0 goals in their last 5 games
    base_home_xg = max(base_home_xg, 0.1)
    base_away_xg = max(base_away_xg, 0.1)

    # We apply an Elo Multiplier to adjust the xG based on true team strength
    home_elo_diff = (home_elo + HOME_ADVANTAGE_ELO) - away_elo
    away_elo_diff = away_elo - (home_elo + HOME_ADVANTAGE_ELO)

    # Dividing by 800 scales the Elo difference smoothly so xG doesn't explode
    home_xg = base_home_xg * math.pow(10, home_elo_diff / 800)
    away_xg = base_away_xg * math.pow(10, away_elo_diff / 800)

    print(f"Calculated xG -> {home_team}: {home_xg:.2f} | {away_team}: {away_xg:.2f}")

    # 3. Build the Bivariate Poisson Matrix
    home_win_prob = 0.0
    draw_prob = 0.0
    away_win_prob = 0.0

    # We loop through every possible scoreline from 0-0 up to 6-6
    for home_goals in range(MAX_GOALS):
        for away_goals in range(MAX_GOALS):
            # The probability of this exact scoreline happening
            scoreline_prob = poisson_probability(home_xg, home_goals) * poisson_probability(away_xg, away_goals)
            
            # Sort the probability into the correct bucket (1, X, or 2)
            if home_goals > away_goals:
                home_win_prob += scoreline_prob
            elif home_goals == away_goals:
                draw_prob += scoreline_prob
            else:
                away_win_prob += scoreline_prob

    # Normalize the probabilities (since we cap at 6 goals, they might sum to 0.99 instead of 1.0)
    total_prob = home_win_prob + draw_prob + away_win_prob
    home_win_prob /= total_prob
    draw_prob /= total_prob
    away_win_prob /= total_prob

    # 4. Output the Results and Implied Odds
    print("\n" + "="*40)
    print(f"MATCH PREDICTION: {home_team} vs {away_team}")
    print("="*40)
    print(f"1 (Home Win) : {home_win_prob * 100:.1f}%  |  Fair Odds: {1/home_win_prob:.2f}")
    print(f"X (Draw)     : {draw_prob * 100:.1f}%  |  Fair Odds: {1/draw_prob:.2f}")
    print(f"2 (Away Win) : {away_win_prob * 100:.1f}%  |  Fair Odds: {1/away_win_prob:.2f}")
    print("="*40 + "\n")

if __name__ == "__main__":
    # Test the engine with a heavyweight clash!
    # Make sure the names perfectly match your database (e.g., 'Bayern Munich', 'Dortmund', 'Leverkusen')
    predict_match("Bayern Munich", "Union Berlin")