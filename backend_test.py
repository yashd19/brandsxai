#!/usr/bin/env python3
"""
WhatsApp AI Backend Regression Test Suite
Tests webhook signature diagnostics + out-of-order status ticks bug fixes
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://f11fcb3b-5aba-4b2b-a12a-6a2028a9906c.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
USERNAME = "testuser"
PASSWORD = "test123"

# Global token storage
AUTH_TOKEN = None

def login():
    """Login once and store the token"""
    global AUTH_TOKEN
    print("\n=== LOGIN ===")
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        AUTH_TOKEN = data.get("access_token")
        print(f"✅ Login successful, token obtained")
        return True
    else:
        print(f"❌ Login failed: {response.text}")
        return False

def get_headers(auth=True):
    """Get headers with optional auth"""
    headers = {"Content-Type": "application/json"}
    if auth and AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers

def test_1_whatsapp_status():
    """TEST 1: GET /api/whatsapp/status"""
    print("\n" + "="*80)
    print("TEST 1: GET /api/whatsapp/status (auth required)")
    print("="*80)
    
    # Test with auth
    response = requests.get(f"{API_BASE}/whatsapp/status", headers=get_headers(auth=True))
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check required fields
    checks = []
    
    # Basic status
    if data.get("token_valid") == True:
        print("✅ token_valid == true")
        checks.append(True)
    else:
        print(f"❌ token_valid: expected true, got {data.get('token_valid')}")
        checks.append(False)
    
    if data.get("ready_to_send") == True:
        print("✅ ready_to_send == true")
        checks.append(True)
    else:
        print(f"❌ ready_to_send: expected true, got {data.get('ready_to_send')}")
        checks.append(False)
    
    if data.get("live_mode") == True:
        print("✅ live_mode == true")
        checks.append(True)
    else:
        print(f"❌ live_mode: expected true, got {data.get('live_mode')}")
        checks.append(False)
    
    # Phone number info
    phone_number = data.get("phone_number", {})
    if phone_number.get("verified_name") == "Swad Mania":
        print(f"✅ verified_name == 'Swad Mania'")
        checks.append(True)
    else:
        print(f"❌ verified_name: expected 'Swad Mania', got {phone_number.get('verified_name')}")
        checks.append(False)
    
    if phone_number.get("display_phone_number"):
        print(f"✅ display_phone_number present: {phone_number.get('display_phone_number')}")
        checks.append(True)
    else:
        print(f"❌ display_phone_number missing")
        checks.append(False)
    
    # Token info
    token_info = data.get("token_info", {})
    if token_info.get("never_expires") == True:
        print(f"✅ token_info.never_expires == true")
        checks.append(True)
    else:
        print(f"❌ token_info.never_expires: expected true, got {token_info.get('never_expires')}")
        checks.append(False)
    
    if token_info.get("type") == "SYSTEM_USER":
        print(f"✅ token_info.type == 'SYSTEM_USER'")
        checks.append(True)
    else:
        print(f"❌ token_info.type: expected 'SYSTEM_USER', got {token_info.get('type')}")
        checks.append(False)
    
    # WABA IDs
    waba_ids = data.get("waba_ids", [])
    if "971659015904015" in waba_ids:
        print(f"✅ waba_ids contains '971659015904015'")
        checks.append(True)
    else:
        print(f"❌ waba_ids missing '971659015904015': {waba_ids}")
        checks.append(False)
    
    # Approved templates
    approved_templates = data.get("approved_templates", [])
    if len(approved_templates) >= 14:
        print(f"✅ approved_templates contains {len(approved_templates)} entries (>= 14)")
        checks.append(True)
    else:
        print(f"❌ approved_templates: expected >= 14, got {len(approved_templates)}")
        checks.append(False)
    
    # Check all templates are APPROVED
    all_approved = all(t.get("status") == "APPROVED" for t in approved_templates)
    if all_approved:
        print(f"✅ All templates have status APPROVED")
        checks.append(True)
    else:
        print(f"❌ Not all templates are APPROVED")
        checks.append(False)
    
    # Check for specific templates
    template_names = [t.get("name") for t in approved_templates]
    if "hello_world" in template_names:
        print(f"✅ 'hello_world' template present")
        checks.append(True)
    else:
        print(f"❌ 'hello_world' template missing")
        checks.append(False)
    
    if "tenant_welcome" in template_names:
        print(f"✅ 'tenant_welcome' template present")
        checks.append(True)
    else:
        print(f"❌ 'tenant_welcome' template missing")
        checks.append(False)
    
    # Check all templates have language en_US
    all_en_us = all(t.get("language") == "en_US" for t in approved_templates)
    if all_en_us:
        print(f"✅ All templates have language 'en_US'")
        checks.append(True)
    else:
        non_en_us = [t for t in approved_templates if t.get("language") != "en_US"]
        print(f"❌ Some templates don't have 'en_US': {[(t.get('name'), t.get('language')) for t in non_en_us]}")
        checks.append(False)
    
    # Webhook traffic
    webhook_traffic = data.get("webhook_traffic")
    if webhook_traffic and isinstance(webhook_traffic, dict):
        print(f"✅ webhook_traffic object present")
        required_keys = ["received_count", "signature_ok_count", "signature_fail_count", "processed_messages", "processed_statuses"]
        for key in required_keys:
            if key in webhook_traffic and isinstance(webhook_traffic[key], int):
                print(f"  ✅ {key}: {webhook_traffic[key]}")
            else:
                print(f"  ❌ {key} missing or not an integer")
                checks.append(False)
        checks.append(True)
    else:
        print(f"❌ webhook_traffic missing or not a dict")
        checks.append(False)
    
    # Webhook signature check
    checks_array = data.get("checks", [])
    webhook_sig_check = next((c for c in checks_array if c.get("check") == "webhook_signature"), None)
    if webhook_sig_check:
        print(f"✅ 'webhook_signature' check found in checks array")
        print(f"  ok: {webhook_sig_check.get('ok')}")
        print(f"  detail: {webhook_sig_check.get('detail')}")
        checks.append(True)
    else:
        print(f"❌ 'webhook_signature' check not found in checks array")
        checks.append(False)
    
    # Test without auth (should be 403)
    print("\n--- Testing without Authorization header ---")
    response_no_auth = requests.get(f"{API_BASE}/whatsapp/status")
    if response_no_auth.status_code == 403:
        print(f"✅ Returns 403 when called without Authorization header")
        checks.append(True)
    else:
        print(f"❌ Expected 403 without auth, got {response_no_auth.status_code}")
        checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 1 PASSED' if success else '❌ TEST 1 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success

def test_2_template_sync():
    """TEST 2: POST /api/whatsapp/templates/sync"""
    print("\n" + "="*80)
    print("TEST 2: POST /api/whatsapp/templates/sync (auth required)")
    print("="*80)
    
    checks = []
    
    # Sync templates
    response = requests.post(f"{API_BASE}/whatsapp/templates/sync", headers=get_headers(auth=True))
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get("synced_count") == 14:
        print(f"✅ synced_count == 14")
        checks.append(True)
    else:
        print(f"❌ synced_count: expected 14, got {data.get('synced_count')}")
        checks.append(False)
    
    if data.get("skipped_not_approved") == 0:
        print(f"✅ skipped_not_approved == 0")
        checks.append(True)
    else:
        print(f"❌ skipped_not_approved: expected 0, got {data.get('skipped_not_approved')}")
        checks.append(False)
    
    if data.get("waba_id") == "971659015904015":
        print(f"✅ waba_id == '971659015904015'")
        checks.append(True)
    else:
        print(f"❌ waba_id: expected '971659015904015', got {data.get('waba_id')}")
        checks.append(False)
    
    # Get templates
    print("\n--- GET /api/whatsapp/templates ---")
    response = requests.get(f"{API_BASE}/whatsapp/templates", headers=get_headers(auth=True))
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Expected 200, got {response.status_code}")
        return False
    
    data = response.json()
    
    if data.get("source") == "meta":
        print(f"✅ source == 'meta'")
        checks.append(True)
    else:
        print(f"❌ source: expected 'meta', got {data.get('source')}")
        checks.append(False)
    
    if data.get("live_mode") == True:
        print(f"✅ live_mode == true")
        checks.append(True)
    else:
        print(f"❌ live_mode: expected true, got {data.get('live_mode')}")
        checks.append(False)
    
    templates = data.get("templates", [])
    if len(templates) == 14:
        print(f"✅ 14 templates returned")
        checks.append(True)
    else:
        print(f"❌ Expected 14 templates, got {len(templates)}")
        checks.append(False)
    
    # Check all templates have language en_US (NOT en)
    all_en_us = all(t.get("language") == "en_US" for t in templates)
    if all_en_us:
        print(f"✅ All templates have language 'en_US' (NOT 'en')")
        checks.append(True)
    else:
        non_en_us = [t for t in templates if t.get("language") != "en_US"]
        print(f"❌ Some templates don't have 'en_US': {[(t.get('name'), t.get('language')) for t in non_en_us]}")
        checks.append(False)
    
    # Check hello_world
    hello_world = next((t for t in templates if t.get("name") == "hello_world"), None)
    if hello_world:
        print(f"✅ 'hello_world' template found")
        if hello_world.get("variable_count") == 0:
            print(f"  ✅ variable_count == 0")
            checks.append(True)
        else:
            print(f"  ❌ variable_count: expected 0, got {hello_world.get('variable_count')}")
            checks.append(False)
        
        if hello_world.get("variables") == []:
            print(f"  ✅ variables == []")
            checks.append(True)
        else:
            print(f"  ❌ variables: expected [], got {hello_world.get('variables')}")
            checks.append(False)
    else:
        print(f"❌ 'hello_world' template not found")
        checks.append(False)
    
    # Check tenant_welcome
    tenant_welcome = next((t for t in templates if t.get("name") == "tenant_welcome"), None)
    if tenant_welcome:
        print(f"✅ 'tenant_welcome' template found")
        if tenant_welcome.get("variable_count") == 2:
            print(f"  ✅ variable_count == 2")
            checks.append(True)
        else:
            print(f"  ❌ variable_count: expected 2, got {tenant_welcome.get('variable_count')}")
            checks.append(False)
        
        variables = tenant_welcome.get("variables", [])
        print(f"  Variables: {variables}")
        # Check that variables are human readable with example hints
        if len(variables) == 2:
            # Should look like ["Variable 1 (e.g. Krish)", "Variable 2 (e.g. 38 Stagg Street)"]
            has_examples = all("e.g." in str(v) for v in variables)
            if has_examples:
                print(f"  ✅ Variables contain example hints (e.g.)")
                checks.append(True)
            else:
                print(f"  ❌ Variables don't contain example hints")
                checks.append(False)
        else:
            print(f"  ❌ Expected 2 variables, got {len(variables)}")
            checks.append(False)
    else:
        print(f"❌ 'tenant_welcome' template not found")
        checks.append(False)
    
    # Check maintenance_visit_scheduled
    maintenance = next((t for t in templates if t.get("name") == "maintenance_visit_scheduled"), None)
    if maintenance:
        print(f"✅ 'maintenance_visit_scheduled' template found")
        if maintenance.get("variable_count") == 4:
            print(f"  ✅ variable_count == 4")
            checks.append(True)
        else:
            print(f"  ❌ variable_count: expected 4, got {maintenance.get('variable_count')}")
            checks.append(False)
    else:
        print(f"❌ 'maintenance_visit_scheduled' template not found")
        checks.append(False)
    
    # Test idempotency - sync again
    print("\n--- Testing idempotency (sync again) ---")
    response = requests.post(f"{API_BASE}/whatsapp/templates/sync", headers=get_headers(auth=True))
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Get templates again
        response = requests.get(f"{API_BASE}/whatsapp/templates", headers=get_headers(auth=True))
        data = response.json()
        templates = data.get("templates", [])
        if len(templates) == 14:
            print(f"✅ Still 14 templates after second sync (no duplicates)")
            checks.append(True)
        else:
            print(f"❌ Expected 14 templates after second sync, got {len(templates)}")
            checks.append(False)
    else:
        print(f"❌ Second sync failed: {response.status_code}")
        checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 2 PASSED' if success else '❌ TEST 2 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success

def test_3_inbound_message_webhook():
    """TEST 3: Inbound message via POST /api/whatsapp/webhook"""
    print("\n" + "="*80)
    print("TEST 3: Inbound message via POST /api/whatsapp/webhook (public, no auth)")
    print("="*80)
    
    checks = []
    
    # Create a unique wamid with timestamp
    timestamp = int(time.time() * 1000)
    wamid = f"wamid.TEST_INBOUND_{timestamp}"
    fake_phone = "919000000001"
    
    # Craft realistic Meta payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "971659015904015",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15515506716",
                        "phone_number_id": "1236101482916191"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Test Customer"
                        },
                        "wa_id": fake_phone
                    }],
                    "messages": [{
                        "from": fake_phone,
                        "id": wamid,
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {
                            "body": "Hello, I'm interested in your products"
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    print(f"Sending webhook with wamid: {wamid}")
    print(f"Fake phone: {fake_phone}")
    print(f"Profile name: Test Customer")
    
    # Send webhook WITHOUT X-Hub-Signature-256 header
    response = requests.post(
        f"{API_BASE}/whatsapp/webhook",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok") == True:
            print(f"✅ Webhook accepted (200 with ok: true)")
            checks.append(True)
        else:
            print(f"❌ Expected ok: true, got {data}")
            checks.append(False)
    else:
        print(f"❌ Expected 200, got {response.status_code}")
        checks.append(False)
    
    # Wait a moment for processing
    time.sleep(1)
    
    # Get conversations
    print("\n--- GET /api/whatsapp/conversations ---")
    response = requests.get(f"{API_BASE}/whatsapp/conversations", headers=get_headers(auth=True))
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Expected 200, got {response.status_code}")
        return False, None, None
    
    data = response.json()
    conversations = data.get("conversations", [])
    print(f"Total conversations: {len(conversations)}")
    
    # Find the conversation for our fake phone
    thread = None
    for conv in conversations:
        if conv.get("lead_phone") == fake_phone or conv.get("lead_phone") == f"91{fake_phone}":
            thread = conv
            break
    
    if thread:
        print(f"✅ Thread exists for lead_phone '{fake_phone}'")
        print(f"  Conversation ID: {thread.get('id')}")
        checks.append(True)
        
        # CRITICAL: Check lead_name is "Test Customer", NOT the phone number
        lead_name = thread.get("lead_name")
        if lead_name == "Test Customer":
            print(f"✅ CRITICAL: lead_name == 'Test Customer' (WhatsApp profile name, NOT phone number)")
            checks.append(True)
        else:
            print(f"❌ CRITICAL: lead_name should be 'Test Customer', got '{lead_name}'")
            checks.append(False)
        
        # Check unread_count
        unread_count = thread.get("unread_count", 0)
        if unread_count >= 1:
            print(f"✅ unread_count >= 1 ({unread_count})")
            checks.append(True)
        else:
            print(f"❌ unread_count should be >= 1, got {unread_count}")
            checks.append(False)
        
        # Check window_expires_at
        window_expires_at = thread.get("window_expires_at")
        if window_expires_at:
            print(f"✅ window_expires_at set: {window_expires_at}")
            # Should be roughly 24h in the future
            checks.append(True)
        else:
            print(f"❌ window_expires_at not set")
            checks.append(False)
        
        # Get conversation details
        print(f"\n--- GET /api/whatsapp/conversations/{thread.get('id')} ---")
        response = requests.get(
            f"{API_BASE}/whatsapp/conversations/{thread.get('id')}",
            headers=get_headers(auth=True)
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            conv_data = response.json()
            messages = conv_data.get("messages", [])
            print(f"Messages count: {len(messages)}")
            
            # Find the inbound message
            inbound_msg = None
            for msg in messages:
                if msg.get("wa_message_id") == wamid:
                    inbound_msg = msg
                    break
            
            if inbound_msg:
                print(f"✅ Inbound message found")
                
                if inbound_msg.get("direction") == "inbound":
                    print(f"  ✅ direction == 'inbound'")
                    checks.append(True)
                else:
                    print(f"  ❌ direction: expected 'inbound', got {inbound_msg.get('direction')}")
                    checks.append(False)
                
                if inbound_msg.get("sender_type") == "customer":
                    print(f"  ✅ sender_type == 'customer'")
                    checks.append(True)
                else:
                    print(f"  ❌ sender_type: expected 'customer', got {inbound_msg.get('sender_type')}")
                    checks.append(False)
                
                if "interested in your products" in inbound_msg.get("content", ""):
                    print(f"  ✅ Correct text content")
                    checks.append(True)
                else:
                    print(f"  ❌ Wrong content: {inbound_msg.get('content')}")
                    checks.append(False)
                
                if inbound_msg.get("simulated") == False:
                    print(f"  ✅ simulated == false")
                    checks.append(True)
                else:
                    print(f"  ❌ simulated: expected false, got {inbound_msg.get('simulated')}")
                    checks.append(False)
            else:
                print(f"❌ Inbound message not found")
                checks.append(False)
        else:
            print(f"❌ Failed to get conversation details")
            checks.append(False)
        
        # Test idempotency - send same payload again
        print("\n--- Testing idempotency (same wamid) ---")
        response = requests.post(
            f"{API_BASE}/whatsapp/webhook",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            time.sleep(1)
            # Get conversation again
            response = requests.get(
                f"{API_BASE}/whatsapp/conversations/{thread.get('id')}",
                headers=get_headers(auth=True)
            )
            if response.status_code == 200:
                conv_data = response.json()
                messages = conv_data.get("messages", [])
                # Count messages with our wamid
                count = sum(1 for msg in messages if msg.get("wa_message_id") == wamid)
                if count == 1:
                    print(f"✅ Message NOT duplicated (count == 1)")
                    checks.append(True)
                else:
                    print(f"❌ Message duplicated (count == {count})")
                    checks.append(False)
            else:
                print(f"❌ Failed to get conversation for idempotency check")
                checks.append(False)
        else:
            print(f"❌ Second webhook failed: {response.status_code}")
            checks.append(False)
    else:
        print(f"❌ Thread not found for phone {fake_phone}")
        checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 3 PASSED' if success else '❌ TEST 3 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success, wamid if thread else None, thread.get('id') if thread else None

def test_4_out_of_order_status_ticks(wamid, conversation_id):
    """TEST 4: Out-of-order delivery ticks - MOST IMPORTANT"""
    print("\n" + "="*80)
    print("TEST 4: Out-of-order delivery ticks (MOST IMPORTANT REGRESSION)")
    print("="*80)
    
    if not wamid or not conversation_id:
        print("❌ No wamid or conversation_id from test 3, skipping")
        return False
    
    checks = []
    fake_phone = "919000000001"
    
    print(f"Using wamid: {wamid}")
    print(f"Conversation ID: {conversation_id}")
    
    def send_status_webhook(status, error=None):
        """Helper to send status webhook"""
        timestamp_val = str(int(time.time()))
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "971659015904015",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15515506716",
                            "phone_number_id": "1236101482916191"
                        },
                        "statuses": [{
                            "id": wamid,
                            "status": status,
                            "timestamp": timestamp_val,
                            "recipient_id": fake_phone
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        if error:
            payload["entry"][0]["changes"][0]["value"]["statuses"][0]["errors"] = [error]
        
        response = requests.post(
            f"{API_BASE}/whatsapp/webhook",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return response
    
    def get_message_status():
        """Helper to get current message status"""
        response = requests.get(
            f"{API_BASE}/whatsapp/conversations/{conversation_id}",
            headers=get_headers(auth=True)
        )
        if response.status_code == 200:
            conv_data = response.json()
            messages = conv_data.get("messages", [])
            for msg in messages:
                if msg.get("wa_message_id") == wamid:
                    return msg.get("status"), msg.get("status_timestamps", {}), msg.get("error")
        return None, {}, None
    
    # a) Send "read" status
    print("\n--- Step a) Send 'read' status ---")
    response = send_status_webhook("read")
    print(f"Webhook status: {response.status_code}")
    time.sleep(1)
    
    status, timestamps, error = get_message_status()
    print(f"Current status: {status}")
    print(f"Status timestamps: {timestamps}")
    
    if status == "read":
        print(f"✅ Status became 'read'")
        checks.append(True)
    else:
        print(f"❌ Status should be 'read', got '{status}'")
        checks.append(False)
    
    if "read" in timestamps:
        print(f"✅ status_timestamps.read present")
        checks.append(True)
    else:
        print(f"❌ status_timestamps.read missing")
        checks.append(False)
    
    # b) Send "delivered" status (should NOT downgrade from "read")
    print("\n--- Step b) Send 'delivered' status (should NOT downgrade) ---")
    response = send_status_webhook("delivered")
    print(f"Webhook status: {response.status_code}")
    time.sleep(1)
    
    status, timestamps, error = get_message_status()
    print(f"Current status: {status}")
    print(f"Status timestamps: {timestamps}")
    
    if status == "read":
        print(f"✅ CRITICAL: Status REMAINED 'read' (did NOT downgrade to 'delivered')")
        checks.append(True)
    else:
        print(f"❌ CRITICAL: Status downgraded to '{status}' (should remain 'read')")
        checks.append(False)
    
    if "delivered" in timestamps:
        print(f"✅ status_timestamps.delivered accumulated")
        checks.append(True)
    else:
        print(f"❌ status_timestamps.delivered missing")
        checks.append(False)
    
    # c) Send "sent" status (should NOT downgrade from "read")
    print("\n--- Step c) Send 'sent' status (should NOT downgrade) ---")
    response = send_status_webhook("sent")
    print(f"Webhook status: {response.status_code}")
    time.sleep(1)
    
    status, timestamps, error = get_message_status()
    print(f"Current status: {status}")
    print(f"Status timestamps: {timestamps}")
    
    if status == "read":
        print(f"✅ CRITICAL: Status REMAINED 'read' (did NOT downgrade to 'sent')")
        checks.append(True)
    else:
        print(f"❌ CRITICAL: Status downgraded to '{status}' (should remain 'read')")
        checks.append(False)
    
    if "sent" in timestamps:
        print(f"✅ status_timestamps.sent accumulated")
        checks.append(True)
    else:
        print(f"❌ status_timestamps.sent missing")
        checks.append(False)
    
    # d) Send "failed" status (should ALWAYS apply)
    print("\n--- Step d) Send 'failed' status (should ALWAYS apply) ---")
    error_obj = {
        "code": 131026,
        "title": "Message Undeliverable",
        "message": "Message failed to send"
    }
    response = send_status_webhook("failed", error_obj)
    print(f"Webhook status: {response.status_code}")
    time.sleep(1)
    
    status, timestamps, error = get_message_status()
    print(f"Current status: {status}")
    print(f"Status timestamps: {timestamps}")
    print(f"Error: {error}")
    
    if status == "failed":
        print(f"✅ CRITICAL: Status became 'failed' (failed ALWAYS applies)")
        checks.append(True)
    else:
        print(f"❌ CRITICAL: Status should be 'failed', got '{status}'")
        checks.append(False)
    
    if error:
        print(f"✅ Error field present in message")
        checks.append(True)
    else:
        print(f"❌ Error field missing")
        checks.append(False)
    
    # Verify all status timestamps are present
    print("\n--- Final status_timestamps check ---")
    print(f"Status timestamps: {timestamps}")
    expected_keys = ["read", "delivered", "sent"]
    for key in expected_keys:
        if key in timestamps:
            print(f"✅ status_timestamps.{key} present")
        else:
            print(f"❌ status_timestamps.{key} missing")
            checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 4 PASSED' if success else '❌ TEST 4 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success

def test_5_webhook_get_verification():
    """TEST 5: Webhook GET verification"""
    print("\n" + "="*80)
    print("TEST 5: Webhook GET verification (public)")
    print("="*80)
    
    checks = []
    
    # Test with first verify token
    print("\n--- Test with hub.verify_token=brandsxai_wa_verify_7bK9mQ2xP4 ---")
    response = requests.get(
        f"{API_BASE}/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "TESTCHAL123",
            "hub.verify_token": "brandsxai_wa_verify_7bK9mQ2xP4"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200 and response.text == "TESTCHAL123":
        print(f"✅ Returns 200 with body 'TESTCHAL123'")
        checks.append(True)
    else:
        print(f"❌ Expected 200 with 'TESTCHAL123', got {response.status_code}: {response.text}")
        checks.append(False)
    
    # Test with second verify token
    print("\n--- Test with hub.verify_token=asdfghjkl1234567890 ---")
    response = requests.get(
        f"{API_BASE}/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "TESTCHAL123",
            "hub.verify_token": "asdfghjkl1234567890"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200 and response.text == "TESTCHAL123":
        print(f"✅ Returns 200 with body 'TESTCHAL123' (both tokens accepted)")
        checks.append(True)
    else:
        print(f"❌ Expected 200 with 'TESTCHAL123', got {response.status_code}: {response.text}")
        checks.append(False)
    
    # Test with wrong verify token
    print("\n--- Test with hub.verify_token=definitely_wrong ---")
    response = requests.get(
        f"{API_BASE}/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "TESTCHAL123",
            "hub.verify_token": "definitely_wrong"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 403:
        print(f"✅ Returns 403 for wrong token")
        checks.append(True)
    else:
        print(f"❌ Expected 403, got {response.status_code}")
        checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 5 PASSED' if success else '❌ TEST 5 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success

def test_6_webhook_traffic_counters():
    """TEST 6: Verify webhook_traffic counters increased"""
    print("\n" + "="*80)
    print("TEST 6: Verify webhook_traffic counters increased")
    print("="*80)
    
    checks = []
    
    response = requests.get(f"{API_BASE}/whatsapp/status", headers=get_headers(auth=True))
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Expected 200, got {response.status_code}")
        return False
    
    data = response.json()
    webhook_traffic = data.get("webhook_traffic", {})
    
    print(f"Webhook traffic: {json.dumps(webhook_traffic, indent=2)}")
    
    received_count = webhook_traffic.get("received_count", 0)
    processed_messages = webhook_traffic.get("processed_messages", 0)
    processed_statuses = webhook_traffic.get("processed_statuses", 0)
    
    if received_count > 0:
        print(f"✅ received_count increased: {received_count}")
        checks.append(True)
    else:
        print(f"❌ received_count should be > 0, got {received_count}")
        checks.append(False)
    
    if processed_messages >= 1:
        print(f"✅ processed_messages >= 1: {processed_messages}")
        checks.append(True)
    else:
        print(f"❌ processed_messages should be >= 1, got {processed_messages}")
        checks.append(False)
    
    if processed_statuses >= 4:
        print(f"✅ processed_statuses >= 4: {processed_statuses}")
        checks.append(True)
    else:
        print(f"❌ processed_statuses should be >= 4, got {processed_statuses}")
        checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 6 PASSED' if success else '❌ TEST 6 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success

def test_7_inbound_non_text_types():
    """TEST 7: Inbound non-text types (reaction, location)"""
    print("\n" + "="*80)
    print("TEST 7: Inbound non-text types (reaction, location)")
    print("="*80)
    
    checks = []
    fake_phone = "919000000002"
    
    # Test reaction
    print("\n--- Test reaction message ---")
    timestamp = int(time.time() * 1000)
    wamid_reaction = f"wamid.REACTION_{timestamp}"
    
    payload_reaction = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "971659015904015",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15515506716",
                        "phone_number_id": "1236101482916191"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Reaction Tester"
                        },
                        "wa_id": fake_phone
                    }],
                    "messages": [{
                        "from": fake_phone,
                        "id": wamid_reaction,
                        "timestamp": str(int(time.time())),
                        "type": "reaction",
                        "reaction": {
                            "message_id": "wamid.some_previous_message",
                            "emoji": "👍"
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    response = requests.post(
        f"{API_BASE}/whatsapp/webhook",
        json=payload_reaction,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200 and response.json().get("ok") == True:
        print(f"✅ Reaction webhook accepted")
        checks.append(True)
    else:
        print(f"❌ Reaction webhook failed: {response.status_code}")
        checks.append(False)
    
    time.sleep(1)
    
    # Get conversations to find the thread
    response = requests.get(f"{API_BASE}/whatsapp/conversations", headers=get_headers(auth=True))
    if response.status_code == 200:
        conversations = response.json().get("conversations", [])
        thread = None
        for conv in conversations:
            if conv.get("lead_phone") == fake_phone or conv.get("lead_phone") == f"91{fake_phone}":
                thread = conv
                break
        
        if thread:
            # Get conversation details
            response = requests.get(
                f"{API_BASE}/whatsapp/conversations/{thread.get('id')}",
                headers=get_headers(auth=True)
            )
            if response.status_code == 200:
                conv_data = response.json()
                messages = conv_data.get("messages", [])
                reaction_msg = next((m for m in messages if m.get("wa_message_id") == wamid_reaction), None)
                
                if reaction_msg:
                    print(f"✅ Reaction message stored")
                    content = reaction_msg.get("content", "")
                    print(f"  Content: {content}")
                    
                    # Should contain the emoji, NOT a generic placeholder like "[reaction]"
                    if "👍" in content and "[reaction]" not in content.lower():
                        print(f"  ✅ Content contains emoji '👍' (NOT generic placeholder)")
                        checks.append(True)
                    else:
                        print(f"  ❌ Content should contain emoji, not generic placeholder")
                        checks.append(False)
                else:
                    print(f"❌ Reaction message not found")
                    checks.append(False)
            else:
                print(f"❌ Failed to get conversation details")
                checks.append(False)
        else:
            print(f"❌ Thread not found for reaction")
            checks.append(False)
    else:
        print(f"❌ Failed to get conversations")
        checks.append(False)
    
    # Test location
    print("\n--- Test location message ---")
    timestamp = int(time.time() * 1000)
    wamid_location = f"wamid.LOCATION_{timestamp}"
    
    payload_location = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "971659015904015",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15515506716",
                        "phone_number_id": "1236101482916191"
                    },
                    "contacts": [{
                        "profile": {
                            "name": "Location Tester"
                        },
                        "wa_id": fake_phone
                    }],
                    "messages": [{
                        "from": fake_phone,
                        "id": wamid_location,
                        "timestamp": str(int(time.time())),
                        "type": "location",
                        "location": {
                            "latitude": 37.7749,
                            "longitude": -122.4194,
                            "name": "Showroom",
                            "address": "123 Main St"
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    response = requests.post(
        f"{API_BASE}/whatsapp/webhook",
        json=payload_location,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200 and response.json().get("ok") == True:
        print(f"✅ Location webhook accepted")
        checks.append(True)
    else:
        print(f"❌ Location webhook failed: {response.status_code}")
        checks.append(False)
    
    time.sleep(1)
    
    # Get conversation details again
    if thread:
        response = requests.get(
            f"{API_BASE}/whatsapp/conversations/{thread.get('id')}",
            headers=get_headers(auth=True)
        )
        if response.status_code == 200:
            conv_data = response.json()
            messages = conv_data.get("messages", [])
            location_msg = next((m for m in messages if m.get("wa_message_id") == wamid_location), None)
            
            if location_msg:
                print(f"✅ Location message stored")
                content = location_msg.get("content", "")
                print(f"  Content: {content}")
                
                # Should contain the location name "Showroom", NOT a generic placeholder like "[location]"
                if "Showroom" in content and "[location]" not in content.lower():
                    print(f"  ✅ Content contains location name 'Showroom' (NOT generic placeholder)")
                    checks.append(True)
                else:
                    print(f"  ❌ Content should contain location name, not generic placeholder")
                    checks.append(False)
            else:
                print(f"❌ Location message not found")
                checks.append(False)
        else:
            print(f"❌ Failed to get conversation details")
            checks.append(False)
    
    success = all(checks)
    print(f"\n{'✅ TEST 7 PASSED' if success else '❌ TEST 7 FAILED'} ({sum(checks)}/{len(checks)} checks)")
    return success

def main():
    """Run all tests"""
    print("="*80)
    print("WhatsApp AI Backend Regression Test Suite")
    print("Testing webhook signature diagnostics + out-of-order status ticks")
    print("="*80)
    
    # Login once
    if not login():
        print("\n❌ LOGIN FAILED - Cannot proceed with tests")
        return
    
    results = {}
    
    # Test 1: GET /api/whatsapp/status
    results["test_1"] = test_1_whatsapp_status()
    
    # Test 2: POST /api/whatsapp/templates/sync
    results["test_2"] = test_2_template_sync()
    
    # Test 3: Inbound message webhook
    test_3_result, wamid, conversation_id = test_3_inbound_message_webhook()
    results["test_3"] = test_3_result
    
    # Test 4: Out-of-order status ticks (MOST IMPORTANT)
    results["test_4"] = test_4_out_of_order_status_ticks(wamid, conversation_id)
    
    # Test 5: Webhook GET verification
    results["test_5"] = test_5_webhook_get_verification()
    
    # Test 6: Webhook traffic counters
    results["test_6"] = test_6_webhook_traffic_counters()
    
    # Test 7: Inbound non-text types
    results["test_7"] = test_7_inbound_non_text_types()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
