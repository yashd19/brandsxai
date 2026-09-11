#!/usr/bin/env python3
"""
Backend Regression Test for WhatsApp AI "One Thread Per Phone Number" Fix
Tests the deduplication logic in POST /api/whatsapp/conversations

Context: POST /api/whatsapp/conversations must NOT create duplicate threads for the same phone.
If a conversation already exists for that brand+phone, it should REUSE it (append the template 
message, update preview) and return "reused": true. It also validates inputs.

Tests:
1. DEDUPE: Verify existing conversation is reused (Rahul Sharma 919876543210)
2. NEW THREAD: Verify new phone creates new thread, then reuses on second POST
3. VALIDATION: Test edge cases (empty name, short phone, missing template)
4. AUTO-OPEN vs MANUAL: Verify voice_agent conversation is reused by manual start
5. FINAL: Verify no duplicate lead_phone values in all conversations
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://whatsapp-lead-hub-8.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

# Test credentials
USERNAME = "testuser"
PASSWORD = "test123"

# Global token storage
auth_token = None

def log_test(step, description):
    """Log test step"""
    print(f"\n{'='*80}")
    print(f"TEST {step}: {description}")
    print(f"{'='*80}")

def log_result(success, message, details=None):
    """Log test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {json.dumps(details, indent=2)}")
    return success

def login():
    """Login and get JWT token"""
    global auth_token
    log_test("0", "Login as testuser/test123")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get('access_token') or data.get('token')
        log_result(True, "Login successful", {"token_length": len(auth_token) if auth_token else 0})
        return True
    else:
        log_result(False, f"Login failed: {response.status_code}", response.text)
        return False

def get_headers(include_auth=True):
    """Get request headers"""
    headers = {"Content-Type": "application/json"}
    if include_auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    return headers

# ============================================================================
# TEST 1: DEDUPE - Verify existing conversation is reused
# ============================================================================

def test_1a_get_initial_conversations():
    """Test 1a: GET /api/whatsapp/conversations - note current count and check for Rahul"""
    log_test("1a", "GET /api/whatsapp/conversations (check initial state)")
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        conversations = data.get('conversations', [])
        count = len(conversations)
        
        # Check if Rahul Sharma (919876543210) exists
        rahul_conv = None
        for conv in conversations:
            if conv.get('lead_phone') == '919876543210':
                rahul_conv = conv
                break
        
        if rahul_conv:
            log_result(True, f"Initial state: {count} conversations, Rahul Sharma exists", {
                "total_count": count,
                "rahul_conversation_id": rahul_conv.get('id'),
                "rahul_lead_name": rahul_conv.get('lead_name'),
                "rahul_lead_phone": rahul_conv.get('lead_phone')
            })
            return count, rahul_conv.get('id')
        else:
            log_result(True, f"Initial state: {count} conversations, Rahul Sharma NOT found", {
                "total_count": count,
                "note": "Rahul conversation may not exist yet - will be created in next test"
            })
            return count, None
    else:
        log_result(False, f"Get conversations failed: {response.status_code}", response.text)
        return None, None

def test_1b_post_duplicate_rahul(expected_conv_id):
    """Test 1b: POST with Rahul's phone - expect reused=true"""
    log_test("1b", "POST /api/whatsapp/conversations (Rahul Sharma - expect reused=true)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Rahul Sharma",
            "lead_phone": "919876543210",
            "template_name": "welcome_offer",
            "template_body_rendered": "Hi again Rahul!",
            "body_variables": ["Rahul", "BrandX X7", "Amit"],
            "language": "en"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        reused = data.get('reused')
        conv_id = data.get('conversation', {}).get('id')
        message = data.get('message', {})
        
        # If expected_conv_id is None, this is the first time creating Rahul's conversation
        if expected_conv_id is None:
            if reused == False and conv_id:
                log_result(True, "First Rahul conversation created (reused=false)", {
                    "reused": reused,
                    "conversation_id": conv_id,
                    "message_content": message.get('content')
                })
                return True, conv_id
            else:
                log_result(False, "Expected reused=false for first creation", {
                    "reused": reused,
                    "conversation_id": conv_id
                })
                return False, conv_id
        else:
            # Expected to reuse existing conversation
            if reused == True and conv_id == expected_conv_id:
                log_result(True, "Conversation reused correctly", {
                    "reused": reused,
                    "conversation_id": conv_id,
                    "expected_id": expected_conv_id,
                    "message_content": message.get('content')
                })
                return True, conv_id
            else:
                log_result(False, "Conversation NOT reused or wrong ID", {
                    "reused": reused,
                    "conversation_id": conv_id,
                    "expected_id": expected_conv_id
                })
                return False, conv_id
    else:
        log_result(False, f"POST conversation failed: {response.status_code}", response.text)
        return False, None

def test_1c_verify_count_unchanged(initial_count):
    """Test 1c: GET conversations again - verify count unchanged"""
    log_test("1c", "GET /api/whatsapp/conversations (verify count unchanged)")
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        conversations = data.get('conversations', [])
        new_count = len(conversations)
        
        # Count conversations with Rahul's phone
        rahul_convs = [c for c in conversations if c.get('lead_phone') == '919876543210']
        rahul_count = len(rahul_convs)
        
        if rahul_count == 1:
            log_result(True, f"Exactly ONE conversation for Rahul's phone", {
                "total_conversations": new_count,
                "rahul_conversations": rahul_count,
                "rahul_conversation_id": rahul_convs[0].get('id')
            })
            return True, rahul_convs[0].get('id')
        else:
            log_result(False, f"Expected 1 conversation for Rahul, found {rahul_count}", {
                "total_conversations": new_count,
                "rahul_conversations": rahul_count
            })
            return False, None
    else:
        log_result(False, f"Get conversations failed: {response.status_code}", response.text)
        return False, None

def test_1d_verify_message_appended(conv_id):
    """Test 1d: GET conversation/{id} - verify new message appended"""
    log_test("1d", f"GET /api/whatsapp/conversations/{conv_id} (verify message appended)")
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations/{conv_id}",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get('messages', [])
        
        # Look for the "Hi again Rahul!" message
        hi_again_msg = None
        for msg in messages:
            if "Hi again Rahul" in msg.get('content', ''):
                hi_again_msg = msg
                break
        
        if hi_again_msg:
            log_result(True, "New template message appended to conversation", {
                "total_messages": len(messages),
                "new_message_content": hi_again_msg.get('content'),
                "message_type": hi_again_msg.get('msg_type'),
                "sender_type": hi_again_msg.get('sender_type')
            })
            return True
        else:
            log_result(False, "New message NOT found in conversation", {
                "total_messages": len(messages),
                "searched_for": "Hi again Rahul"
            })
            return False
    else:
        log_result(False, f"Get conversation failed: {response.status_code}", response.text)
        return False

# ============================================================================
# TEST 2: NEW THREAD - Verify new phone creates new thread, then reuses
# ============================================================================

def test_2a_post_new_phone():
    """Test 2a: POST with brand-new phone (Neha Gupta) - expect reused=false"""
    log_test("2a", "POST /api/whatsapp/conversations (Neha Gupta - new phone)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Neha Gupta",
            "lead_phone": "919811112222",
            "template_name": "welcome_offer",
            "template_body_rendered": "Hi Neha!",
            "body_variables": ["Neha", "BrandX X5", "Amit"],
            "language": "en"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        reused = data.get('reused')
        conv_id = data.get('conversation', {}).get('id')
        
        if reused == False and conv_id:
            log_result(True, "New conversation created (reused=false)", {
                "reused": reused,
                "conversation_id": conv_id,
                "lead_name": data.get('conversation', {}).get('lead_name'),
                "lead_phone": data.get('conversation', {}).get('lead_phone')
            })
            return True, conv_id
        else:
            log_result(False, "Expected reused=false for new phone", {
                "reused": reused,
                "conversation_id": conv_id
            })
            return False, conv_id
    else:
        log_result(False, f"POST conversation failed: {response.status_code}", response.text)
        return False, None

def test_2b_post_same_phone_again(expected_conv_id):
    """Test 2b: POST with same phone again - expect reused=true"""
    log_test("2b", "POST /api/whatsapp/conversations (Neha again - expect reused=true)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Neha Gupta",
            "lead_phone": "919811112222",
            "template_name": "welcome_offer",
            "template_body_rendered": "Hi Neha again!",
            "body_variables": ["Neha", "BrandX X5", "Amit"],
            "language": "en"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        reused = data.get('reused')
        conv_id = data.get('conversation', {}).get('id')
        
        if reused == True and conv_id == expected_conv_id:
            log_result(True, "Conversation reused correctly (reused=true, same ID)", {
                "reused": reused,
                "conversation_id": conv_id,
                "expected_id": expected_conv_id
            })
            return True
        else:
            log_result(False, "Conversation NOT reused or wrong ID", {
                "reused": reused,
                "conversation_id": conv_id,
                "expected_id": expected_conv_id
            })
            return False
    else:
        log_result(False, f"POST conversation failed: {response.status_code}", response.text)
        return False

# ============================================================================
# TEST 3: VALIDATION - Test edge cases (expect HTTP 400)
# ============================================================================

def test_3a_empty_lead_name():
    """Test 3a: POST with empty lead_name - expect 400"""
    log_test("3a", "POST with empty lead_name (expect 400)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "",
            "lead_phone": "919800000001",
            "template_name": "welcome_offer",
            "template_body_rendered": "x",
            "body_variables": [],
            "language": "en"
        }
    )
    
    if response.status_code == 400:
        log_result(True, "Validation error returned (400) for empty lead_name", {
            "status_code": response.status_code,
            "error": response.json().get('detail') if response.headers.get('content-type') == 'application/json' else response.text
        })
        return True
    else:
        log_result(False, f"Expected 400, got {response.status_code}", {
            "status_code": response.status_code,
            "response": response.text
        })
        return False

def test_3b_short_phone():
    """Test 3b: POST with short phone - expect 400"""
    log_test("3b", "POST with short phone (expect 400)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Test",
            "lead_phone": "123",
            "template_name": "welcome_offer",
            "template_body_rendered": "x",
            "body_variables": [],
            "language": "en"
        }
    )
    
    if response.status_code == 400:
        log_result(True, "Validation error returned (400) for short phone", {
            "status_code": response.status_code,
            "error": response.json().get('detail') if response.headers.get('content-type') == 'application/json' else response.text
        })
        return True
    else:
        log_result(False, f"Expected 400, got {response.status_code}", {
            "status_code": response.status_code,
            "response": response.text
        })
        return False

def test_3c_missing_template_name():
    """Test 3c: POST with missing template_name - expect 400"""
    log_test("3c", "POST with missing template_name (expect 400)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Test",
            "lead_phone": "919800000002",
            "template_name": "",
            "template_body_rendered": "x",
            "body_variables": [],
            "language": "en"
        }
    )
    
    if response.status_code == 400:
        log_result(True, "Validation error returned (400) for missing template_name", {
            "status_code": response.status_code,
            "error": response.json().get('detail') if response.headers.get('content-type') == 'application/json' else response.text
        })
        return True
    else:
        log_result(False, f"Expected 400, got {response.status_code}", {
            "status_code": response.status_code,
            "response": response.text
        })
        return False

# ============================================================================
# TEST 4: AUTO-OPEN vs MANUAL - Verify voice_agent conversation is reused
# ============================================================================

def test_4_auto_open_vs_manual():
    """Test 4: POST with Anil Kumar's phone (voice_agent conversation) - expect reused=true"""
    log_test("4", "POST with Anil Kumar (voice_agent conversation - expect reused=true)")
    
    # First, check if Anil Kumar's voice_agent conversation exists
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        log_result(False, f"Failed to get conversations: {response.status_code}", response.text)
        return False
    
    conversations = response.json().get('conversations', [])
    anil_conv = None
    for conv in conversations:
        if conv.get('lead_phone') == '919876500011' and conv.get('source') == 'voice_agent':
            anil_conv = conv
            break
    
    if not anil_conv:
        log_result(False, "Anil Kumar's voice_agent conversation NOT found", {
            "note": "Expected existing voice_agent conversation for phone 919876500011"
        })
        return False
    
    expected_conv_id = anil_conv.get('id')
    print(f"Found existing voice_agent conversation: {expected_conv_id}")
    
    # Now POST manual conversation with same phone
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Anil Kumar",
            "lead_phone": "919876500011",
            "template_name": "welcome_offer",
            "template_body_rendered": "Hi Anil!",
            "body_variables": ["Anil", "BrandX X7", "Amit"],
            "language": "en"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        reused = data.get('reused')
        conv_id = data.get('conversation', {}).get('id')
        
        if reused == True and conv_id == expected_conv_id:
            log_result(True, "Voice_agent conversation reused by manual start", {
                "reused": reused,
                "conversation_id": conv_id,
                "expected_id": expected_conv_id,
                "note": "Manual start correctly reused voice_agent conversation"
            })
            return True
        else:
            log_result(False, "Voice_agent conversation NOT reused", {
                "reused": reused,
                "conversation_id": conv_id,
                "expected_id": expected_conv_id
            })
            return False
    else:
        log_result(False, f"POST conversation failed: {response.status_code}", response.text)
        return False

# ============================================================================
# TEST 5: FINAL - Verify no duplicate lead_phone values
# ============================================================================

def test_5_no_duplicate_phones():
    """Test 5: GET all conversations - verify no duplicate lead_phone values"""
    log_test("5", "GET /api/whatsapp/conversations (verify no duplicate phones)")
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        conversations = data.get('conversations', [])
        
        # Collect all lead_phone values
        phone_counts = {}
        for conv in conversations:
            phone = conv.get('lead_phone')
            if phone:
                phone_counts[phone] = phone_counts.get(phone, 0) + 1
        
        # Find duplicates
        duplicates = {phone: count for phone, count in phone_counts.items() if count > 1}
        
        if not duplicates:
            log_result(True, "No duplicate lead_phone values found", {
                "total_conversations": len(conversations),
                "unique_phones": len(phone_counts),
                "all_phones": list(phone_counts.keys())
            })
            return True
        else:
            log_result(False, "DUPLICATE lead_phone values found!", {
                "total_conversations": len(conversations),
                "duplicates": duplicates
            })
            return False
    else:
        log_result(False, f"Get conversations failed: {response.status_code}", response.text)
        return False

# ============================================================================
# Main test runner
# ============================================================================

def run_all_tests():
    """Run all regression tests"""
    print("\n" + "="*80)
    print("WHATSAPP AI REGRESSION TEST - ONE THREAD PER PHONE NUMBER")
    print("="*80)
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    def record_result(test_id, description, success):
        results["total"] += 1
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({
            "test_id": test_id,
            "description": description,
            "success": success
        })
    
    # Login
    if not login():
        print("\n❌ LOGIN FAILED - Cannot proceed with tests")
        return results
    
    # TEST 1: DEDUPE
    print("\n" + "="*80)
    print("TEST 1: DEDUPE - Verify existing conversation is reused")
    print("="*80)
    
    initial_count, rahul_conv_id = test_1a_get_initial_conversations()
    record_result("1a", "Get initial conversations", initial_count is not None)
    
    if initial_count is not None:
        success_1b, new_rahul_id = test_1b_post_duplicate_rahul(rahul_conv_id)
        record_result("1b", "POST duplicate Rahul (expect reused)", success_1b)
        
        # Update rahul_conv_id if it was created for the first time
        if rahul_conv_id is None and new_rahul_id:
            rahul_conv_id = new_rahul_id
        
        success_1c, verified_id = test_1c_verify_count_unchanged(initial_count)
        record_result("1c", "Verify exactly ONE Rahul conversation", success_1c)
        
        if verified_id:
            success_1d = test_1d_verify_message_appended(verified_id)
            record_result("1d", "Verify message appended", success_1d)
        else:
            record_result("1d", "Verify message appended", False)
    else:
        record_result("1b", "POST duplicate Rahul (expect reused)", False)
        record_result("1c", "Verify exactly ONE Rahul conversation", False)
        record_result("1d", "Verify message appended", False)
    
    # TEST 2: NEW THREAD
    print("\n" + "="*80)
    print("TEST 2: NEW THREAD - Verify new phone creates new thread, then reuses")
    print("="*80)
    
    success_2a, neha_conv_id = test_2a_post_new_phone()
    record_result("2a", "POST new phone (Neha)", success_2a)
    
    if neha_conv_id:
        success_2b = test_2b_post_same_phone_again(neha_conv_id)
        record_result("2b", "POST same phone again (expect reused)", success_2b)
    else:
        record_result("2b", "POST same phone again (expect reused)", False)
    
    # TEST 3: VALIDATION
    print("\n" + "="*80)
    print("TEST 3: VALIDATION - Test edge cases (expect HTTP 400)")
    print("="*80)
    
    success_3a = test_3a_empty_lead_name()
    record_result("3a", "Empty lead_name (expect 400)", success_3a)
    
    success_3b = test_3b_short_phone()
    record_result("3b", "Short phone (expect 400)", success_3b)
    
    success_3c = test_3c_missing_template_name()
    record_result("3c", "Missing template_name (expect 400)", success_3c)
    
    # TEST 4: AUTO-OPEN vs MANUAL
    print("\n" + "="*80)
    print("TEST 4: AUTO-OPEN vs MANUAL - Verify voice_agent conversation is reused")
    print("="*80)
    
    success_4 = test_4_auto_open_vs_manual()
    record_result("4", "Voice_agent conversation reused", success_4)
    
    # TEST 5: FINAL
    print("\n" + "="*80)
    print("TEST 5: FINAL - Verify no duplicate lead_phone values")
    print("="*80)
    
    success_5 = test_5_no_duplicate_phones()
    record_result("5", "No duplicate phones", success_5)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success rate: {(results['passed']/results['total']*100):.1f}%")
    
    print("\nDetailed Results:")
    for detail in results["details"]:
        status = "✅" if detail["success"] else "❌"
        print(f"  {status} Test {detail['test_id']}: {detail['description']}")
    
    return results

if __name__ == "__main__":
    results = run_all_tests()
    exit(0 if results["failed"] == 0 else 1)
