#!/usr/bin/env python3
"""
Backend test for WhatsApp AI auto-appear paths:
- PART A: System ingest endpoint (voice AI platform pushes messages)
- PART B: Meta webhook auto-creates thread for inbound
"""

import requests
import json
import sys

# Base URL from frontend/.env
BASE_URL = "https://whatsapp-lead-hub-8.preview.emergentagent.com/api"

# Test credentials
TEST_USER = "testuser"
TEST_PASS = "test123"

# Ingest token from backend/.env
INGEST_TOKEN = "brandsxai_ingest_3fJ8sN1wQ6"

def login():
    """Login and get JWT token"""
    print("\n=== LOGIN ===")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": TEST_USER,
        "password": TEST_PASS
    })
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"ERROR: Login failed - {resp.text}")
        sys.exit(1)
    data = resp.json()
    token = data.get("access_token")
    print(f"✅ Login successful, token: {token[:20]}...")
    return token

def test_part_a(token):
    """Test PART A - System ingest endpoint"""
    print("\n" + "="*80)
    print("PART A — System ingest endpoint (voice AI platform pushes messages)")
    print("="*80)
    
    results = []
    
    # Step 1: Missing/wrong token
    print("\n--- Step 1: Missing/wrong token ---")
    resp = requests.post(f"{BASE_URL}/whatsapp/ingest/message", 
        headers={"X-Ingest-Token": "WRONG"},
        json={"lead_phone": "919700000001", "content": "hi"}
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 403:
        print("✅ PASS: Wrong token correctly returns 403")
        results.append(("Step 1: Wrong token returns 403", True))
    else:
        print(f"❌ FAIL: Expected 403, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 1: Wrong token returns 403", False))
    
    # Step 2: Fire an outbound template (as voice agent would)
    print("\n--- Step 2: Fire outbound template ---")
    resp = requests.post(f"{BASE_URL}/whatsapp/ingest/message",
        headers={"X-Ingest-Token": INGEST_TOKEN},
        json={
            "lead_phone": "919700000009",
            "lead_name": "Vikram Rao",
            "campaign_name": "Voice Outreach",
            "direction": "outbound",
            "msg_type": "template",
            "template_name": "welcome_offer",
            "content": "Hi Vikram, thanks for your interest! Reply YES.",
            "wa_message_id": "wamid.TEST1"
        }
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        thread_created = data.get("thread_created", False)
        conv = data.get("conversation", {})
        msg = data.get("message", {})
        
        checks = []
        checks.append(("thread_created is true", thread_created == True))
        checks.append(("conversation exists", conv.get("id") is not None))
        checks.append(("lead_phone is 919700000009", conv.get("lead_phone") == "919700000009"))
        checks.append(("lead_name is Vikram Rao", conv.get("lead_name") == "Vikram Rao"))
        checks.append(("message sender_type is bot", msg.get("sender_type") == "bot"))
        checks.append(("message msg_type is template", msg.get("msg_type") == "template"))
        
        all_pass = all(c[1] for c in checks)
        for check_name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {check_name}")
        
        if all_pass:
            print("✅ PASS: Outbound template created conversation correctly")
            results.append(("Step 2: Outbound template creates conversation", True))
            vikram_conv_id = conv.get("id")
        else:
            print("❌ FAIL: Some checks failed")
            results.append(("Step 2: Outbound template creates conversation", False))
            vikram_conv_id = conv.get("id")
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 2: Outbound template creates conversation", False))
        vikram_conv_id = None
    
    # Step 3: Auto-appear check - login and GET conversations
    print("\n--- Step 3: Auto-appear check - Vikram Rao thread must be present ---")
    resp = requests.get(f"{BASE_URL}/whatsapp/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        conversations = data.get("conversations", [])
        print(f"Total conversations: {len(conversations)}")
        
        vikram_found = False
        for conv in conversations:
            if conv.get("lead_phone") == "919700000009":
                vikram_found = True
                print(f"✅ Found Vikram Rao conversation: {conv.get('id')}")
                print(f"   Lead name: {conv.get('lead_name')}")
                print(f"   Phone: {conv.get('lead_phone')}")
                print(f"   Stage: {conv.get('stage')}")
                break
        
        if vikram_found:
            print("✅ PASS: Vikram Rao thread appears in inbox automatically")
            results.append(("Step 3: Vikram thread auto-appears in inbox", True))
        else:
            print("❌ FAIL: Vikram Rao thread not found in conversations")
            results.append(("Step 3: Vikram thread auto-appears in inbox", False))
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 3: Vikram thread auto-appears in inbox", False))
    
    # Step 3b: GET specific conversation to verify template message
    if vikram_conv_id:
        print("\n--- Step 3b: Verify template message in conversation ---")
        resp = requests.get(f"{BASE_URL}/whatsapp/conversations/{vikram_conv_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            messages = data.get("messages", [])
            print(f"Total messages: {len(messages)}")
            
            template_found = False
            for msg in messages:
                if msg.get("msg_type") == "template" and msg.get("sender_type") == "bot":
                    template_found = True
                    print(f"✅ Found template message:")
                    print(f"   Content: {msg.get('content')}")
                    print(f"   Sender type: {msg.get('sender_type')}")
                    print(f"   Message type: {msg.get('msg_type')}")
                    break
            
            if template_found:
                print("✅ PASS: Template message present with sender_type bot")
                results.append(("Step 3b: Template message in conversation", True))
            else:
                print("❌ FAIL: Template message not found")
                results.append(("Step 3b: Template message in conversation", False))
        else:
            print(f"❌ FAIL: Expected 200, got {resp.status_code}")
            results.append(("Step 3b: Template message in conversation", False))
    
    # Step 4: Inbound via ingest
    print("\n--- Step 4: Inbound via ingest (same thread) ---")
    resp = requests.post(f"{BASE_URL}/whatsapp/ingest/message",
        headers={"X-Ingest-Token": INGEST_TOKEN},
        json={
            "lead_phone": "919700000009",
            "direction": "inbound",
            "content": "YES, interested"
        }
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        conv = data.get("conversation", {})
        msg = data.get("message", {})
        
        checks = []
        checks.append(("Same conversation ID", conv.get("id") == vikram_conv_id))
        checks.append(("Message direction is inbound", msg.get("direction") == "inbound"))
        checks.append(("Message sender_type is customer", msg.get("sender_type") == "customer"))
        checks.append(("Message content correct", msg.get("content") == "YES, interested"))
        
        all_pass = all(c[1] for c in checks)
        for check_name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {check_name}")
        
        if all_pass:
            print("✅ PASS: Inbound message added to same thread (no duplicate)")
            results.append(("Step 4: Inbound message to same thread", True))
        else:
            print("❌ FAIL: Some checks failed")
            results.append(("Step 4: Inbound message to same thread", False))
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 4: Inbound message to same thread", False))
    
    # Step 5: Idempotency - same wa_message_id
    print("\n--- Step 5: Idempotency check (same wa_message_id) ---")
    resp = requests.post(f"{BASE_URL}/whatsapp/ingest/message",
        headers={"X-Ingest-Token": INGEST_TOKEN},
        json={
            "lead_phone": "919700000009",
            "lead_name": "Vikram Rao",
            "campaign_name": "Voice Outreach",
            "direction": "outbound",
            "msg_type": "template",
            "template_name": "welcome_offer",
            "content": "Hi Vikram, thanks for your interest! Reply YES.",
            "wa_message_id": "wamid.TEST1"  # Same as step 2
        }
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        duplicate = data.get("duplicate", False)
        
        if duplicate:
            print("✅ PASS: Duplicate detected (duplicate: true)")
            results.append(("Step 5: Idempotency (duplicate detection)", True))
            
            # Verify no second copy in thread
            if vikram_conv_id:
                resp2 = requests.get(f"{BASE_URL}/whatsapp/conversations/{vikram_conv_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if resp2.status_code == 200:
                    messages = resp2.json().get("messages", [])
                    template_count = sum(1 for m in messages if m.get("wa_message_id") == "wamid.TEST1")
                    print(f"  Template messages with wamid.TEST1: {template_count}")
                    if template_count == 1:
                        print("  ✅ Only one copy exists (no duplicate)")
                    else:
                        print(f"  ❌ Found {template_count} copies (expected 1)")
        else:
            print("❌ FAIL: Duplicate not detected")
            results.append(("Step 5: Idempotency (duplicate detection)", False))
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 5: Idempotency (duplicate detection)", False))
    
    # Step 6: Validation - short phone
    print("\n--- Step 6: Validation - short phone ---")
    resp = requests.post(f"{BASE_URL}/whatsapp/ingest/message",
        headers={"X-Ingest-Token": INGEST_TOKEN},
        json={
            "lead_phone": "123",
            "content": "x"
        }
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 400:
        print("✅ PASS: Short phone correctly returns 400")
        results.append(("Step 6: Validation (short phone)", True))
    else:
        print(f"❌ FAIL: Expected 400, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 6: Validation (short phone)", False))
    
    return results

def test_part_b(token):
    """Test PART B - Meta webhook auto-creates thread"""
    print("\n" + "="*80)
    print("PART B — Meta webhook auto-creates thread for inbound")
    print("="*80)
    
    results = []
    
    # Step 7: POST webhook with realistic Meta payload
    print("\n--- Step 7: POST webhook with Meta payload ---")
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "PNID"},
                    "messages": [{
                        "from": "919733000077",
                        "id": "wamid.INB1",
                        "timestamp": "1700000000",
                        "type": "text",
                        "text": {"body": "Hello from customer"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/whatsapp/webhook",
        json=webhook_payload
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("ok") == True:
            print("✅ PASS: Webhook returns 200 with ok: true")
            results.append(("Step 7: Webhook accepts Meta payload", True))
        else:
            print("❌ FAIL: Response does not have ok: true")
            results.append(("Step 7: Webhook accepts Meta payload", False))
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 7: Webhook accepts Meta payload", False))
    
    # Step 8: Auto-appear check - thread for 919733000077 exists
    print("\n--- Step 8: Auto-appear check - thread for 919733000077 ---")
    resp = requests.get(f"{BASE_URL}/whatsapp/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        conversations = data.get("conversations", [])
        print(f"Total conversations: {len(conversations)}")
        
        webhook_conv_found = False
        webhook_conv_id = None
        for conv in conversations:
            if conv.get("lead_phone") == "919733000077":
                webhook_conv_found = True
                webhook_conv_id = conv.get("id")
                print(f"✅ Found webhook-created conversation: {webhook_conv_id}")
                print(f"   Phone: {conv.get('lead_phone')}")
                print(f"   Stage: {conv.get('stage')}")
                break
        
        if webhook_conv_found:
            print("✅ PASS: Webhook auto-created thread appears in inbox")
            results.append(("Step 8: Webhook thread auto-appears", True))
            
            # Verify the inbound message
            print("\n--- Step 8b: Verify inbound message in webhook thread ---")
            resp2 = requests.get(f"{BASE_URL}/whatsapp/conversations/{webhook_conv_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp2.status_code == 200:
                data2 = resp2.json()
                messages = data2.get("messages", [])
                print(f"Total messages: {len(messages)}")
                
                inbound_found = False
                for msg in messages:
                    if msg.get("content") == "Hello from customer":
                        inbound_found = True
                        print(f"✅ Found inbound message:")
                        print(f"   Content: {msg.get('content')}")
                        print(f"   Direction: {msg.get('direction')}")
                        print(f"   Sender type: {msg.get('sender_type')}")
                        
                        checks = []
                        checks.append(("Direction is inbound", msg.get("direction") == "inbound"))
                        checks.append(("Sender type is customer", msg.get("sender_type") == "customer"))
                        
                        all_pass = all(c[1] for c in checks)
                        for check_name, passed in checks:
                            print(f"  {'✅' if passed else '❌'} {check_name}")
                        
                        if all_pass:
                            results.append(("Step 8b: Inbound message correct", True))
                        else:
                            results.append(("Step 8b: Inbound message correct", False))
                        break
                
                if not inbound_found:
                    print("❌ FAIL: Inbound message not found")
                    results.append(("Step 8b: Inbound message correct", False))
            else:
                print(f"❌ FAIL: Could not get conversation details")
                results.append(("Step 8b: Inbound message correct", False))
        else:
            print("❌ FAIL: Webhook thread not found in conversations")
            results.append(("Step 8: Webhook thread auto-appears", False))
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 8: Webhook thread auto-appears", False))
    
    # Step 9: Webhook idempotency
    print("\n--- Step 9: Webhook idempotency (same message id) ---")
    resp = requests.post(f"{BASE_URL}/whatsapp/webhook",
        json=webhook_payload  # Same payload as step 7
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ Webhook accepted duplicate payload")
        
        # Verify only ONE message with that ID exists
        if webhook_conv_id:
            resp2 = requests.get(f"{BASE_URL}/whatsapp/conversations/{webhook_conv_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp2.status_code == 200:
                messages = resp2.json().get("messages", [])
                inbound_count = sum(1 for m in messages if m.get("wa_message_id") == "wamid.INB1")
                print(f"Messages with wamid.INB1: {inbound_count}")
                
                if inbound_count == 1:
                    print("✅ PASS: Only one copy exists (webhook idempotency works)")
                    results.append(("Step 9: Webhook idempotency", True))
                else:
                    print(f"❌ FAIL: Found {inbound_count} copies (expected 1)")
                    results.append(("Step 9: Webhook idempotency", False))
            else:
                print("❌ FAIL: Could not verify message count")
                results.append(("Step 9: Webhook idempotency", False))
        else:
            print("❌ FAIL: No conversation ID to check")
            results.append(("Step 9: Webhook idempotency", False))
    else:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        results.append(("Step 9: Webhook idempotency", False))
    
    return results

def main():
    print("="*80)
    print("WhatsApp AI Auto-Appear Paths Testing")
    print("="*80)
    
    # Login
    token = login()
    
    # Test Part A
    part_a_results = test_part_a(token)
    
    # Test Part B
    part_b_results = test_part_b(token)
    
    # Summary
    all_results = part_a_results + part_b_results
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print("\nPART A - System ingest endpoint:")
    for name, result in part_a_results:
        print(f"  {'✅' if result else '❌'} {name}")
    
    print("\nPART B - Meta webhook:")
    for name, result in part_b_results:
        print(f"  {'✅' if result else '❌'} {name}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {passed}/{total} tests passed")
    print(f"{'='*80}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
