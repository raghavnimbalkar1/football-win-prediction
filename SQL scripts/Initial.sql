-- 1. Create the database for the project
CREATE DATABASE IF NOT EXISTS live_win_probability;
USE live_win_probability;

-- 2. Create the table for historical matches
CREATE TABLE IF NOT EXISTS matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    match_date DATE NOT NULL,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    home_goals INT NOT NULL,
    away_goals INT NOT NULL,
    season VARCHAR(10) NOT NULL
);

-- 3. Create the table for dynamic team metrics (Elo & Form)
CREATE TABLE IF NOT EXISTS team_metrics (
    team_name VARCHAR(50) PRIMARY KEY,
    current_elo FLOAT DEFAULT 1500.0,
    attacking_strength FLOAT DEFAULT 0.0,
    defensive_weakness FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. Create table for live matches (real-time tracking)
CREATE TABLE IF NOT EXISTS live_matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    external_match_id VARCHAR(100) UNIQUE,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    current_minute INT DEFAULT 0,
    home_goals INT DEFAULT 0,
    away_goals INT DEFAULT 0,
    status ENUM('scheduled', 'in_progress', 'finished', 'postponed') DEFAULT 'scheduled',
    match_date DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_match_date (match_date)
);

-- 5. Create table for match events (goals, cards, substitutions)
CREATE TABLE IF NOT EXISTS match_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    event_type ENUM('goal', 'yellow_card', 'red_card', 'substitution', 'injury') NOT NULL,
    team VARCHAR(50) NOT NULL,
    player_name VARCHAR(100),
    minute INT NOT NULL,
    second INT DEFAULT 0,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES live_matches (match_id) ON DELETE CASCADE,
    INDEX idx_match_id (match_id),
    INDEX idx_event_type (event_type)
);

-- 6. Create table for prediction snapshots (historical predictions per minute)
CREATE TABLE IF NOT EXISTS prediction_snapshots (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    minute INT NOT NULL,
    home_win_prob FLOAT NOT NULL,
    draw_prob FLOAT NOT NULL,
    away_win_prob FLOAT NOT NULL,
    home_xg FLOAT NOT NULL,
    away_xg FLOAT NOT NULL,
    home_elo FLOAT NOT NULL,
    away_elo FLOAT NOT NULL,
    current_score_home INT NOT NULL,
    current_score_away INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES live_matches (match_id) ON DELETE CASCADE,
    INDEX idx_match_id (match_id),
    INDEX idx_minute (minute)
);

-- 7. Create table for match state cache (momentum, expected goals tracking)
CREATE TABLE IF NOT EXISTS match_state_cache (
    state_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT UNIQUE NOT NULL,
    base_home_xg FLOAT NOT NULL,
    base_away_xg FLOAT NOT NULL,
    current_home_xg FLOAT NOT NULL,
    current_away_xg FLOAT NOT NULL,
    home_momentum FLOAT DEFAULT 0.0,
    away_momentum FLOAT DEFAULT 0.0,
    last_cached TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES live_matches (match_id) ON DELETE CASCADE
);

-- 8. Create table for pre-match baselines (snapshot of initial predictions)
CREATE TABLE IF NOT EXISTS prematch_baselines (
    baseline_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT UNIQUE NOT NULL,
    home_team VARCHAR(50) NOT NULL,
    away_team VARCHAR(50) NOT NULL,
    pre_home_xg FLOAT NOT NULL,
    pre_away_xg FLOAT NOT NULL,
    pre_home_elo FLOAT NOT NULL,
    pre_away_elo FLOAT NOT NULL,
    pre_home_win_prob FLOAT NOT NULL,
    pre_draw_prob FLOAT NOT NULL,
    pre_away_win_prob FLOAT NOT NULL,
    home_form_rating FLOAT DEFAULT 1500.0,
    away_form_rating FLOAT DEFAULT 1500.0,
    league_position_home INT,
    league_position_away INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES live_matches (match_id) ON DELETE CASCADE,
    INDEX idx_match_id (match_id)
);

-- 9. Create table for advanced match statistics (shots, possession, etc.)
CREATE TABLE IF NOT EXISTS match_statistics (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    minute INT NOT NULL,
    home_shots INT DEFAULT 0,
    away_shots INT DEFAULT 0,
    home_shots_on_target INT DEFAULT 0,
    away_shots_on_target INT DEFAULT 0,
    home_possession FLOAT DEFAULT 50.0,
    away_possession FLOAT DEFAULT 50.0,
    home_pass_accuracy FLOAT DEFAULT 0.0,
    away_pass_accuracy FLOAT DEFAULT 0.0,
    home_tackles INT DEFAULT 0,
    away_tackles INT DEFAULT 0,
    home_fouls INT DEFAULT 0,
    away_fouls INT DEFAULT 0,
    home_corners INT DEFAULT 0,
    away_corners INT DEFAULT 0,
    home_yellow_cards INT DEFAULT 0,
    away_yellow_cards INT DEFAULT 0,
    home_red_cards INT DEFAULT 0,
    away_red_cards INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES live_matches (match_id) ON DELETE CASCADE,
    INDEX idx_match_id (match_id),
    INDEX idx_minute (minute)
);