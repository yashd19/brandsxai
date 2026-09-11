#!/usr/bin/env python3
"""
Backend test for WhatsApp AI media upload + auto-open on voice dial
Tests the new features:
- PART A: Chunked media upload + serve
- PART B: Send + receive media in conversation
- PART C: Auto-open WhatsApp thread when voice agent dials
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
    print(f"STEP {step}: {description}")
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
# PART A: Chunked media upload + serve
# ============================================================================

def test_upload_init():
    """Step 1: Initialize chunked upload"""
    log_test("1", "POST /api/whatsapp/upload/init")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/upload/init",
        headers=get_headers(),
        json={"filename": "pic.png", "content_type": "image/png"}
    )
    
    if response.status_code == 200:
        data = response.json()
        upload_id = data.get('upload_id')
        if upload_id:
            log_result(True, "Upload initialized", {"upload_id": upload_id})
            return upload_id
        else:
            log_result(False, "No upload_id in response", data)
            return None
    else:
        log_result(False, f"Upload init failed: {response.status_code}", response.text)
        return None

def test_upload_chunk(upload_id, chunk_data, index=0):
    """Step 2: Upload a chunk"""
    log_test(f"2.{index}", f"POST /api/whatsapp/upload/chunk (index={index})")
    
    # Send raw binary data
    headers = {"Content-Type": "application/octet-stream"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/upload/chunk?upload_id={upload_id}&index={index}",
        headers=headers,
        data=chunk_data
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            log_result(True, f"Chunk {index} uploaded", {"size": data.get('size'), "index": data.get('index')})
            return True
        else:
            log_result(False, "Upload chunk response not ok", data)
            return False
    else:
        log_result(False, f"Upload chunk failed: {response.status_code}", response.text)
        return False

def test_upload_complete(upload_id):
    """Step 3: Complete upload"""
    log_test("3", "POST /api/whatsapp/upload/complete")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/upload/complete",
        headers=get_headers(),
        json={"upload_id": upload_id, "filename": "pic.png", "content_type": "image/png"}
    )
    
    if response.status_code == 200:
        data = response.json()
        media_id = data.get('media_id')
        url = data.get('url')
        kind = data.get('kind')
        
        if media_id and url and kind == 'image':
            log_result(True, "Upload completed", {
                "media_id": media_id,
                "url": url,
                "kind": kind
            })
            return media_id, url
        else:
            log_result(False, "Missing fields in response", data)
            return None, None
    else:
        log_result(False, f"Upload complete failed: {response.status_code}", response.text)
        return None, None

def test_get_media(media_url, expected_bytes):
    """Step 4: GET media file (public endpoint)"""
    log_test("4", f"GET {media_url} (public, no auth)")
    
    # Prepend base URL if needed
    if media_url.startswith('/api/'):
        full_url = f"{BACKEND_URL}{media_url}"
    else:
        full_url = media_url
    
    # No auth header for public endpoint
    response = requests.get(full_url)
    
    if response.status_code == 200:
        received_bytes = response.content
        if received_bytes == expected_bytes:
            log_result(True, "Media retrieved successfully", {
                "expected_size": len(expected_bytes),
                "received_size": len(received_bytes),
                "bytes_match": True
            })
            return True
        else:
            log_result(False, "Bytes mismatch", {
                "expected_size": len(expected_bytes),
                "received_size": len(received_bytes),
                "expected": expected_bytes[:50],
                "received": received_bytes[:50]
            })
            return False
    else:
        log_result(False, f"Get media failed: {response.status_code}", response.text)
        return False

# ============================================================================
# PART B: Send + receive media in conversation
# ============================================================================

def test_create_conversation():
    """Step 5: Create a conversation"""
    log_test("5", "POST /api/whatsapp/conversations (create conversation)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers(),
        json={
            "lead_name": "Media Test",
            "lead_phone": "919812340000",
            "template_name": "welcome_offer",
            "template_body_rendered": "Hi Media Test!",
            "body_variables": ["Media Test", "BrandX X7", "Amit"],
            "language": "en"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        conv_id = data.get('conversation', {}).get('id')
        if conv_id:
            log_result(True, "Conversation created", {"conversation_id": conv_id})
            return conv_id
        else:
            log_result(False, "No conversation id in response", data)
            return None
    else:
        log_result(False, f"Create conversation failed: {response.status_code}", response.text)
        return None

def test_send_media_message(conv_id, media_url):
    """Step 6: Send media message"""
    log_test("6", f"POST /api/whatsapp/conversations/{conv_id}/messages (send image)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations/{conv_id}/messages",
        headers=get_headers(),
        json={
            "content": "Check this out",
            "msg_type": "image",
            "media_url": media_url
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        message = data.get('message', {})
        
        if (message.get('msg_type') == 'image' and 
            message.get('media_url') == media_url and
            message.get('simulated') == True):
            log_result(True, "Media message sent", {
                "msg_type": message.get('msg_type'),
                "media_url": message.get('media_url'),
                "simulated": message.get('simulated'),
                "sender_type": message.get('sender_type')
            })
            return True
        else:
            log_result(False, "Message fields incorrect", message)
            return False
    else:
        log_result(False, f"Send media message failed: {response.status_code}", response.text)
        return False

def test_simulate_inbound_media(conv_id, media_url):
    """Step 7: Simulate inbound media message"""
    log_test("7", f"POST /api/whatsapp/conversations/{conv_id}/simulate-inbound (inbound image)")
    
    response = requests.post(
        f"{BASE_URL}/whatsapp/conversations/{conv_id}/simulate-inbound",
        headers=get_headers(),
        json={
            "content": "my current car",
            "msg_type": "image",
            "media_url": media_url
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        message = data.get('message', {})
        
        if (message.get('msg_type') == 'image' and 
            message.get('media_url') == media_url and
            message.get('direction') == 'inbound' and
            message.get('sender_type') == 'customer'):
            log_result(True, "Inbound media message simulated", {
                "msg_type": message.get('msg_type'),
                "media_url": message.get('media_url'),
                "direction": message.get('direction'),
                "sender_type": message.get('sender_type')
            })
            return True
        else:
            log_result(False, "Message fields incorrect", message)
            return False
    else:
        log_result(False, f"Simulate inbound failed: {response.status_code}", response.text)
        return False

def test_get_conversation_messages(conv_id, media_url):
    """Step 8: Verify media messages in conversation"""
    log_test("8", f"GET /api/whatsapp/conversations/{conv_id} (verify media messages)")
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations/{conv_id}",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get('messages', [])
        
        # Find media messages
        outbound_media = [m for m in messages if m.get('msg_type') == 'image' and m.get('direction') == 'outbound']
        inbound_media = [m for m in messages if m.get('msg_type') == 'image' and m.get('direction') == 'inbound']
        
        if len(outbound_media) >= 1 and len(inbound_media) >= 1:
            log_result(True, "Media messages present in conversation", {
                "total_messages": len(messages),
                "outbound_media_count": len(outbound_media),
                "inbound_media_count": len(inbound_media)
            })
            return True
        else:
            log_result(False, "Media messages not found", {
                "total_messages": len(messages),
                "outbound_media_count": len(outbound_media),
                "inbound_media_count": len(inbound_media)
            })
            return False
    else:
        log_result(False, f"Get conversation failed: {response.status_code}", response.text)
        return False

# ============================================================================
# PART C: Auto-open WhatsApp thread when voice agent dials
# ============================================================================

def test_create_campaign():
    """Step 9: Create campaign"""
    log_test("9", "POST /api/campaigns (create campaign)")
    
    response = requests.post(
        f"{BASE_URL}/campaigns",
        headers=get_headers(),
        json={"name": "Voice Auto Test"}
    )
    
    if response.status_code == 200:
        data = response.json()
        campaign_id = data.get('id') or data.get('campaign', {}).get('id')
        if campaign_id:
            log_result(True, "Campaign created", {"campaign_id": campaign_id})
            return campaign_id
        else:
            log_result(False, "No campaign id in response", data)
            return None
    else:
        log_result(False, f"Create campaign failed: {response.status_code}", response.text)
        return None

def test_add_opportunity(campaign_id):
    """Step 10: Add opportunity"""
    log_test("10", f"POST /api/campaigns/{campaign_id}/opportunities (add opportunity)")
    
    response = requests.post(
        f"{BASE_URL}/campaigns/{campaign_id}/opportunities",
        headers=get_headers(),
        json={
            "name": "Anil Kumar",
            "phone": "9876500011"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        opp_id = data.get('id') or data.get('opportunity', {}).get('id')
        if opp_id:
            log_result(True, "Opportunity added", {"opportunity_id": opp_id})
            return opp_id
        else:
            log_result(False, "No opportunity id in response", data)
            return None
    else:
        log_result(False, f"Add opportunity failed: {response.status_code}", response.text)
        return None

def test_dial_opportunity(opp_id, phone):
    """Step 11: Dial opportunity (voice API may error - that's OK)"""
    log_test("11", f"POST /api/opportunities/{opp_id}/dial (dial opportunity)")
    
    response = requests.post(
        f"{BASE_URL}/opportunities/{opp_id}/dial",
        headers=get_headers(),
        json={"phone": phone}
    )
    
    # NOTE: The external voice API may return 502/504 or other errors
    # This is EXPECTED and should not fail the test
    # The important part is that the WhatsApp conversation is created BEFORE the dial
    
    if response.status_code in [200, 502, 504, 400]:
        log_result(True, f"Dial endpoint called (status {response.status_code})", {
            "note": "Voice API error is expected and OK",
            "status_code": response.status_code
        })
        return True
    else:
        log_result(True, f"Dial endpoint called with status {response.status_code}", {
            "note": "Any response is acceptable - WhatsApp thread should be created regardless"
        })
        return True

def test_verify_auto_conversation(phone):
    """Step 12: Verify auto-created WhatsApp conversation"""
    log_test("12", "GET /api/whatsapp/conversations (verify auto-created conversation)")
    
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        conversations = data.get('conversations', [])
        
        # Phone might be normalized with country code (91 prefix for India)
        # Try both with and without country code
        normalized_phone = f"91{phone}" if not phone.startswith("91") else phone
        
        # Find conversation for the dialed phone
        auto_conv = None
        for conv in conversations:
            conv_phone = conv.get('lead_phone')
            if (conv_phone == phone or conv_phone == normalized_phone) and conv.get('source') == 'voice_agent':
                auto_conv = conv
                break
        
        if auto_conv:
            # Verify it has a template message
            conv_id = auto_conv.get('id')
            msg_response = requests.get(
                f"{BASE_URL}/whatsapp/conversations/{conv_id}",
                headers=get_headers()
            )
            
            if msg_response.status_code == 200:
                conv_data = msg_response.json()
                messages = conv_data.get('messages', [])
                template_msg = [m for m in messages if m.get('msg_type') == 'template' and m.get('sender_type') == 'bot']
                
                if template_msg:
                    log_result(True, "Auto-created conversation verified", {
                        "conversation_id": conv_id,
                        "lead_phone": auto_conv.get('lead_phone'),
                        "lead_name": auto_conv.get('lead_name'),
                        "source": auto_conv.get('source'),
                        "has_template_message": True
                    })
                    return conv_id
                else:
                    log_result(False, "No template message found", {
                        "conversation_id": conv_id,
                        "message_count": len(messages)
                    })
                    return None
            else:
                log_result(False, f"Failed to get conversation messages: {msg_response.status_code}", msg_response.text)
                return None
        else:
            log_result(False, "Auto-created conversation not found", {
                "total_conversations": len(conversations),
                "searched_phone": phone,
                "normalized_phone": normalized_phone
            })
            return None
    else:
        log_result(False, f"Get conversations failed: {response.status_code}", response.text)
        return None

def test_dial_idempotency(opp_id, phone):
    """Step 13: Test dial idempotency"""
    log_test("13", f"POST /api/opportunities/{opp_id}/dial (test idempotency)")
    
    # Phone might be normalized with country code
    normalized_phone = f"91{phone}" if not phone.startswith("91") else phone
    
    # Get current conversation count
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        log_result(False, "Failed to get conversations before second dial", response.text)
        return False
    
    conversations_before = response.json().get('conversations', [])
    count_before = len([c for c in conversations_before if c.get('lead_phone') in [phone, normalized_phone]])
    
    # Dial again
    dial_response = requests.post(
        f"{BASE_URL}/opportunities/{opp_id}/dial",
        headers=get_headers(),
        json={"phone": phone}
    )
    
    # Get conversation count after
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        log_result(False, "Failed to get conversations after second dial", response.text)
        return False
    
    conversations_after = response.json().get('conversations', [])
    count_after = len([c for c in conversations_after if c.get('lead_phone') in [phone, normalized_phone]])
    
    if count_before == count_after == 1:
        log_result(True, "Dial idempotency verified", {
            "conversations_before": count_before,
            "conversations_after": count_after,
            "note": "No duplicate conversation created"
        })
        return True
    else:
        log_result(False, "Idempotency check failed", {
            "conversations_before": count_before,
            "conversations_after": count_after
        })
        return False

# ============================================================================
# Main test runner
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("WHATSAPP AI BACKEND TESTING - MEDIA + AUTO-OPEN")
    print("="*80)
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    def record_result(step, description, success):
        results["total"] += 1
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({
            "step": step,
            "description": description,
            "success": success
        })
    
    # Login
    if not login():
        print("\n❌ LOGIN FAILED - Cannot proceed with tests")
        return results
    
    # PART A: Chunked media upload + serve
    print("\n" + "="*80)
    print("PART A: CHUNKED MEDIA UPLOAD + SERVE")
    print("="*80)
    
    # Test data - PNG header + some test bytes
    test_bytes = b"\x89PNG\r\n\x1a\n test bytes for chunked upload"
    chunk1 = test_bytes[:15]
    chunk2 = test_bytes[15:]
    
    upload_id = test_upload_init()
    record_result("1", "Initialize upload", upload_id is not None)
    
    if upload_id:
        chunk1_ok = test_upload_chunk(upload_id, chunk1, 0)
        record_result("2.0", "Upload chunk 0", chunk1_ok)
        
        chunk2_ok = test_upload_chunk(upload_id, chunk2, 1)
        record_result("2.1", "Upload chunk 1", chunk2_ok)
        
        media_id, media_url = test_upload_complete(upload_id)
        record_result("3", "Complete upload", media_id is not None and media_url is not None)
        
        if media_url:
            media_ok = test_get_media(media_url, test_bytes)
            record_result("4", "Get media (public)", media_ok)
        else:
            record_result("4", "Get media (public)", False)
            media_url = None
    else:
        record_result("2.0", "Upload chunk 0", False)
        record_result("2.1", "Upload chunk 1", False)
        record_result("3", "Complete upload", False)
        record_result("4", "Get media (public)", False)
        media_url = None
    
    # PART B: Send + receive media in conversation
    print("\n" + "="*80)
    print("PART B: SEND + RECEIVE MEDIA IN CONVERSATION")
    print("="*80)
    
    conv_id = test_create_conversation()
    record_result("5", "Create conversation", conv_id is not None)
    
    if conv_id and media_url:
        send_ok = test_send_media_message(conv_id, media_url)
        record_result("6", "Send media message", send_ok)
        
        inbound_ok = test_simulate_inbound_media(conv_id, media_url)
        record_result("7", "Simulate inbound media", inbound_ok)
        
        verify_ok = test_get_conversation_messages(conv_id, media_url)
        record_result("8", "Verify media in conversation", verify_ok)
    else:
        record_result("6", "Send media message", False)
        record_result("7", "Simulate inbound media", False)
        record_result("8", "Verify media in conversation", False)
    
    # PART C: Auto-open WhatsApp thread on voice dial
    print("\n" + "="*80)
    print("PART C: AUTO-OPEN WHATSAPP THREAD ON VOICE DIAL")
    print("="*80)
    
    campaign_id = test_create_campaign()
    record_result("9", "Create campaign", campaign_id is not None)
    
    if campaign_id:
        opp_id = test_add_opportunity(campaign_id)
        record_result("10", "Add opportunity", opp_id is not None)
        
        if opp_id:
            phone = "9876500011"
            dial_ok = test_dial_opportunity(opp_id, phone)
            record_result("11", "Dial opportunity", dial_ok)
            
            auto_conv_id = test_verify_auto_conversation(phone)
            record_result("12", "Verify auto-created conversation", auto_conv_id is not None)
            
            if auto_conv_id:
                idempotent_ok = test_dial_idempotency(opp_id, phone)
                record_result("13", "Test dial idempotency", idempotent_ok)
            else:
                record_result("13", "Test dial idempotency", False)
        else:
            record_result("11", "Dial opportunity", False)
            record_result("12", "Verify auto-created conversation", False)
            record_result("13", "Test dial idempotency", False)
    else:
        record_result("10", "Add opportunity", False)
        record_result("11", "Dial opportunity", False)
        record_result("12", "Verify auto-created conversation", False)
        record_result("13", "Test dial idempotency", False)
    
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
        print(f"  {status} Step {detail['step']}: {detail['description']}")
    
    return results

if __name__ == "__main__":
    results = run_all_tests()
    exit(0 if results["failed"] == 0 else 1)
