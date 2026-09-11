#!/usr/bin/env python3
"""
Backend API Test Suite for BrandsXAI WhatsApp AI Feature
Tests all WhatsApp AI endpoints in SIMULATION mode
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://whatsapp-lead-hub-8.preview.emergentagent.com/api"
TEST_USER = "mukesh"
TEST_PASSWORD = "mukesh123"

# Test results tracking
test_results = []
access_token = None
conversation_id = None
first_message_timestamp = None

def log_test(test_name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    test_results.append(result)
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    print()

def test_auth_login():
    """Test 1: Authenticate as brand user"""
    global access_token
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            if access_token:
                log_test("AUTH: Login as brand user", True, f"Token received, user: {data.get('username')}")
                return True
            else:
                log_test("AUTH: Login as brand user", False, "No access_token in response")
                return False
        else:
            log_test("AUTH: Login as brand user", False, f"Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("AUTH: Login as brand user", False, f"Exception: {str(e)}")
        return False

def test_list_templates():
    """Test 2: GET /api/whatsapp/templates - expect >=6 templates"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/whatsapp/templates", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("templates", [])
            if len(templates) >= 6:
                log_test("GET /api/whatsapp/templates", True, f"Found {len(templates)} templates (expected >=6)")
                return True
            else:
                log_test("GET /api/whatsapp/templates", False, f"Only {len(templates)} templates found, expected >=6")
                return False
        else:
            log_test("GET /api/whatsapp/templates", False, f"Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("GET /api/whatsapp/templates", False, f"Exception: {str(e)}")
        return False

def test_create_conversation():
    """Test 3: POST /api/whatsapp/conversations - start conversation with template"""
    global conversation_id, first_message_timestamp
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "lead_name": "Rahul Sharma",
            "lead_phone": "919876543210",
            "campaign_name": "Diwali Offer 2026",
            "product_interest": "BrandX SUV X7",
            "template_name": "welcome_offer",
            "template_body_rendered": "Hi Rahul, thanks for your interest in the BrandX SUV X7! We have an exclusive Diwali offer for you. Our sales expert Amit will be happy to assist you.",
            "body_variables": ["Rahul", "BrandX SUV X7", "Amit"],
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/whatsapp/conversations", json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            conversation = data.get("conversation")
            message = data.get("message")
            
            if not conversation or not message:
                log_test("POST /api/whatsapp/conversations", False, "Missing conversation or message in response")
                return False
            
            conversation_id = conversation.get("id")
            first_message_timestamp = message.get("created_at")
            
            # Verify conversation fields
            checks = []
            checks.append(("conversation.id exists", bool(conversation_id)))
            checks.append(("conversation.lead_name", conversation.get("lead_name") == "Rahul Sharma"))
            checks.append(("conversation.stage", conversation.get("stage") == "Contacted"))
            checks.append(("message.sender_type", message.get("sender_type") == "bot"))
            checks.append(("message.msg_type", message.get("msg_type") == "template"))
            checks.append(("message.simulated", message.get("simulated") == True))
            checks.append(("message.direction", message.get("direction") == "outbound"))
            
            failed_checks = [c[0] for c in checks if not c[1]]
            
            if not failed_checks:
                log_test("POST /api/whatsapp/conversations", True, f"Conversation created: {conversation_id}, simulated=true")
                return True
            else:
                log_test("POST /api/whatsapp/conversations", False, f"Failed checks: {', '.join(failed_checks)}")
                return False
        else:
            log_test("POST /api/whatsapp/conversations", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("POST /api/whatsapp/conversations", False, f"Exception: {str(e)}")
        return False

def test_list_conversations():
    """Test 4: GET /api/whatsapp/conversations - verify new conversation present"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/whatsapp/conversations", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", [])
            live_mode = data.get("live_mode", True)
            
            # Find our conversation
            found = any(c.get("id") == conversation_id for c in conversations)
            
            if found and live_mode == False:
                log_test("GET /api/whatsapp/conversations", True, f"Found conversation {conversation_id}, live_mode=false")
                return True
            elif not found:
                log_test("GET /api/whatsapp/conversations", False, f"Conversation {conversation_id} not found in list")
                return False
            else:
                log_test("GET /api/whatsapp/conversations", False, f"live_mode={live_mode}, expected false")
                return False
        else:
            log_test("GET /api/whatsapp/conversations", False, f"Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("GET /api/whatsapp/conversations", False, f"Exception: {str(e)}")
        return False

def test_get_conversation():
    """Test 5: GET /api/whatsapp/conversations/{id} - get conversation details"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/whatsapp/conversations/{conversation_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            conversation = data.get("conversation")
            messages = data.get("messages", [])
            
            if conversation and len(messages) >= 1:
                log_test(f"GET /api/whatsapp/conversations/{conversation_id}", True, f"Retrieved conversation with {len(messages)} message(s)")
                return True
            else:
                log_test(f"GET /api/whatsapp/conversations/{conversation_id}", False, "Missing conversation or messages")
                return False
        else:
            log_test(f"GET /api/whatsapp/conversations/{conversation_id}", False, f"Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(f"GET /api/whatsapp/conversations/{conversation_id}", False, f"Exception: {str(e)}")
        return False

def test_send_human_message():
    """Test 6: POST /api/whatsapp/conversations/{id}/messages - send human text"""
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "content": "Sure, happy to help! Let me know if you have any questions about the SUV X7.",
            "msg_type": "text"
        }
        
        response = requests.post(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/messages",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("message")
            
            if not message:
                log_test("POST /api/whatsapp/conversations/{id}/messages", False, "No message in response")
                return False
            
            checks = []
            checks.append(("direction", message.get("direction") == "outbound"))
            checks.append(("sender_type", message.get("sender_type") == "human"))
            checks.append(("msg_type", message.get("msg_type") == "text"))
            checks.append(("simulated", message.get("simulated") == True))
            
            failed_checks = [c[0] for c in checks if not c[1]]
            
            if not failed_checks:
                log_test("POST /api/whatsapp/conversations/{id}/messages", True, "Human message sent, simulated=true")
                return True
            else:
                log_test("POST /api/whatsapp/conversations/{id}/messages", False, f"Failed checks: {', '.join(failed_checks)}")
                return False
        else:
            log_test("POST /api/whatsapp/conversations/{id}/messages", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("POST /api/whatsapp/conversations/{id}/messages", False, f"Exception: {str(e)}")
        return False

def test_simulate_inbound():
    """Test 7: POST /api/whatsapp/conversations/{id}/simulate-inbound - simulate customer reply"""
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "content": "Yes, tell me more about the offer. What's the price and what features does it have?"
        }
        
        response = requests.post(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/simulate-inbound",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("message")
            
            if not message:
                log_test("POST /api/whatsapp/conversations/{id}/simulate-inbound", False, "No message in response")
                return False
            
            checks = []
            checks.append(("direction", message.get("direction") == "inbound"))
            checks.append(("sender_type", message.get("sender_type") == "customer"))
            checks.append(("simulated", message.get("simulated") == True))
            
            failed_checks = [c[0] for c in checks if not c[1]]
            
            if not failed_checks:
                log_test("POST /api/whatsapp/conversations/{id}/simulate-inbound", True, "Inbound customer message simulated")
                return True
            else:
                log_test("POST /api/whatsapp/conversations/{id}/simulate-inbound", False, f"Failed checks: {', '.join(failed_checks)}")
                return False
        else:
            log_test("POST /api/whatsapp/conversations/{id}/simulate-inbound", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("POST /api/whatsapp/conversations/{id}/simulate-inbound", False, f"Exception: {str(e)}")
        return False

def test_poll_messages():
    """Test 8: GET /api/whatsapp/conversations/{id}/messages?after= - poll for new messages"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        # Use the first message timestamp to get only newer messages
        response = requests.get(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/messages?after={first_message_timestamp}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            
            # Should have at least 2 messages (human text + simulated inbound)
            if len(messages) >= 2:
                log_test("GET /api/whatsapp/conversations/{id}/messages?after=", True, f"Retrieved {len(messages)} newer messages")
                return True
            else:
                log_test("GET /api/whatsapp/conversations/{id}/messages?after=", False, f"Expected >=2 messages, got {len(messages)}")
                return False
        else:
            log_test("GET /api/whatsapp/conversations/{id}/messages?after=", False, f"Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("GET /api/whatsapp/conversations/{id}/messages?after=", False, f"Exception: {str(e)}")
        return False

def test_ai_suggestions():
    """Test 9: POST /api/whatsapp/conversations/{id}/suggestions - get AI suggestions with creative_ideas"""
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        response = requests.post(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/suggestions",
            headers=headers,
            timeout=30  # Claude may take a few seconds
        )
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get("suggestions", [])
            creative_ideas = data.get("creative_ideas", [])
            temperature = data.get("temperature")
            intent = data.get("intent")
            
            checks = []
            checks.append(("suggestions count", len(suggestions) >= 2))  # Expect about 3
            checks.append(("creative_ideas exists", creative_ideas is not None))
            checks.append(("creative_ideas count", len(creative_ideas) >= 2))  # Expect 2-3
            checks.append(("temperature", temperature in ["hot", "warm", "cold"]))
            checks.append(("intent exists", bool(intent)))
            
            failed_checks = [c[0] for c in checks if not c[1]]
            
            if not failed_checks:
                log_test("POST /api/whatsapp/conversations/{id}/suggestions", True, 
                        f"Got {len(suggestions)} suggestions, {len(creative_ideas)} creative_ideas, temperature={temperature}, intent={intent[:50]}...")
                print(f"   Creative Ideas: {creative_ideas}")
                print(f"   Suggestions: {[s[:60]+'...' if len(s)>60 else s for s in suggestions]}")
                return True
            else:
                log_test("POST /api/whatsapp/conversations/{id}/suggestions", False, 
                        f"Failed checks: {', '.join(failed_checks)}. Data: {json.dumps(data)[:300]}")
                return False
        else:
            log_test("POST /api/whatsapp/conversations/{id}/suggestions", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("POST /api/whatsapp/conversations/{id}/suggestions", False, f"Exception: {str(e)}")
        return False

def test_draft_from_idea():
    """Test 10: POST /api/whatsapp/conversations/{id}/draft-from-idea - draft message from creative idea"""
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "idea": "invite to weekend test-drive event"
        }
        
        response = requests.post(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/draft-from-idea",
            json=payload,
            headers=headers,
            timeout=30  # Claude may take a few seconds
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("message")
            
            if message and len(message) > 10:  # Should be a non-empty message
                log_test("POST /api/whatsapp/conversations/{id}/draft-from-idea", True, 
                        f"Drafted message: {message[:100]}{'...' if len(message)>100 else ''}")
                return True
            else:
                log_test("POST /api/whatsapp/conversations/{id}/draft-from-idea", False, 
                        f"Message is empty or too short. Data: {json.dumps(data)}")
                return False
        else:
            log_test("POST /api/whatsapp/conversations/{id}/draft-from-idea", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("POST /api/whatsapp/conversations/{id}/draft-from-idea", False, f"Exception: {str(e)}")
        return False

def test_ai_summary():
    """Test 11: GET /api/whatsapp/conversations/{id}/summary - get AI summary"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/summary",
            headers=headers,
            timeout=30  # Claude may take a few seconds
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary")
            next_step = data.get("next_step")
            
            if summary and next_step:
                log_test("GET /api/whatsapp/conversations/{id}/summary", True, 
                        f"Summary: {summary[:80]}... Next step: {next_step[:60]}...")
                return True
            else:
                log_test("GET /api/whatsapp/conversations/{id}/summary", False, 
                        f"Missing summary or next_step. Data: {json.dumps(data)}")
                return False
        else:
            log_test("GET /api/whatsapp/conversations/{id}/summary", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("GET /api/whatsapp/conversations/{id}/summary", False, f"Exception: {str(e)}")
        return False

def test_book_appointment():
    """Test 12: POST /api/whatsapp/conversations/{id}/appointment - book showroom visit"""
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "date": "2026-09-20",
            "time": "15:30",
            "notes": "test drive for SUV X7"
        }
        
        response = requests.post(
            f"{BASE_URL}/whatsapp/conversations/{conversation_id}/appointment",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            appointment = data.get("appointment")
            message = data.get("message")
            
            if not appointment or not message:
                log_test("POST /api/whatsapp/conversations/{id}/appointment", False, "Missing appointment or message")
                return False
            
            # Verify appointment fields
            checks = []
            checks.append(("appointment.date", appointment.get("date") == "2026-09-20"))
            checks.append(("appointment.time", appointment.get("time") == "15:30"))
            checks.append(("appointment.status", appointment.get("status") == "scheduled"))
            checks.append(("message.simulated", message.get("simulated") == True))
            
            failed_checks = [c[0] for c in checks if not c[1]]
            
            if not failed_checks:
                # Now verify the conversation stage changed to "Visit Booked"
                headers_get = {"Authorization": f"Bearer {access_token}"}
                conv_response = requests.get(
                    f"{BASE_URL}/whatsapp/conversations/{conversation_id}",
                    headers=headers_get,
                    timeout=10
                )
                
                if conv_response.status_code == 200:
                    conv_data = conv_response.json()
                    stage = conv_data.get("conversation", {}).get("stage")
                    
                    if stage == "Visit Booked":
                        log_test("POST /api/whatsapp/conversations/{id}/appointment", True, 
                                f"Appointment booked, stage changed to 'Visit Booked'")
                        return True
                    else:
                        log_test("POST /api/whatsapp/conversations/{id}/appointment", False, 
                                f"Stage is '{stage}', expected 'Visit Booked'")
                        return False
                else:
                    log_test("POST /api/whatsapp/conversations/{id}/appointment", False, 
                            f"Failed to verify stage change: {conv_response.status_code}")
                    return False
            else:
                log_test("POST /api/whatsapp/conversations/{id}/appointment", False, 
                        f"Failed checks: {', '.join(failed_checks)}")
                return False
        else:
            log_test("POST /api/whatsapp/conversations/{id}/appointment", False, f"Status {response.status_code}: {response.text[:300]}")
            return False
    except Exception as e:
        log_test("POST /api/whatsapp/conversations/{id}/appointment", False, f"Exception: {str(e)}")
        return False

def test_webhook_verify_success():
    """Test 13a: GET /api/whatsapp/webhook - verify with correct token"""
    try:
        # No auth header for webhook
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "brandsxai_wa_verify_7bK9mQ2xP4",
            "hub.challenge": "12345"
        }
        
        response = requests.get(f"{BASE_URL}/whatsapp/webhook", params=params, timeout=10)
        
        if response.status_code == 200 and response.text == "12345":
            log_test("GET /api/whatsapp/webhook (correct token)", True, "Returned challenge: 12345")
            return True
        else:
            log_test("GET /api/whatsapp/webhook (correct token)", False, 
                    f"Status {response.status_code}, body: {response.text[:100]}")
            return False
    except Exception as e:
        log_test("GET /api/whatsapp/webhook (correct token)", False, f"Exception: {str(e)}")
        return False

def test_webhook_verify_fail():
    """Test 13b: GET /api/whatsapp/webhook - verify with wrong token"""
    try:
        # No auth header for webhook
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token_12345",
            "hub.challenge": "12345"
        }
        
        response = requests.get(f"{BASE_URL}/whatsapp/webhook", params=params, timeout=10)
        
        if response.status_code == 403:
            log_test("GET /api/whatsapp/webhook (wrong token)", True, "Correctly rejected with 403")
            return True
        else:
            log_test("GET /api/whatsapp/webhook (wrong token)", False, 
                    f"Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        log_test("GET /api/whatsapp/webhook (wrong token)", False, f"Exception: {str(e)}")
        return False

def test_auth_guard():
    """Test 14: Auth guard - calling endpoint without token should return 403"""
    try:
        # No auth header
        response = requests.get(f"{BASE_URL}/whatsapp/conversations", timeout=10)
        
        if response.status_code == 403:
            log_test("Auth guard (no token)", True, "Correctly rejected with 403")
            return True
        else:
            log_test("Auth guard (no token)", False, f"Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Auth guard (no token)", False, f"Exception: {str(e)}")
        return False

def test_auth_login_testuser():
    """Test 15: Authenticate as testuser/test123"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "testuser", "password": "test123"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            features = data.get("features", [])
            
            # Check if WhatsApp AI feature (id=3) is present
            has_whatsapp_ai = any(f.get("id") == 3 for f in features)
            
            if token and has_whatsapp_ai:
                log_test("AUTH: Login as testuser/test123", True, 
                        f"Token received, WhatsApp AI feature present (feature id 3)")
                return True
            elif not token:
                log_test("AUTH: Login as testuser/test123", False, "No access_token in response")
                return False
            else:
                log_test("AUTH: Login as testuser/test123", False, 
                        f"WhatsApp AI feature (id=3) not found in features: {[f.get('id') for f in features]}")
                return False
        else:
            log_test("AUTH: Login as testuser/test123", False, f"Status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("AUTH: Login as testuser/test123", False, f"Exception: {str(e)}")
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    if failed > 0:
        print("FAILED TESTS:")
        print("-" * 80)
        for r in test_results:
            if not r["passed"]:
                print(f"❌ {r['test']}")
                print(f"   {r['details']}\n")
    
    print("="*80)

def main():
    """Run all tests"""
    print("="*80)
    print("BrandsXAI WhatsApp AI Backend Test Suite")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("="*80 + "\n")
    
    # Run tests in sequence
    if not test_auth_login():
        print("\n❌ Authentication failed. Cannot proceed with other tests.\n")
        print_summary()
        return
    
    test_list_templates()
    test_create_conversation()
    
    if conversation_id:
        test_list_conversations()
        test_get_conversation()
        test_send_human_message()
        test_simulate_inbound()
        test_poll_messages()
        test_ai_suggestions()
        test_draft_from_idea()
        test_ai_summary()
        test_book_appointment()
    else:
        print("\n❌ Conversation creation failed. Skipping conversation-dependent tests.\n")
    
    test_webhook_verify_success()
    test_webhook_verify_fail()
    test_auth_guard()
    test_auth_login_testuser()
    
    print_summary()
    
    # Save results to file
    with open("/app/test_results_whatsapp.json", "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"\nDetailed results saved to: /app/test_results_whatsapp.json\n")

if __name__ == "__main__":
    main()
