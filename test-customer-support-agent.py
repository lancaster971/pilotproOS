#!/usr/bin/env python3
"""
🎧 TEST CUSTOMER SUPPORT AGENT
Test diretto dell'agent customer support senza container
"""

import asyncio
import json
import requests
import time

async def test_customer_support_endpoint():
    """Test dell'endpoint customer support per n8n"""

    print("🎧 TESTING CUSTOMER SUPPORT AGENT")
    print("="*50)

    # Test scenarios che n8n potrebbe inviare
    test_scenarios = [
        {
            "name": "User Lookup by Email",
            "message": "Trova informazioni per l'utente tiziano@gmail.com",
            "customer_id": None
        },
        {
            "name": "Recent Users List",
            "message": "Chi sono gli ultimi utenti registrati?",
            "customer_id": None
        },
        {
            "name": "System Status Check",
            "message": "Come sta andando il sistema oggi?",
            "customer_id": None
        },
        {
            "name": "User by ID",
            "message": "Dimmi tutto sull'utente ID 1",
            "customer_id": "1"
        },
        {
            "name": "General Support",
            "message": "Ho problemi di login, puoi aiutarmi?",
            "customer_id": None
        }
    ]

    results = []

    for i, scenario in enumerate(test_scenarios):
        print(f"\n🧪 TEST {i+1}: {scenario['name']}")
        print(f"   Message: {scenario['message']}")

        try:
            # Test con GET (più facile per n8n)
            params = {
                "message": scenario["message"]
            }
            if scenario["customer_id"]:
                params["customer_id"] = scenario["customer_id"]

            start_time = time.time()
            response = requests.get(
                "http://localhost:8000/api/n8n/agent/customer-support",
                params=params,
                timeout=30
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                results.append({
                    "scenario": scenario["name"],
                    "success": data.get("success", False),
                    "response_time": duration,
                    "response": data.get("agent_response", "")[:100] + "...",
                    "database_used": data.get("database_used", False)
                })

                success_icon = "✅" if data.get("success") else "❌"
                db_icon = "🗄️" if data.get("database_used") else "💬"

                print(f"   {success_icon} Status: {data.get('success')}")
                print(f"   ⏱️ Time: {duration:.1f}s")
                print(f"   {db_icon} Database used: {data.get('database_used')}")
                print(f"   💬 Response: {data.get('agent_response', '')[:150]}...")

            else:
                results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time": duration
                })

                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:100]}")

        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout (>30s)")
            results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": "Timeout"
            })

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
            results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": str(e)
            })

        time.sleep(2)  # Pausa tra test

    # Summary
    print("\n" + "="*60)
    print("📊 CUSTOMER SUPPORT AGENT - TEST SUMMARY")
    print("="*60)

    successful = [r for r in results if r.get('success')]
    total_tests = len(results)

    print(f"\n🎯 RESULTS: {len(successful)}/{total_tests} tests passed")

    for result in results:
        icon = "✅" if result.get('success') else "❌"
        time_info = f" ({result.get('response_time', 0):.1f}s)" if 'response_time' in result else ""
        print(f"   {icon} {result['scenario']}{time_info}")

    if successful:
        avg_time = sum(r.get('response_time', 0) for r in successful) / len(successful)
        print(f"\n⚡ Average response time: {avg_time:.1f}s")

        # Show database usage
        db_usage = [r for r in successful if r.get('database_used')]
        print(f"🗄️ Database queries: {len(db_usage)}/{len(successful)} responses")

    print(f"\n🔗 n8n HTTP Request Node Configuration:")
    print(f"   Method: GET")
    print(f"   URL: http://pilotpros-intelligence-engine:8000/api/n8n/agent/customer-support")
    print(f"   Query Params: message={{{{$json.message}}}}&customer_id={{{{$json.customer_id}}}}")

    return results

if __name__ == "__main__":
    asyncio.run(test_customer_support_endpoint())