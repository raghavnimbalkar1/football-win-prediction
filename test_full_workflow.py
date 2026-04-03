#!/usr/bin/env python3
"""
Full workflow test for Live Win Probability System
Tests: Match initialization -> Score update -> Simulation -> WebSocket broadcast
"""
import requests
import json
import asyncio
import websockets
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def test_match_initialization():
    """Test initializing a match"""
    print("\n[1] Testing Match Initialization...")
    
    # Use a unique match ID to avoid conflicts
    import random
    match_id = random.randint(1000, 9999)
    
    payload = {
        "match_id": match_id,
        "external_match_id": f"ext_{match_id}",
        "home_team": "Bayern Munich",
        "away_team": "Dortmund",
        "match_date": datetime.now().isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/api/match/initialize", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: SUCCESS")
        print(f"   Match ID: {data.get('match_id')}")
        print(f"   State: {data.get('state')}")
        print(f"   Initial Predictions: {data.get('last_predictions')}")
        return data
    else:
        print(f"   Status: FAILED ({response.status_code})")
        print(f"   Error: {response.text}")
        return None

def test_score_update(match_id):
    """Test updating match score with simulation"""
    print("\n[2] Testing Score Update with Simulation...")
    
    payload = {
        "home_goals": 1,
        "away_goals": 0,
        "minute": 25,
        "second": 30
    }
    
    response = requests.post(f"{BASE_URL}/api/match/{match_id}/score", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: SUCCESS")
        print(f"   Current Score: {data.get('home_goals')}-{data.get('away_goals')}")
        print(f"   Minute: {data.get('current_minute')}")
        
        if data.get('last_predictions'):
            preds = data.get('last_predictions')
            print(f"   Updated Probabilities:")
            print(f"     - Home Win: {preds.get('home_win_prob', 'N/A')}")
            print(f"     - Draw: {preds.get('draw_prob', 'N/A')}")
            print(f"     - Away Win: {preds.get('away_win_prob', 'N/A')}")
        
        return data
    else:
        print(f"   Status: FAILED ({response.status_code})")
        print(f"   Error: {response.text}")
        return None

def test_get_state(match_id):
    """Test getting match state"""
    print("\n[3] Testing Get Match State...")
    
    response = requests.get(f"{BASE_URL}/api/match/{match_id}/state")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: SUCCESS")
        print(f"   State: {data.get('state')}")
        print(f"   Score: {data.get('home_goals')}-{data.get('away_goals')}")
        return data
    else:
        print(f"   Status: FAILED ({response.status_code})")
        print(f"   Error: {response.text}")
        return None

def test_add_event(match_id):
    """Test adding a match event"""
    print("\n[4] Testing Add Match Event (Goal)...")
    
    payload = {
        "event_type": "goal",
        "team": "Dortmund",
        "player_name": "Marco Reus",
        "minute": 42,
        "second": 15,
        "description": "Equalizer goal"
    }
    
    response = requests.post(f"{BASE_URL}/api/match/{match_id}/event", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: SUCCESS")
        print(f"   Current Score: {data.get('home_goals')}-{data.get('away_goals')}")
        print(f"   Events Count: {len(data.get('events', []))}")
        return data
    else:
        print(f"   Status: FAILED ({response.status_code})")
        print(f"   Error: {response.text}")
        return None

def test_predictions_update(match_id):
    """Test manual prediction update"""
    print("\n[5] Testing Predictions Update...")
    
    response = requests.post(f"{BASE_URL}/api/match/{match_id}/predictions")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: SUCCESS")
        
        if data.get('last_predictions'):
            preds = data.get('last_predictions')
            print(f"   Recalculated Probabilities:")
            print(f"     - Home Win: {preds.get('home_win_prob', 'N/A')}")
            print(f"     - Draw: {preds.get('draw_prob', 'N/A')}")
            print(f"     - Away Win: {preds.get('away_win_prob', 'N/A')}")
        
        return data
    else:
        print(f"   Status: FAILED ({response.status_code})")
        print(f"   Error: {response.text}")
        return None

async def test_websocket_connection(match_id):
    """Test WebSocket connection and message receiving"""
    print("\n[6] Testing WebSocket Connection...")
    
    try:
        uri = f"{WS_URL}/ws/match/{match_id}"
        print(f"   Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print(f"   Status: CONNECTED")
            
            # Receive connection confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(message)
            print(f"   Received: {data.get('type')} message")
            print(f"   Message: {data.get('message')}")
            
            # Try to receive another message (if any pending)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2)
                data = json.loads(message)
                print(f"   Additional Message: {data.get('type')}")
            except asyncio.TimeoutError:
                print(f"   No additional messages (timeout)")
            
            return True
    except asyncio.TimeoutError:
        print(f"   Status: FAILED - Connection timeout")
        return False
    except Exception as e:
        print(f"   Status: FAILED - {str(e)}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("LIVE WIN PROBABILITY SYSTEM - FULL WORKFLOW TEST")
    print("="*60)
    
    # Test initialization
    match_data = test_match_initialization()
    if not match_data:
        print("\nExiting: Match initialization failed")
        return
    
    match_id = match_data.get('match_id')
    
    # Test get state
    test_get_state(match_id)
    
    # Test score update
    test_score_update(match_id)
    
    # Test add event
    time.sleep(1)  # Brief delay
    test_add_event(match_id)
    
    # Test predictions update
    time.sleep(1)  # Brief delay
    test_predictions_update(match_id)
    
    # Test WebSocket
    time.sleep(1)  # Brief delay
    asyncio.run(test_websocket_connection(match_id))
    
    print("\n" + "="*60)
    print("WORKFLOW TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
