"""
FastAPI Backend Server for Live Win Probability Prediction Engine
"""
from fastapi import FastAPI, HTTPException, WebSocket, Query, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import asyncio
import json
from datetime import datetime
from typing import Optional, Set, Dict
from contextlib import asynccontextmanager

# Import prediction engine and services
from predictive_engine import predict_match
from services import get_state_service
from services.simulation_service import get_live_simulation_service
from models import LiveMatchState, MatchEvent, EventType
from schemas import InitializeMatchRequest, UpdateScoreRequest, AddEventRequest, UpdatePredictionRequest

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

# ============ WEBSOCKET MANAGER ============

class ConnectionManager:
    """Manages WebSocket connections for live updates"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, match_id: int, websocket: WebSocket) -> None:
        """Register a new WebSocket connection"""
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = set()
        self.active_connections[match_id].add(websocket)
        logger.info(f"WebSocket connected to match {match_id}")
    
    def disconnect(self, match_id: int, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection"""
        if match_id in self.active_connections:
            self.active_connections[match_id].discard(websocket)
            logger.info(f"WebSocket disconnected from match {match_id}")
    
    async def broadcast(self, match_id: int, message: dict) -> None:
        """Send message to all connected clients for a match"""
        if match_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[match_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[match_id].discard(conn)
    
    def get_active_matches(self) -> list:
        """Get list of matches with active connections"""
        return [m for m in self.active_connections if self.active_connections[m]]


manager = ConnectionManager()

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
            "live_updates": True,  # Now True with state service!
            "simulation": False,    # Will be True in Phase 3
            "websocket": False      # Will be True in Phase 3
        },
        "endpoints": {
            "health": "/health",
            "prediction": "/api/predict/{home_team}/{away_team}",
            "comparison": "/api/compare/{home1}/{away1}/{home2}/{away2}",
            "live_match_init": "POST /api/match/initialize",
            "live_match_state": "GET /api/match/{match_id}/state",
            "live_match_score": "POST /api/match/{match_id}/score",
            "live_match_event": "POST /api/match/{match_id}/event",
            "live_match_predictions": "POST /api/match/{match_id}/predictions",
            "live_match_finish": "POST /api/match/{match_id}/finish",
            "live_match_summary": "GET /api/match/{match_id}/summary",
            "live_match_history": "GET /api/match/{match_id}/history",
            "status": "/api/status",
            "websocket": "WS /ws/match/{match_id}"
        },
        "timestamp": datetime.now().isoformat()
    }

# ============ WEBSOCKET ENDPOINTS ============

@app.websocket("/ws/match/{match_id}")
async def websocket_endpoint(websocket: WebSocket, match_id: int):
    """
    WebSocket endpoint for live match probability updates
    
    Subscribes a client to receive real-time probability updates as match events occur.
    
    Args:
        websocket: WebSocket connection
        match_id: ID of the match to subscribe to
    """
    await manager.connect(match_id, websocket)
    
    try:
        # Send initial state when connected
        service = get_state_service()
        state = service.get_current_state(match_id)
        if state:
            await websocket.send_json({
                "type": "connected",
                "match_id": match_id,
                "message": "Connected to live match updates",
                "current_state": state.to_dict() if hasattr(state, 'to_dict') else {}
            })
        
        # Keep connection open, listen for any messages
        while True:
            # Receive messages (if client sends any)
            message = await websocket.receive_text()
            logger.debug(f"Received WebSocket message from match {match_id}: {message}")
            
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)
        logger.info(f"WebSocket disconnected from match {match_id}")
    except Exception as e:
        logger.error(f"WebSocket error for match {match_id}: {e}")
        manager.disconnect(match_id, websocket)

# ============ LIVE MATCH ENDPOINTS ============

@app.post("/api/match/initialize")
async def initialize_match(request: InitializeMatchRequest):
    """
    Initialize a new live match
    
    Args:
        request: InitializeMatchRequest with match details
    
    Returns:
        Initialized LiveMatchState
    """
    try:
        service = get_state_service()
        state = service.initialize_match(
            match_id=request.match_id,
            external_match_id=request.external_match_id,
            home_team=request.home_team,
            away_team=request.away_team,
            match_date=datetime.fromisoformat(request.match_date)
        )
        
        if state is None:
            raise HTTPException(status_code=400, detail="Failed to initialize match")
        
        logger.info(f"Match {request.match_id} initialized: {request.home_team} vs {request.away_team}")
        return state.to_dict()
        
    except Exception as e:
        logger.error(f"Error initializing match: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/match/{match_id}/state")
async def get_match_state(match_id: int):
    """
    Get current state of a live match
    
    Args:
        match_id: Match ID
    
    Returns:
        Current LiveMatchState
    """
    try:
        service = get_state_service()
        state = service.get_current_state(match_id)
        
        if state is None:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        return state.to_dict()
        
    except Exception as e:
        logger.error(f"Error getting match state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match/{match_id}/score")
async def update_match_score(match_id: int, request: UpdateScoreRequest):
    """
    Update match score and recalculate predictions
    
    Args:
        match_id: Match ID
        request: UpdateScoreRequest with score details
    
    Returns:
        Updated LiveMatchState
    """
    try:
        service = get_state_service()
        state = service.update_score(
            match_id=match_id,
            home_goals=request.home_goals,
            away_goals=request.away_goals,
            current_minute=request.minute,
            current_second=request.second
        )
        
        if state is None:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        logger.info(f"Score updated for match {match_id}: {request.home_goals}-{request.away_goals}")
        
        # Run Monte Carlo simulation and update predictions
        sim_service = get_live_simulation_service()
        sim_result = sim_service.simulate_and_update(match_id)
        
        # Broadcast updated predictions to all connected clients
        if sim_result:
            await manager.broadcast(match_id, {
                "type": "score_update",
                "match_id": match_id,
                "home_goals": request.home_goals,
                "away_goals": request.away_goals,
                "minute": request.minute,
                "second": request.second,
                "predictions": sim_result.get("predictions", {})
            })
        
        return state.to_dict()
        
    except Exception as e:
        logger.error(f"Error updating score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match/{match_id}/event")
async def add_match_event(match_id: int, request: AddEventRequest):
    """
    Add an event to the match (goal, card, substitution, etc.)
    
    Args:
        match_id: Match ID
        request: AddEventRequest with event details
    
    Returns:
        Updated LiveMatchState
    """
    try:
        service = get_state_service()
        
        # Create event
        event = MatchEvent(
            event_type=EventType(request.event_type),
            team=request.team,
            player_name=request.player_name,
            minute=request.minute,
            second=request.second,
            description=request.description
        )
        
        # Add event to match
        state = service.add_event(match_id, event)
        
        if state is None:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        logger.info(f"Event added to match {match_id}: {request.event_type} by {request.player_name}")
        
        # Trigger simulation and broadcast for goals (events that change score)
        if request.event_type in ["goal", "own_goal"]:
            sim_service = get_live_simulation_service()
            sim_result = sim_service.simulate_and_update(match_id)
            
            if sim_result:
                # Get current state for score information
                current_state = service.get_current_state(match_id)
                await manager.broadcast(match_id, {
                    "type": "event",
                    "match_id": match_id,
                    "event": {
                        "type": request.event_type,
                        "player": request.player_name,
                        "team": request.team,
                        "minute": request.minute,
                        "description": request.description
                    },
                    "home_goals": current_state.home_goals if current_state else 0,
                    "away_goals": current_state.away_goals if current_state else 0,
                    "predictions": sim_result.get("predictions", {})
                })
                return state.to_dict()
        else:
            # Broadcast other events without triggering simulation
            await manager.broadcast(match_id, {
                "type": "event",
                "match_id": match_id,
                "event": {
                    "type": request.event_type,
                    "player": request.player_name,
                    "team": request.team,
                    "minute": request.minute,
                    "description": request.description
                }
            })
        
        return state.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match/{match_id}/predictions")
async def update_match_predictions(match_id: int):
    """
    Recalculate predictions for live match
    
    Args:
        match_id: Match ID
    
    Returns:
        Updated LiveMatchState with new predictions
    """
    try:
        service = get_state_service()
        state = service.get_current_state(match_id)
        
        if state is None:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        # Recalculate predictions using the engine
        from predictive_engine import predict_match
        predictions = predict_match(state.home_team, state.away_team)
        
        if "error" in predictions:
            raise HTTPException(status_code=400, detail=predictions["error"])
        
        # Update state with new predictions
        updated_state = service.update_predictions(match_id, predictions)
        
        if updated_state is None:
            raise HTTPException(status_code=500, detail="Failed to update predictions")
        
        logger.info(f"Predictions updated for match {match_id}")
        
        # Broadcast updated predictions to all connected clients
        await manager.broadcast(match_id, {
            "type": "predictions_update",
            "match_id": match_id,
            "predictions": predictions
        })
        
        return updated_state.to_dict()
        
    except Exception as e:
        logger.error(f"Error updating predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match/{match_id}/finish")
async def finish_match(match_id: int):
    """
    Mark match as finished
    
    Args:
        match_id: Match ID
    
    Returns:
        Final LiveMatchState
    """
    try:
        service = get_state_service()
        state = service.finish_match(match_id)
        
        if state is None:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        logger.info(f"Match {match_id} finished: {state.home_goals}-{state.away_goals}")
        return state.to_dict()
        
    except Exception as e:
        logger.error(f"Error finishing match: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/match/{match_id}/summary")
async def get_match_summary(match_id: int):
    """
    Get quick summary of match state
    
    Returns:
        Lightweight match summary
    """
    try:
        service = get_state_service()
        state = service.get_current_state(match_id)
        
        if state is None:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        return state.get_summary()
        
    except Exception as e:
        logger.error(f"Error getting match summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/match/{match_id}/history")
async def get_prediction_history(match_id: int):
    """
    Get historical predictions for a match (by minute)
    
    Args:
        match_id: Match ID
    
    Returns:
        List of prediction snapshots
    """
    try:
        service = get_state_service()
        history = service.get_prediction_history(match_id)
        
        if not history:
            logger.info(f"No prediction history found for match {match_id}")
        
        return {"match_id": match_id, "predictions": history}
        
    except Exception as e:
        logger.error(f"Error getting prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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