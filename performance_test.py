#!/usr/bin/env python3
"""
Performance test for WhatsApp AI endpoints after event-loop fix.
Tests sequential baseline vs concurrent load to verify blocking is resolved.
"""
import asyncio
import httpx
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any

# Configuration
BASE_URL = "https://whatsapp-lead-hub-8.preview.emergentagent.com"
USERNAME = "testuser"
PASSWORD = "test123"

class PerformanceTest:
    def __init__(self):
        self.token = None
        self.conversation_id = None
        self.base_url = BASE_URL
        
    def login(self) -> str:
        """Login once and get Bearer token"""
        print("=" * 80)
        print("STEP 0: Authentication")
        print("=" * 80)
        
        response = httpx.post(
            f"{self.base_url}/api/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        self.token = data.get("access_token")
        
        if not self.token:
            raise Exception("No access_token in login response")
        
        print(f"✅ Login successful: {USERNAME}")
        print(f"   Token: {self.token[:20]}...")
        return self.token
    
    def get_conversation_id(self) -> str:
        """Get a conversation ID from the list"""
        print("\n" + "=" * 80)
        print("STEP 0.5: Get Conversation ID")
        print("=" * 80)
        
        response = httpx.get(
            f"{self.base_url}/api/whatsapp/conversations",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get conversations: {response.status_code}")
        
        data = response.json()
        conversations = data.get("conversations", [])
        
        if not conversations:
            raise Exception("No conversations found")
        
        self.conversation_id = conversations[0]["id"]
        print(f"✅ Using conversation ID: {self.conversation_id}")
        print(f"   Lead: {conversations[0].get('lead_name', 'Unknown')}")
        print(f"   Phone: {conversations[0].get('lead_phone', 'Unknown')}")
        return self.conversation_id
    
    def sequential_baseline(self, count: int = 5) -> Dict[str, Any]:
        """Test 1: Sequential baseline - measure single-request latency"""
        print("\n" + "=" * 80)
        print(f"TEST 1: Sequential Baseline ({count} requests)")
        print("=" * 80)
        
        latencies = []
        
        for i in range(count):
            start = time.time()
            response = httpx.get(
                f"{self.base_url}/api/whatsapp/conversations/{self.conversation_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0
            )
            latency = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code != 200:
                print(f"❌ Request {i+1} failed: {response.status_code}")
            else:
                latencies.append(latency)
                print(f"   Request {i+1}: {latency:.2f}ms - Status: {response.status_code}")
        
        if not latencies:
            raise Exception("All sequential requests failed")
        
        result = {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "avg": statistics.mean(latencies),
            "median": statistics.median(latencies)
        }
        
        print(f"\n📊 Sequential Baseline Results:")
        print(f"   Count: {result['count']}")
        print(f"   Min:   {result['min']:.2f}ms")
        print(f"   Avg:   {result['avg']:.2f}ms")
        print(f"   Max:   {result['max']:.2f}ms")
        print(f"   Median: {result['median']:.2f}ms")
        
        return result
    
    async def concurrent_single_endpoint(self, count: int = 20) -> Dict[str, Any]:
        """Test 2: Concurrent requests to single endpoint"""
        print("\n" + "=" * 80)
        print(f"TEST 2: Concurrency {count} (Single Endpoint)")
        print("=" * 80)
        
        async def fetch_conversation(client: httpx.AsyncClient, index: int):
            start = time.time()
            response = await client.get(
                f"{self.base_url}/api/whatsapp/conversations/{self.conversation_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0
            )
            latency = (time.time() - start) * 1000
            return {
                "index": index,
                "status": response.status_code,
                "latency": latency,
                "data": response.json() if response.status_code == 200 else None
            }
        
        wall_start = time.time()
        
        async with httpx.AsyncClient() as client:
            tasks = [fetch_conversation(client, i) for i in range(count)]
            results = await asyncio.gather(*tasks)
        
        wall_time = (time.time() - wall_start) * 1000
        
        # Analyze results
        latencies = [r["latency"] for r in results if r["status"] == 200]
        failed = [r for r in results if r["status"] != 200]
        
        if failed:
            print(f"❌ {len(failed)} requests failed:")
            for r in failed[:5]:  # Show first 5 failures
                print(f"   Request {r['index']}: Status {r['status']}")
        
        if not latencies:
            raise Exception("All concurrent requests failed")
        
        # Calculate p95
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95 = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
        
        result = {
            "count": len(latencies),
            "failed": len(failed),
            "min": min(latencies),
            "max": max(latencies),
            "avg": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": p95,
            "wall_time": wall_time,
            "results": results
        }
        
        print(f"\n📊 Concurrent Test Results:")
        print(f"   Total:     {count}")
        print(f"   Success:   {result['count']}")
        print(f"   Failed:    {result['failed']}")
        print(f"   Min:       {result['min']:.2f}ms")
        print(f"   Avg:       {result['avg']:.2f}ms")
        print(f"   Median:    {result['median']:.2f}ms")
        print(f"   P95:       {result['p95']:.2f}ms")
        print(f"   Max:       {result['max']:.2f}ms")
        print(f"   Wall Time: {wall_time:.2f}ms")
        
        return result
    
    async def concurrent_mixed_endpoints(self, count: int = 50) -> Dict[str, Any]:
        """Test 3: Concurrent mixed requests (list, get, messages)"""
        print("\n" + "=" * 80)
        print(f"TEST 3: Concurrency {count} (Mixed Endpoints)")
        print("=" * 80)
        
        async def fetch_mixed(client: httpx.AsyncClient, index: int):
            # Distribute requests across 3 endpoint types
            endpoint_type = index % 3
            
            start = time.time()
            
            if endpoint_type == 0:
                # GET list
                url = f"{self.base_url}/api/whatsapp/conversations"
                endpoint_name = "list"
            elif endpoint_type == 1:
                # GET conversation
                url = f"{self.base_url}/api/whatsapp/conversations/{self.conversation_id}"
                endpoint_name = "get_conversation"
            else:
                # GET messages with after filter
                url = f"{self.base_url}/api/whatsapp/conversations/{self.conversation_id}/messages?after=2020-01-01T00:00:00"
                endpoint_name = "get_messages"
            
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0
            )
            
            latency = (time.time() - start) * 1000
            
            return {
                "index": index,
                "endpoint": endpoint_name,
                "status": response.status_code,
                "latency": latency,
                "data": response.json() if response.status_code == 200 else None
            }
        
        wall_start = time.time()
        
        async with httpx.AsyncClient() as client:
            tasks = [fetch_mixed(client, i) for i in range(count)]
            results = await asyncio.gather(*tasks)
        
        wall_time = (time.time() - wall_start) * 1000
        
        # Analyze results by endpoint type
        by_endpoint = {}
        for r in results:
            endpoint = r["endpoint"]
            if endpoint not in by_endpoint:
                by_endpoint[endpoint] = {"latencies": [], "failed": 0}
            
            if r["status"] == 200:
                by_endpoint[endpoint]["latencies"].append(r["latency"])
            else:
                by_endpoint[endpoint]["failed"] += 1
        
        # Overall stats
        all_latencies = [r["latency"] for r in results if r["status"] == 200]
        failed_count = len([r for r in results if r["status"] != 200])
        
        if not all_latencies:
            raise Exception("All mixed concurrent requests failed")
        
        # Calculate p95
        sorted_latencies = sorted(all_latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95 = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
        
        result = {
            "count": len(all_latencies),
            "failed": failed_count,
            "min": min(all_latencies),
            "max": max(all_latencies),
            "avg": statistics.mean(all_latencies),
            "median": statistics.median(all_latencies),
            "p95": p95,
            "wall_time": wall_time,
            "by_endpoint": by_endpoint,
            "results": results
        }
        
        print(f"\n📊 Mixed Concurrent Test Results:")
        print(f"   Total:     {count}")
        print(f"   Success:   {result['count']}")
        print(f"   Failed:    {result['failed']}")
        print(f"   Min:       {result['min']:.2f}ms")
        print(f"   Avg:       {result['avg']:.2f}ms")
        print(f"   Median:    {result['median']:.2f}ms")
        print(f"   P95:       {result['p95']:.2f}ms")
        print(f"   Max:       {result['max']:.2f}ms")
        print(f"   Wall Time: {wall_time:.2f}ms")
        
        print(f"\n   By Endpoint:")
        for endpoint, stats in by_endpoint.items():
            if stats["latencies"]:
                avg = statistics.mean(stats["latencies"])
                print(f"      {endpoint}: avg={avg:.2f}ms, count={len(stats['latencies'])}, failed={stats['failed']}")
        
        return result
    
    def verify_correctness(self, concurrent_results: List[Dict[str, Any]]) -> bool:
        """Test 5: Verify correctness - all responses have correct IDs"""
        print("\n" + "=" * 80)
        print("TEST 5: Correctness Verification")
        print("=" * 80)
        
        errors = []
        
        for r in concurrent_results:
            if r["status"] != 200 or not r["data"]:
                continue
            
            data = r["data"]
            
            # Check conversation.id
            if "conversation" in data:
                conv = data["conversation"]
                if conv.get("id") != self.conversation_id:
                    errors.append(f"Request {r['index']}: conversation.id mismatch - expected {self.conversation_id}, got {conv.get('id')}")
                
                # Check messages
                messages = conv.get("messages", [])
                for msg in messages:
                    if msg.get("conversation_id") != self.conversation_id:
                        errors.append(f"Request {r['index']}: message.conversation_id mismatch - expected {self.conversation_id}, got {msg.get('conversation_id')}")
        
        if errors:
            print(f"❌ Correctness check FAILED:")
            for err in errors[:10]:  # Show first 10 errors
                print(f"   {err}")
            return False
        else:
            print(f"✅ Correctness check PASSED:")
            print(f"   All {len(concurrent_results)} responses have correct conversation.id")
            print(f"   All messages have correct conversation_id")
            return True
    
    async def run_all_tests(self):
        """Run all performance tests"""
        print("\n" + "=" * 80)
        print("WhatsApp AI Performance Test Suite")
        print("Testing event-loop fix effectiveness")
        print("=" * 80)
        
        # Step 0: Login and get conversation ID
        self.login()
        self.get_conversation_id()
        
        # Test 1: Sequential baseline
        sequential_result = self.sequential_baseline(count=5)
        
        # Test 2: Concurrency 20 (first run)
        concurrent_20_result_1 = await self.concurrent_single_endpoint(count=20)
        
        # Test 3: Concurrency 50 mixed
        concurrent_50_mixed_result = await self.concurrent_mixed_endpoints(count=50)
        
        # Wait 5 seconds
        print("\n⏳ Waiting 5 seconds before repeat test...")
        await asyncio.sleep(5)
        
        # Test 4: Concurrency 20 (repeat)
        concurrent_20_result_2 = await self.concurrent_single_endpoint(count=20)
        
        # Test 5: Verify correctness
        correctness_ok = self.verify_correctness(concurrent_20_result_1["results"])
        
        # Final summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        
        print(f"\n1. Sequential Baseline (5 requests):")
        print(f"   Min: {sequential_result['min']:.2f}ms")
        print(f"   Avg: {sequential_result['avg']:.2f}ms")
        print(f"   Max: {sequential_result['max']:.2f}ms")
        
        print(f"\n2. Concurrency 20 - First Run:")
        print(f"   Min: {concurrent_20_result_1['min']:.2f}ms")
        print(f"   Avg: {concurrent_20_result_1['avg']:.2f}ms")
        print(f"   P95: {concurrent_20_result_1['p95']:.2f}ms")
        print(f"   Max: {concurrent_20_result_1['max']:.2f}ms")
        print(f"   Wall Time: {concurrent_20_result_1['wall_time']:.2f}ms")
        
        print(f"\n3. Concurrency 50 Mixed:")
        print(f"   Min: {concurrent_50_mixed_result['min']:.2f}ms")
        print(f"   Avg: {concurrent_50_mixed_result['avg']:.2f}ms")
        print(f"   P95: {concurrent_50_mixed_result['p95']:.2f}ms")
        print(f"   Max: {concurrent_50_mixed_result['max']:.2f}ms")
        print(f"   Wall Time: {concurrent_50_mixed_result['wall_time']:.2f}ms")
        
        print(f"\n4. Concurrency 20 - Second Run (consistency check):")
        print(f"   Min: {concurrent_20_result_2['min']:.2f}ms")
        print(f"   Avg: {concurrent_20_result_2['avg']:.2f}ms")
        print(f"   P95: {concurrent_20_result_2['p95']:.2f}ms")
        print(f"   Max: {concurrent_20_result_2['max']:.2f}ms")
        print(f"   Wall Time: {concurrent_20_result_2['wall_time']:.2f}ms")
        
        print(f"\n5. Correctness: {'✅ PASSED' if correctness_ok else '❌ FAILED'}")
        
        # Effectiveness analysis
        print("\n" + "=" * 80)
        print("EFFECTIVENESS ANALYSIS")
        print("=" * 80)
        
        sequential_avg = sequential_result['avg']
        concurrent_avg_1 = concurrent_20_result_1['avg']
        concurrent_avg_2 = concurrent_20_result_2['avg']
        
        ratio_1 = concurrent_avg_1 / sequential_avg
        ratio_2 = concurrent_avg_2 / sequential_avg
        
        print(f"\nSequential baseline avg: {sequential_avg:.2f}ms")
        print(f"Concurrent avg (run 1):  {concurrent_avg_1:.2f}ms ({ratio_1:.2f}x sequential)")
        print(f"Concurrent avg (run 2):  {concurrent_avg_2:.2f}ms ({ratio_2:.2f}x sequential)")
        
        # Determine if fix is effective
        # If concurrent latencies are close to sequential (within 2x), fix is effective
        # If concurrent latencies are clustered around 2000-2500ms, fix is NOT effective
        
        if concurrent_avg_1 > 2000 and concurrent_avg_2 > 2000:
            print(f"\n❌ FIX NOT EFFECTIVE:")
            print(f"   Concurrent latencies still clustered around 2-2.5s")
            print(f"   Event loop is still being blocked")
        elif ratio_1 < 2.0 and ratio_2 < 2.0:
            print(f"\n✅ FIX EFFECTIVE:")
            print(f"   Concurrent latencies are close to sequential baseline")
            print(f"   Event loop blocking has been resolved")
        else:
            print(f"\n⚠️  PARTIAL IMPROVEMENT:")
            print(f"   Concurrent latencies improved but not optimal")
            print(f"   Some blocking may still exist")
        
        return {
            "sequential": sequential_result,
            "concurrent_20_run1": concurrent_20_result_1,
            "concurrent_50_mixed": concurrent_50_mixed_result,
            "concurrent_20_run2": concurrent_20_result_2,
            "correctness": correctness_ok
        }

if __name__ == "__main__":
    test = PerformanceTest()
    asyncio.run(test.run_all_tests())
