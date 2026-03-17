import pandas as pd
import os
from sqlalchemy import text
from app.db import engine 

def load_local_csvs_to_mysql():
    # 1. Map your local files to their respective seasons
    file_configs = [
        {"path": "../data/raw/bundesliga_23_24.csv", "season": "2023-2024"},
        {"path": "../data/raw/bundesliga_24_25.csv", "season": "2024-2025"},
        {"path": "../data/raw/bundesliga_25_26.csv", "season": "2025-2026"}
    ]

    all_matches = []

    # 2. Loop through the 3 files, read, and clean them
    for config in file_configs:
        file_path = config["path"]
        season_label = config["season"]

        if not os.path.exists(file_path):
            print(f"WARNING: Could not find {file_path}. Skipping this season.")
            continue

        print(f"Reading {season_label} data from {file_path}...")
        df = pd.read_csv(file_path)

        # Keep only necessary columns
        df = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].copy()

        # Rename to match MySQL schema
        df.rename(columns={
            'Date': 'match_date',
            'HomeTeam': 'home_team',
            'AwayTeam': 'away_team',
            'FTHG': 'home_goals',
            'FTAG': 'away_goals'
        }, inplace=True)

        # Standardize dates to YYYY-MM-DD (handles DD/MM/YYYY or DD/MM/YY)
        df['match_date'] = pd.to_datetime(df['match_date'], dayfirst=True).dt.date
        
        # Add the season column
        df['season'] = season_label

        all_matches.append(df)

    if not all_matches:
        print("ERROR: No CSV files were loaded. Exiting.")
        return

    # Combine all 3 seasons into one master DataFrame
    master_df = pd.concat(all_matches, ignore_index=True)
    
    # Drop any rows where matches were postponed/cancelled (no goals recorded)
    master_df.dropna(subset=['home_goals', 'away_goals'], inplace=True)

    print(f"Total historical matches loaded into memory: {len(master_df)}")

    # 3. DUPLICATE PROTECTION: Check MySQL for what already exists
    # We create a unique "match signature" (Date + Home + Away)
    print("Checking database to prevent duplicates...")
    existing_df = pd.read_sql("SELECT match_date, home_team, away_team FROM matches", engine)
    
    master_df['signature'] = master_df['match_date'].astype(str) + master_df['home_team'] + master_df['away_team']
    
    if not existing_df.empty:
        existing_df['signature'] = existing_df['match_date'].astype(str) + existing_df['home_team'] + existing_df['away_team']
        # Filter the master_df to ONLY keep rows whose signature is NOT in the database
        new_matches_df = master_df[~master_df['signature'].isin(existing_df['signature'])].copy()
    else:
        new_matches_df = master_df.copy()

    # Drop the temporary signature column before inserting
    new_matches_df.drop(columns=['signature'], inplace=True)

    # 4. Insert the new matches
    if new_matches_df.empty:
        print("SUCCESS: Database is already up to date! No new matches to insert.")
    else:
        print(f"Found {len(new_matches_df)} new matches. Inserting into MySQL...")
        try:
            new_matches_df.to_sql('matches', con=engine, if_exists='append', index=False)
            print(f" SUCCESS: {len(new_matches_df)} matches successfully inserted!")
        except Exception as e:
            print(f"ERROR: Failed to insert data.\nDetails: {e}")

if __name__ == "__main__":
    load_local_csvs_to_mysql()