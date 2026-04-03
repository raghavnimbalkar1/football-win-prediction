#!/usr/bin/env python3
"""
Phase 2 API Testing Script
Demonstrates the live match state management workflow
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_api_status():
    """Test API status endpoint"""
    print_section("1. API Status Check")
    
    response = requests.get(f"{BASE_URL}/api/status")
    data = response.json()
    
    print(f"✓ Service: {data['service']}")
    print(f"✓ Version: {data['version']}")
    print(f"✓ Live Updates: {data['capabilities']['live_updates']}")
    print(f"\nAvailable Endpoints ({len(data['endpoints'])}):")
    for name, endpoint in data['endpoints'].items():
        print(f"  - {name}: {endpoint}")
    
    return response.status_code == 200

def test_initialize_match():
    """Test match initialization"""
    print_section("2. Initialize Live Match")
    
    payload = {
        "match_id": 1,
        "external_match_id": "sofascore_12345",
        "home_team": "Bayern Munich",
        "away_team": "Borussia Dortmund",
        "match_date": "2026-04-03T20:30:00"
    }
    
    print(f"Initializing: {payload['home_team']} vs {payload['away_team']}")
    print(f"Match ID: {payload['match_id']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/match/initialize", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Match initialized successfully!")
            print(f"  Home Team: {data['home_team']}")
            print(f"  Away Team: {data['away_team']}")
            print(f"  Status: {data['status']}")
            print(f"  Initial Score: {data['home_goals']}-{data['away_goals']}")
            print(f"\nInitial Predictions:")
            print(f"  Home Win:  {data['home_win_prob']*100:.1f}%")
            print(f"  Draw:      {data['draw_prob']*100:.1f}%")
            print(f"  Away Win:  {data['away_win_prob']*100:.1f}%")
            print(f"\nExpected Goals:")
            print(f"  Home: {data['current_home_xg']:.2f}")
            print(f"  Away: {data['current_away_xg']:.2f}")
            return True
        else:
            print(f"\n✗ Error: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        print("Note: Make sure Redis is running: redis-server")
        return False

def test_get_state(match_id=1):
    """Test getting match state"""
    print_section("3. Get Current Match State")
    
    try:
        response = requests.get(f"{BASE_URL}/api/match/{match_id}/state")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Match {match_id} State:")
            print(f"  Score: {data['home_goals']}-{data['away_goals']}")
            print(f"  Minute: {data['current_minute']}")
            print(f"  Status: {data['status']}")
            print(f"  Win Probs: {data['home_win_prob']:.1%} / {data['draw_prob']:.1%} / {data['away_win_prob']:.1%}")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def test_update_score(match_id=1):
    """Test score update"""
    print_section("4. Update Match Score")
    
    params = {
        "home_goals": 1,
        "away_goals": 0,
        "minute": 25,
        "second": 30
    }
    
    print(f"Updating score to {params['home_goals']}-{params['away_goals']} at minute {params['minute']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/match/{match_id}/score",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Score updated!")
            print(f"  New Score: {data['home_goals']}-{data['away_goals']}")
            print(f"  Minute: {data['current_minute']}:{data['current_second']}")
            print(f"  Updated Predictions:")
            print(f"    Home Win: {data['home_win_prob']*100:.1f}%")
            print(f"    Draw: {data['draw_prob']*100:.1f}%")
            print(f"    Away Win: {data['away_win_prob']*100:.1f}%")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def test_add_event(match_id=1):
    """Test adding match event"""
    print_section("5. Add Match Event (Goal)")
    
    payload = {
        "event_type": "goal",
        "team": "Bayern Munich",
        "player_name": "Robert Lewandowski",
        "minute": 35,
        "second": 15,
        "description": "Header from close range"
    }
    
    print(f"Event: {payload['event_type']} by {payload['player_name']}")
    print(f"Time: {payload['minute']}:{payload['second']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/match/{match_id}/event",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Event added!")
            print(f"  Total events: {len(data['events'])}")
            print(f"  Current score: {data['home_goals']}-{data['away_goals']}")
            print(f"  Last event: {data['events'][-1]['event_type']} - {data['events'][-1]['player_name']}")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def test_update_predictions(match_id=1):
    """Test prediction update"""
    print_section("6. Update Predictions")
    
    print("Recalculating predictions based on current match state...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/match/{match_id}/predictions")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Predictions updated!")
            print(f"  Updated at: minute {data['current_minute']}")
            print(f"  Current score: {data['home_goals']}-{data['away_goals']}")
            print(f"  New probabilities:")
            print(f"    Home Win: {data['home_win_prob']*100:.1f}%")
            print(f"    Draw: {data['draw_prob']*100:.1f}%")
            print(f"    Away Win: {data['away_win_prob']*100:.1f}%")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def test_get_summary(match_id=1):
    """Test match summary"""
    print_section("7. Get Match Summary (Quick View)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/match/{match_id}/summary")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Match Summary:")
            print(f"  Score: {data['home_goals']}-{data['away_goals']}")
            print(f"  Minute: {data['current_minute']}")
            print(f"  Status: {data['status']}")
            print(f"  Win Probs: {data['home_win_prob']:.1%} / {data['draw_prob']:.1%} / {data['away_win_prob']:.1%}")
            print(f"  xG: {data['home_xg']:.2f} - {data['away_xg']:.2f}")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def test_finish_match(match_id=1):
    """Test finishing match"""
    print_section("8. Finish Match")
    
    print("Marking match as completed...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/match/{match_id}/finish")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Match finished!")
            print(f"  Final Score: {data['home_goals']}-{data['away_goals']}")
            print(f"  Status: {data['status']}")
            print(f"  Final Minute: {data['current_minute']}")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  LIVE WIN PROBABILITY - PHASE 2 API TEST SUITE")
    print("="*60)
    
    tests = [
        ("API Status", test_api_status),
        ("Initialize Match", test_initialize_match),
        ("Get Current State", lambda: test_get_state(1)),
        ("Update Score", lambda: test_update_score(1)),
        ("Add Event", lambda: test_add_event(1)),
        ("Update Predictions", lambda: test_update_predictions(1)),
        ("Get Summary", lambda: test_get_summary(1)),
        ("Finish Match", lambda: test_finish_match(1)),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}  -  {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 2 is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check Redis installation and configuration.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
