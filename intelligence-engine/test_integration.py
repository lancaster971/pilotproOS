#!/usr/bin/env python3
"""
Integration test for Router + Masking Engine
Tests the complete flow with real data
"""
import asyncio
from app.core.router import SmartLLMRouter, RouterConfig
from app.security import MultiLevelMaskingEngine, UserLevel, MaskingConfig

async def test_integration():
    """Test router + masking integration"""

    print("\n" + "="*80)
    print("INTEGRATION TEST: ROUTER + MASKING ENGINE")
    print("="*80)

    # Initialize components
    router = SmartLLMRouter(RouterConfig(
        groq_api_key="test",
        openai_api_key="test",
        google_api_key="test",
        audit_enabled=False
    ))

    masking_business = MultiLevelMaskingEngine(
        MaskingConfig(user_level=UserLevel.BUSINESS, strict_mode=False)
    )

    masking_admin = MultiLevelMaskingEngine(
        MaskingConfig(user_level=UserLevel.ADMIN, strict_mode=False)
    )

    # Test scenarios
    test_cases = [
        {
            "query": "Il workflow n8n ha generato un errore nel database PostgreSQL",
            "description": "Technical error message"
        },
        {
            "query": "Mostra l'ultimo messaggio ricevuto dal webhook",
            "description": "Message extraction request"
        },
        {
            "query": "SELECT * FROM execution_entity WHERE workflow_id = '123'",
            "description": "SQL query"
        },
        {
            "query": "Ciao Milhena, come va il sistema oggi?",
            "description": "Simple greeting"
        }
    ]

    for test in test_cases:
        print(f"\n📝 Test: {test['description']}")
        print(f"   Original: {test['query'][:60]}...")

        # Route the query
        decision = await router.route(test['query'])
        print(f"   → Routed to: {decision.model_tier.value} (confidence: {decision.confidence:.1%})")
        print(f"   → Est. cost: ${decision.estimated_cost:.6f}")

        # Apply masking for business user
        masked_business = masking_business.mask(test['query'])
        print(f"   → Business masking: {masked_business.masked[:60]}...")
        print(f"     Replacements: {masked_business.replacements_made}")

        # Apply masking for admin user
        masked_admin = masking_admin.mask(test['query'])
        print(f"   → Admin masking: {masked_admin.masked[:60]}...")
        print(f"     Replacements: {masked_admin.replacements_made}")

        # Validate no leaks for business
        is_clean, leaks = masking_business.validate_no_leaks(masked_business.masked)
        if is_clean:
            print(f"   ✅ Business output is clean")
        else:
            print(f"   ⚠️  Leaks detected in business output: {leaks}")

    # Show router statistics
    print("\n" + "="*80)
    print("ROUTER STATISTICS")
    print("="*80)

    stats = router.get_usage_stats()
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['total_cost']:.6f}")
    print(f"Savings: {stats['savings_percentage']:.1f}%")

    # Show masking statistics
    print("\n" + "="*80)
    print("MASKING STATISTICS")
    print("="*80)

    business_stats = masking_business.get_stats()
    print(f"Business level patterns: {business_stats['patterns_loaded']['business']}")

    admin_stats = masking_admin.get_stats()
    print(f"Admin level patterns: {admin_stats['patterns_loaded']['admin']}")

    print("\n✅ Integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_integration())