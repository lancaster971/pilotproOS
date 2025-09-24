#!/usr/bin/env python3
"""
Test script per Milhena CLI integration
"""

import sys
sys.path.append('.')

def test_milhena_import():
    """Test se Milhena si può importare correttamente nel CLI"""
    try:
        from agents.crews.milhena_crew_agents import MilhenaMultiAgentCrew, QuickMilhenaAgent
        from model_selector import ModelSelector

        print("✅ Import Milhena: SUCCESS")

        # Test inizializzazione
        model_selector = ModelSelector()
        milhena_crew = MilhenaMultiAgentCrew(model_selector)
        quick_milhena = QuickMilhenaAgent(model_selector)

        print("✅ Inizializzazione agenti: SUCCESS")

        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False

def test_cli_menu_structure():
    """Test che il menu del CLI sia configurato correttamente"""
    try:
        from cli import AgentCLI

        cli = AgentCLI()

        # Verifica che la funzione milhena_assistant esista
        if hasattr(cli, 'milhena_assistant'):
            print("✅ Funzione milhena_assistant presente: SUCCESS")
        else:
            print("❌ Funzione milhena_assistant mancante")
            return False

        return True

    except Exception as e:
        print(f"❌ CLI Test Error: {e}")
        return False

def simulate_milhena_interaction():
    """Simula un'interazione con Milhena"""
    try:
        from agents.crews.milhena_crew_agents import QuickMilhenaAgent
        from model_selector import ModelSelector

        print("🧪 Test simulazione Quick Milhena...")

        quick_milhena = QuickMilhenaAgent(ModelSelector())
        result = quick_milhena.quick_answer("Quante esecuzioni oggi?")

        if result.get("success"):
            print(f"✅ Quick Milhena Response: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Quick Milhena Failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Simulation Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING MILHENA CLI INTEGRATION\n")

    tests = [
        ("Import Test", test_milhena_import),
        ("CLI Menu Structure", test_cli_menu_structure),
        ("Milhena Simulation", simulate_milhena_interaction)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"🔧 Running {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print(f"{'✅' if success else '❌'} {test_name}: {'PASS' if success else 'FAIL'}\n")

    # Summary
    passed = sum(1 for _, success in results if success)
    total = len(results)

    print("="*50)
    print(f"📊 SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Milhena CLI integration is ready!")
        print("\n🚀 Per testare manualmente:")
        print("   python3 cli.py")
        print("   Scegli opzione 4: Milhena Assistant")
    else:
        print("⚠️  Some tests failed. Check the output above.")

    print("="*50)