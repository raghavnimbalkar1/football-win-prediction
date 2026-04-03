"""
FastAPI Backend Server for Live Win Probability Prediction Engine
"""
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime

# Import prediction engine
from predictive_engine import predict_match

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ INITIALIZE FASTAPI ============
app = FastAPI(
    title="Live Win Probability API",
    description="Real-time football match prediction engine",
    version="1.0.0"
)

# ============ CORS CONFIGURATION ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ HEALTH CHECK ============
@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "service": "Live Win Probability API"
    }

# ============ PREDICTION ENDPOINTS ============
@app.get("/api/predict/{home_team}/{away_team}")
async def get_prediction(home_team: str, away_team: str):
    """
    Get prediction for a match between two teams
    
    Args:
        home_team: Home team name (URL-encoded)
        away_team: Away team name (URL-encoded)
    
    Returns:
        JSON with win probabilities, odds, xG, and Elo ratings
    
    Example:
        /api/predict/Bayern%20Munich/Borussia%20Dortmund
    """
    try:
        logger.info(f"Requesting prediction: {home_team} vs {away_team}")
        
        # Decode team names (handle URL encoding)
        home_team = home_team.replace("%20", " ")
        away_team = away_team.replace("%20", " ")
        
        # Get prediction from engine
        result = predict_match(home_team, away_team)
        
        # Check for errors
        if "error" in result:
            logger.error(f"Prediction error: {result['error']}")
            raise HTTPException(status_code=404, detail=result["error"])
        
        logger.info(f"Prediction successful for {home_team} vs {away_team}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============ COMPARISON ENDPOINTS ============
@app.get("/api/compare/{home_team_1}/{away_team_1}/{home_team_2}/{away_team_2}")
async def compare_predictions(
    home_team_1: str, 
    away_team_1: str, 
    home_team_2: str, 
    away_team_2: str
):
    """
    Compare predictions for two different matches
    
    Returns:
        JSON with both predictions side-by-side
    """
    try:
        # Decode team names
        home_team_1 = home_team_1.replace("%20", " ")
        away_team_1 = away_team_1.replace("%20", " ")
        home_team_2 = home_team_2.replace("%20", " ")
        away_team_2 = away_team_2.replace("%20", " ")
        
        # Get both predictions
        pred1 = predict_match(home_team_1, away_team_1)
        pred2 = predict_match(home_team_2, away_team_2)
        
        if "error" in pred1 or "error" in pred2:
            raise HTTPException(
                status_code=404, 
                detail="One or more teams not found in database"
            )
        
        return {
            "match_1": pred1,
            "match_2": pred2,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error comparing predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============ STATUS ENDPOINTS ============
@app.get("/api/status")
async def get_status():
    """Get API status and capabilities"""
    return {
        "service": "Live Win Probability API",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": {
            "static_predictions": True,
            "live_updates": False,  # Will be True in Phase 3
            "simulation": False,    # Will be True in Phase 3
            "websocket": False      # Will be True in Phase 3
        },
        "endpoints": {
            "health": "/health",
            "prediction": "/api/predict/{home_team}/{away_team}",
            "comparison": "/api/compare/{home1}/{away1}/{home2}/{away2}",
            "status": "/api/status"
        },
        "timestamp": datetime.now().isoformat()
    }

# ============ ERROR HANDLERS ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom error handler for HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/")
async def root():
    """Root endpoint - provides API documentation"""
    return {
        "message": "Welcome to Live Win Probability API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "status": "/api/status"
    }

# ============ RUN SERVER ============
if __name__ == "__main__":
    logger.info("Starting Live Win Probability API Server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )