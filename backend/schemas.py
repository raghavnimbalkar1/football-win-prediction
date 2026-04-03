"""
Pydantic request/response schemas for FastAPI validation
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ============ MATCH INITIALIZATION ============

class InitializeMatchRequest(BaseModel):
    """Request to initialize a new live match"""
    match_id: int
    external_match_id: str
    home_team: str
    away_team: str
    match_date: str  # ISO datetime string
    
    class Config:
        example = {
            "match_id": 1,
            "external_match_id": "sofascore_12345",
            "home_team": "Bayern Munich",
            "away_team": "Borussia Dortmund",
            "match_date": "2026-04-03T20:30:00"
        }


# ============ SCORE UPDATE ============

class UpdateScoreRequest(BaseModel):
    """Request to update match score"""
    home_goals: int
    away_goals: int
    minute: int
    second: int = 0
    
    class Config:
        example = {
            "home_goals": 1,
            "away_goals": 0,
            "minute": 25,
            "second": 30
        }


# ============ MATCH EVENT ============

class AddEventRequest(BaseModel):
    """Request to add a match event"""
    event_type: str  # "goal", "yellow_card", "red_card", "substitution", "injury"
    team: str
    player_name: str
    minute: int
    second: int = 0
    description: str = ""
    
    class Config:
        example = {
            "event_type": "goal",
            "team": "Bayern Munich",
            "player_name": "Robert Lewandowski",
            "minute": 35,
            "second": 15,
            "description": "Header from close range"
        }


# ============ PREDICTION UPDATE ============

class UpdatePredictionRequest(BaseModel):
    """Request to recalculate predictions"""
    recalculate_momentum: bool = False
    
    class Config:
        example = {
            "recalculate_momentum": True
        }
