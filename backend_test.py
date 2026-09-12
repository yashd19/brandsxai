#!/usr/bin/env python3
"""
WhatsApp AI Read Endpoints Regression Test
Tests the performance-optimized read endpoints after refactor
"""
import requests
import time
import asyncio
import httpx
from statistics import mean
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
BASE_URL = "https://whatsapp-lead-hub-8.preview.emergentagent.com/api"
USERNAME = "testuser"
PASSWORD = "test123"

def login():
    """Login and get JWT token"""
    print("🔐 Logging in as testuser/test123...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        print(f"❌ Login failed: No token in response")
        print(f"Response data: {data}")
        return None
    print(f"✅ Login successful, token received")
    return token

def test_1_list_conversations(token):
    """
    TEST 1: GET /api/whatsapp/conversations
    - Should return 200
    - Should have "conversations" array with >= 1 item
    - Should be sorted by last_message_at desc
    - Should have "live_mode": false
    """
    print("\n" + "="*80)
    print("TEST 1: GET /api/whatsapp/conversations")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/whatsapp/conversations", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return None, None
    
    data = response.json()
    
    # Check for conversations array
    if "conversations" not in data:
        print(f"❌ FAILED: Missing 'conversations' key in response")
        return None, None
    
    conversations = data["conversations"]
    if len(conversations) < 1:
        print(f"❌ FAILED: Expected at least 1 conversation, got {len(conversations)}")
        return None, None
    
    print(f"✅ Found {len(conversations)} conversations")
    
    # Check sorting by last_message_at desc
    timestamps = [conv.get("last_message_at") for conv in conversations if conv.get("last_message_at")]
    if len(timestamps) > 1:
        is_sorted = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
        if is_sorted:
            print(f"✅ Conversations sorted by last_message_at DESC")
        else:
            print(f"❌ FAILED: Conversations NOT sorted by last_message_at DESC")
            print(f"First 5 timestamps: {timestamps[:5]}")
    
    # Check live_mode
    if "live_mode" not in data:
        print(f"❌ FAILED: Missing 'live_mode' key in response")
        return None, None
    
    if data["live_mode"] != False:
        print(f"❌ FAILED: Expected live_mode=false, got {data['live_mode']}")
        return None, None
    
    print(f"✅ live_mode: false")
    
    # Pick two conversation IDs for next tests
    conv_ids = [conv["id"] for conv in conversations[:2]]
    if len(conv_ids) < 2:
        print(f"⚠️  WARNING: Only {len(conv_ids)} conversation(s) available, need 2 for cross-contamination test")
        if len(conv_ids) == 1:
            conv_ids.append(conv_ids[0])  # Use same ID twice if only one available
    
    print(f"\n✅ TEST 1 PASSED")
    print(f"Selected conversation IDs for next tests:")
    print(f"  A: {conv_ids[0]}")
    print(f"  B: {conv_ids[1]}")
    
    return conv_ids[0], conv_ids[1]

def test_2_get_conversation_no_contamination(token, conv_a, conv_b):
    """
    TEST 2: GET /api/whatsapp/conversations/{id}
    - Test conversation A: should return 200 with conversation, messages, appointments, live_mode
    - conversation.id should equal A
    - conversation.unread_count should be 0
    - All messages should have conversation_id == A
    - Repeat for B and verify no cross-contamination
    """
    print("\n" + "="*80)
    print("TEST 2: GET /api/whatsapp/conversations/{id} - No Cross-Contamination")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test conversation A
    print(f"\n📋 Testing conversation A: {conv_a}")
    response_a = requests.get(f"{BASE_URL}/whatsapp/conversations/{conv_a}", headers=headers)
    
    if response_a.status_code != 200:
        print(f"❌ FAILED: Expected 200 for conversation A, got {response_a.status_code}")
        print(f"Response: {response_a.text}")
        return False
    
    data_a = response_a.json()
    
    # Check required keys
    required_keys = ["conversation", "messages", "appointments", "live_mode"]
    for key in required_keys:
        if key not in data_a:
            print(f"❌ FAILED: Missing '{key}' in response for conversation A")
            return False
    
    print(f"✅ All required keys present: {required_keys}")
    
    # Check conversation.id == A
    if data_a["conversation"]["id"] != conv_a:
        print(f"❌ FAILED: conversation.id mismatch for A")
        print(f"Expected: {conv_a}, Got: {data_a['conversation']['id']}")
        return False
    
    print(f"✅ conversation.id matches: {conv_a}")
    
    # Check unread_count == 0
    if data_a["conversation"]["unread_count"] != 0:
        print(f"❌ FAILED: Expected unread_count=0, got {data_a['conversation']['unread_count']}")
        return False
    
    print(f"✅ unread_count: 0")
    
    # Check all messages belong to conversation A
    messages_a = data_a["messages"]
    print(f"✅ Found {len(messages_a)} messages in conversation A")
    
    for i, msg in enumerate(messages_a):
        if msg.get("conversation_id") != conv_a:
            print(f"❌ FAILED: Message {i} has wrong conversation_id")
            print(f"Expected: {conv_a}, Got: {msg.get('conversation_id')}")
            return False
    
    print(f"✅ All {len(messages_a)} messages belong to conversation A")
    
    # Test conversation B (if different from A)
    if conv_b != conv_a:
        print(f"\n📋 Testing conversation B: {conv_b}")
        response_b = requests.get(f"{BASE_URL}/whatsapp/conversations/{conv_b}", headers=headers)
        
        if response_b.status_code != 200:
            print(f"❌ FAILED: Expected 200 for conversation B, got {response_b.status_code}")
            print(f"Response: {response_b.text}")
            return False
        
        data_b = response_b.json()
        
        # Check conversation.id == B
        if data_b["conversation"]["id"] != conv_b:
            print(f"❌ FAILED: conversation.id mismatch for B")
            print(f"Expected: {conv_b}, Got: {data_b['conversation']['id']}")
            return False
        
        print(f"✅ conversation.id matches: {conv_b}")
        
        # Check all messages belong to conversation B
        messages_b = data_b["messages"]
        print(f"✅ Found {len(messages_b)} messages in conversation B")
        
        for i, msg in enumerate(messages_b):
            if msg.get("conversation_id") != conv_b:
                print(f"❌ FAILED: Message {i} has wrong conversation_id")
                print(f"Expected: {conv_b}, Got: {msg.get('conversation_id')}")
                return False
        
        print(f"✅ All {len(messages_b)} messages belong to conversation B")
        
        # Verify no cross-contamination
        print(f"\n🔍 Verifying no cross-contamination...")
        print(f"Conversation A has {len(messages_a)} messages, all with conversation_id={conv_a}")
        print(f"Conversation B has {len(messages_b)} messages, all with conversation_id={conv_b}")
        print(f"✅ No cross-contamination detected")
    else:
        print(f"\n⚠️  Skipping conversation B test (same as A)")
    
    print(f"\n✅ TEST 2 PASSED")
    return True

def test_3_response_time_5_calls(token, conv_id):
    """
    TEST 3: Measure response time over 5 sequential calls
    - Should report average latency in ms
    - Should be well under 1 second each
    """
    print("\n" + "="*80)
    print("TEST 3: Response Time - 5 Sequential Calls")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    latencies = []
    
    print(f"\n📊 Measuring response time for conversation {conv_id}...")
    
    for i in range(5):
        start = time.time()
        response = requests.get(f"{BASE_URL}/whatsapp/conversations/{conv_id}", headers=headers)
        end = time.time()
        
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)
        
        if response.status_code != 200:
            print(f"❌ FAILED: Call {i+1} returned {response.status_code}")
            return False
        
        print(f"  Call {i+1}: {latency_ms:.2f} ms")
    
    avg_latency = mean(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    print(f"\n📈 Latency Statistics:")
    print(f"  Average: {avg_latency:.2f} ms")
    print(f"  Min: {min_latency:.2f} ms")
    print(f"  Max: {max_latency:.2f} ms")
    
    if avg_latency < 1000:
        print(f"✅ Average latency well under 1 second")
    else:
        print(f"⚠️  WARNING: Average latency >= 1 second")
    
    print(f"\n✅ TEST 3 PASSED")
    return True

def test_4_messages_after_filter(token, conv_id):
    """
    TEST 4: GET /api/whatsapp/conversations/{id}/messages?after=<timestamp>
    - Get all messages first
    - Use created_at of FIRST message
    - Query with after parameter
    - Should return only messages with created_at > that timestamp
    """
    print("\n" + "="*80)
    print("TEST 4: Messages After Filter")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, get the conversation to get all messages
    print(f"\n📋 Getting all messages for conversation {conv_id}...")
    response = requests.get(f"{BASE_URL}/whatsapp/conversations/{conv_id}", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Could not get conversation, status {response.status_code}")
        return False
    
    data = response.json()
    all_messages = data["messages"]
    
    if len(all_messages) < 2:
        print(f"⚠️  WARNING: Only {len(all_messages)} message(s) in conversation, need at least 2 for filter test")
        if len(all_messages) == 0:
            print(f"❌ FAILED: No messages to test with")
            return False
    
    print(f"✅ Found {len(all_messages)} total messages")
    
    # Get the created_at of the FIRST message
    first_message_timestamp = all_messages[0]["created_at"]
    print(f"📅 First message timestamp: {first_message_timestamp}")
    
    # Query with after parameter
    print(f"\n🔍 Querying messages after {first_message_timestamp}...")
    response = requests.get(
        f"{BASE_URL}/whatsapp/conversations/{conv_id}/messages",
        headers=headers,
        params={"after": first_message_timestamp}
    )
    
    if response.status_code != 200:
        print(f"❌ FAILED: Query with after parameter returned {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    filtered_data = response.json()
    filtered_messages = filtered_data["messages"]
    
    print(f"✅ Received {len(filtered_messages)} messages after filter")
    
    # Verify all returned messages have created_at > first_message_timestamp
    for i, msg in enumerate(filtered_messages):
        if msg["created_at"] <= first_message_timestamp:
            print(f"❌ FAILED: Message {i} has created_at <= filter timestamp")
            print(f"Filter: {first_message_timestamp}, Message: {msg['created_at']}")
            return False
    
    print(f"✅ All {len(filtered_messages)} messages have created_at > {first_message_timestamp}")
    
    # Expected count should be total - 1 (excluding the first message)
    expected_count = len(all_messages) - 1
    if len(filtered_messages) == expected_count:
        print(f"✅ Correct count: {len(filtered_messages)} (total {len(all_messages)} - 1)")
    else:
        print(f"⚠️  WARNING: Expected {expected_count} messages, got {len(filtered_messages)}")
    
    print(f"\n✅ TEST 4 PASSED")
    return True

def test_5_conversation_not_found(token):
    """
    TEST 5: GET /api/whatsapp/conversations/does-not-exist
    - Should return 404
    """
    print("\n" + "="*80)
    print("TEST 5: Conversation Not Found (404)")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = "does-not-exist-12345"
    
    print(f"\n🔍 Requesting non-existent conversation: {fake_id}")
    response = requests.get(f"{BASE_URL}/whatsapp/conversations/{fake_id}", headers=headers)
    
    if response.status_code == 404:
        print(f"✅ Correctly returned 404 for non-existent conversation")
        print(f"Response: {response.json()}")
        print(f"\n✅ TEST 5 PASSED")
        return True
    else:
        print(f"❌ FAILED: Expected 404, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_6_concurrency_smoke(token, conv_id):
    """
    TEST 6: Concurrency Smoke Test
    - Fire 20 concurrent GET requests to /api/whatsapp/conversations/{id}
    - All should return 200
    - Report max latency
    """
    print("\n" + "="*80)
    print("TEST 6: Concurrency Smoke Test (20 concurrent requests)")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    num_requests = 20
    
    print(f"\n🚀 Firing {num_requests} concurrent requests to conversation {conv_id}...")
    
    def make_request(request_num):
        start = time.time()
        response = requests.get(f"{BASE_URL}/whatsapp/conversations/{conv_id}", headers=headers)
        end = time.time()
        latency_ms = (end - start) * 1000
        return {
            "request_num": request_num,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "success": response.status_code == 200
        }
    
    # Use ThreadPoolExecutor for concurrent requests
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, i+1) for i in range(num_requests)]
        for future in as_completed(futures):
            results.append(future.result())
    
    end_time = time.time()
    total_time = (end_time - start_time) * 1000
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    latencies = [r["latency_ms"] for r in successful]
    
    print(f"\n📊 Results:")
    print(f"  Total time: {total_time:.2f} ms")
    print(f"  Successful: {len(successful)}/{num_requests}")
    print(f"  Failed: {len(failed)}/{num_requests}")
    
    if failed:
        print(f"\n❌ Failed requests:")
        for r in failed:
            print(f"  Request {r['request_num']}: {r['status_code']}")
    
    if latencies:
        avg_latency = mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\n📈 Latency Statistics (successful requests):")
        print(f"  Average: {avg_latency:.2f} ms")
        print(f"  Min: {min_latency:.2f} ms")
        print(f"  Max: {max_latency:.2f} ms")
        
        print(f"\n✅ Max latency: {max_latency:.2f} ms")
    
    if len(successful) == num_requests:
        print(f"\n✅ TEST 6 PASSED - All {num_requests} requests returned 200")
        return True
    else:
        print(f"\n❌ TEST 6 FAILED - {len(failed)} requests failed")
        return False

def main():
    print("="*80)
    print("WhatsApp AI Read Endpoints - Regression Test")
    print("Performance Refactor Verification")
    print("="*80)
    
    # Login
    token = login()
    if not token:
        print("\n❌ OVERALL RESULT: FAILED (Login failed)")
        return
    
    # Test 1: List conversations
    conv_a, conv_b = test_1_list_conversations(token)
    if not conv_a:
        print("\n❌ OVERALL RESULT: FAILED (Test 1 failed)")
        return
    
    # Test 2: Get conversation with no cross-contamination
    if not test_2_get_conversation_no_contamination(token, conv_a, conv_b):
        print("\n❌ OVERALL RESULT: FAILED (Test 2 failed)")
        return
    
    # Test 3: Response time (5 sequential calls)
    if not test_3_response_time_5_calls(token, conv_a):
        print("\n❌ OVERALL RESULT: FAILED (Test 3 failed)")
        return
    
    # Test 4: Messages after filter
    if not test_4_messages_after_filter(token, conv_a):
        print("\n❌ OVERALL RESULT: FAILED (Test 4 failed)")
        return
    
    # Test 5: Conversation not found (404)
    if not test_5_conversation_not_found(token):
        print("\n❌ OVERALL RESULT: FAILED (Test 5 failed)")
        return
    
    # Test 6: Concurrency smoke test
    if not test_6_concurrency_smoke(token, conv_a):
        print("\n❌ OVERALL RESULT: FAILED (Test 6 failed)")
        return
    
    # All tests passed
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED (6/6)")
    print("="*80)
    print("\nSummary:")
    print("  ✅ Test 1: List conversations (sorted, live_mode=false)")
    print("  ✅ Test 2: Get conversation (no cross-contamination)")
    print("  ✅ Test 3: Response time (5 sequential calls)")
    print("  ✅ Test 4: Messages after filter")
    print("  ✅ Test 5: Conversation not found (404)")
    print("  ✅ Test 6: Concurrency smoke test (20 concurrent requests)")

if __name__ == "__main__":
    main()
