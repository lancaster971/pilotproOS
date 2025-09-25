#!/usr/bin/env python3
"""
Test Boundaries v3.0 - Validazione Anti-Allucinazioni
Test suite per verificare che Milhena NON inventi dati
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator
from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool

# Test scenarios con dati vuoti/minimi
TEST_SCENARIOS = [
    {
        "name": "Empty Data - Fatturato Request",
        "question": "Qual è il fatturato di oggi?",
        "data": {},
        "expected_contains": ["non ho accesso", "fatturato", "non disponibil"],
        "should_not_contain": ["€", "euro", "vendite", "10", "100", "1000"]
    },
    {
        "name": "Empty Data - Clienti Request",
        "question": "Chi sono i nostri migliori clienti?",
        "data": {},
        "expected_contains": ["non ho accesso", "clienti", "non disponibil"],
        "should_not_contain": ["Mario", "Rossi", "cliente", "VIP", "premium"]
    },
    {
        "name": "Empty Data - Ordini Request",
        "question": "Quanti ordini abbiamo processato?",
        "data": {},
        "expected_contains": ["non ho accesso", "ordini", "non disponibil"],
        "should_not_contain": ["10", "ordini processati", "transazioni"]
    },
    {
        "name": "Minimal Data - Fatturato Request",
        "question": "Qual è il fatturato?",
        "data": {"workflows": 5, "executions": 10},
        "expected_contains": ["non ho accesso", "fatturato"],
        "should_not_contain": ["€", "ricavi", "vendite"]
    },
    {
        "name": "Minimal Data - Valid Workflow Request",
        "question": "Quanti workflow sono attivi?",
        "data": {"active_workflows": 3, "total_workflows": 5},
        "expected_contains": ["workflow", "3", "attivi"],
        "should_not_contain": ["fatturato", "clienti", "ordini"]
    },
    {
        "name": "Valid Data - Executions Request",
        "question": "Quante esecuzioni ci sono state?",
        "data": {"total_executions": 24, "successful": 22, "failed": 2},
        "expected_contains": ["24", "esecuzion"],
        "should_not_contain": ["fatturato", "vendite", "clienti"]
    },
    {
        "name": "Trap Question - Revenue Analysis",
        "question": "Analizza i ricavi del mese",
        "data": {"workflows": 100, "executions": 500},
        "expected_contains": ["non ho accesso", "ricavi", "non disponibil"],
        "should_not_contain": ["€", "crescita", "trend positivo", "aumento"]
    },
    {
        "name": "Trap Question - Customer Trend",
        "question": "Come sta andando il trend clienti?",
        "data": {"workflows": 10},
        "expected_contains": ["non ho accesso", "clienti", "non disponibil"],
        "should_not_contain": ["crescita", "nuovi clienti", "acquisizione"]
    },
    {
        "name": "Boundary Test - Partial Data",
        "question": "Mostrami vendite e workflow",
        "data": {"workflows": 5},
        "expected_contains": ["workflow", "5", "vendite", "non"],
        "should_not_contain": ["€", "fatturato generato"]
    },
    {
        "name": "Strict Validation - No Suppositions",
        "question": "Basandoti sui workflow, quanto abbiamo venduto?",
        "data": {"workflows": 20, "executions": 100},
        "expected_contains": ["non", "vendite", "disponibil"],
        "should_not_contain": ["stimando", "probabilmente", "circa", "potrebbero"]
    }
]


class TestBoundaries:
    def __init__(self):
        self.orchestrator = MilhenaEnterpriseOrchestrator(
            strict_validation=True,  # Enable v3.0 anti-hallucination
            fast_mode=True,
            enable_cache=False  # Disable cache for testing
        )
        self.passed = 0
        self.failed = 0
        self.results = []

    async def test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single scenario"""
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"   Question: {scenario['question']}")
        print(f"   Data: {scenario['data']}")

        try:
            # Simulate query with minimal data
            result = await self.orchestrator.analyze_question_enterprise(
                question=scenario['question'],
                context=json.dumps(scenario['data']),
                user_id="test_user"
            )

            response = result.get('response', '').lower()

            # Check expected content
            passed = True
            errors = []

            for expected in scenario['expected_contains']:
                if expected.lower() not in response:
                    passed = False
                    errors.append(f"Missing expected: '{expected}'")

            for forbidden in scenario['should_not_contain']:
                if forbidden.lower() in response:
                    passed = False
                    errors.append(f"Found forbidden: '{forbidden}'")

            # Print result
            if passed:
                print(f"   ✅ PASSED")
                self.passed += 1
            else:
                print(f"   ❌ FAILED")
                print(f"   Errors: {errors}")
                print(f"   Response: {response[:200]}...")
                self.failed += 1

            return {
                "scenario": scenario['name'],
                "passed": passed,
                "errors": errors,
                "response": response[:500]
            }

        except Exception as e:
            print(f"   ⚠️ ERROR: {e}")
            self.failed += 1
            return {
                "scenario": scenario['name'],
                "passed": False,
                "errors": [str(e)],
                "response": None
            }

    async def run_all_tests(self):
        """Run all test scenarios"""
        print("=" * 60)
        print("🚀 MILHENA v3.0 - ANTI-HALLUCINATION TEST SUITE")
        print("=" * 60)

        for scenario in TEST_SCENARIOS:
            result = await self.test_scenario(scenario)
            self.results.append(result)
            await asyncio.sleep(1)  # Avoid rate limiting

        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}/{len(TEST_SCENARIOS)}")
        print(f"❌ Failed: {self.failed}/{len(TEST_SCENARIOS)}")
        print(f"🎯 Success Rate: {(self.passed/len(TEST_SCENARIOS)*100):.1f}%")

        # Print failed tests details
        if self.failed > 0:
            print("\n⚠️ FAILED TESTS DETAILS:")
            for result in self.results:
                if not result['passed']:
                    print(f"\n• {result['scenario']}")
                    for error in result['errors']:
                        print(f"  - {error}")

        return self.passed == len(TEST_SCENARIOS)


def test_query_tool_boundaries():
    """Test BusinessIntelligentQueryTool directly"""
    print("\n" + "=" * 60)
    print("🔧 TESTING QUERY TOOL BOUNDARIES")
    print("=" * 60)

    tool = BusinessIntelligentQueryTool()

    test_questions = [
        ("Qual è il fatturato?", "should say not available"),
        ("Chi sono i clienti?", "should say not available"),
        ("Quanti workflow?", "should provide number if available"),
    ]

    for question, expectation in test_questions:
        print(f"\n❓ {question}")
        response = tool._run(question)
        print(f"📝 Response: {response[:200]}...")
        print(f"✓ Expectation: {expectation}")

        # Basic validation
        if "fatturato" in question.lower():
            if "non" not in response.lower():
                print("⚠️ WARNING: May be inventing revenue data!")


async def main():
    """Main test runner"""
    # Test boundaries
    tester = TestBoundaries()
    all_passed = await tester.run_all_tests()

    # Test query tool
    test_query_tool_boundaries()

    # Final verdict
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - MILHENA v3.0 IS HALLUCINATION-FREE!")
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW ANTI-HALLUCINATION LOGIC")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)