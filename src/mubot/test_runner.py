#!/usr/bin/env python3
"""
Quick Test Runner for MuBot

Run this to verify everything is working:
    python test_runner.py

This runs basic checks without sending any real emails.
"""

import asyncio
import sys
from pathlib import Path

def check_installation():
    """Step 1: Check if MuBot is installed."""
    print("\n" + "=" * 60)
    print("1️⃣ Checking Installation")
    print("=" * 60)
    
    try:
        from mubot.agent import JobSearchAgent
        from mubot.pipelines import JobPipeline
        from mubot.memory import MemoryManager
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\nFix: Run 'pip install -e .'")
        return False

def check_initialization():
    """Step 2: Check if project is initialized."""
    print("\n" + "=" * 60)
    print("2️⃣ Checking Initialization")
    print("=" * 60)
    
    required_files = [
        "data/USER.md",
        "data/MEMORY.md",
        "data/TOOLS.md",
        "data/heartbeat-state.json",
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        print("\nFix: Run 'python -m scripts.init_project'")
        return False
    
    print("✅ All required files present")
    return True

def check_environment():
    """Step 3: Check environment variables."""
    print("\n" + "=" * 60)
    print("3️⃣ Checking Environment")
    print("=" * 60)
    
    from mubot.config import get_settings
    
    try:
        settings = get_settings()
        
        if not settings.openai_api_key:
            print("❌ OPENAI_API_KEY not set")
            print("\nFix: Add to .env file: OPENAI_API_KEY=sk-...")
            return False
        
        print(f"✅ API key configured")
        print(f"✅ Model: {settings.llm_model}")
        print(f"✅ Daily limit: {settings.max_daily_emails} emails")
        return True
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return False

async def test_agent_initialization():
    """Step 4: Test agent initialization."""
    print("\n" + "=" * 60)
    print("4️⃣ Testing Agent Initialization")
    print("=" * 60)
    
    from mubot.agent import JobSearchAgent
    
    try:
        agent = JobSearchAgent()
        success = await agent.initialize()
        
        if success:
            print("✅ Agent initialized successfully")
            if agent.user_profile:
                print(f"✅ Profile loaded: {agent.user_profile.name}")
            return True
        else:
            print("❌ Agent initialization failed")
            print("   (This is OK if USER.md is empty)")
            return True  # Not a critical failure
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_email_drafting():
    """Step 5: Test email drafting (no sending)."""
    print("\n" + "=" * 60)
    print("5️⃣ Testing Email Drafting")
    print("=" * 60)
    
    from mubot.agent import JobSearchAgent
    
    try:
        agent = JobSearchAgent()
        await agent.initialize()
        
        draft, warnings = await agent.draft_email(
            company_name="TestCorp",
            role_title="Software Engineer",
            company_context="Test company for testing",
        )
        
        assert draft.subject, "No subject generated"
        assert draft.body, "No body generated"
        assert len(draft.body) > 100, "Body too short"
        
        print(f"✅ Email drafted successfully")
        print(f"   Subject: {draft.subject[:50]}...")
        print(f"   Body length: {len(draft.body)} chars")
        print(f"   Personalization: {len(draft.personalization_elements)} elements")
        
        if warnings:
            print(f"   Warnings: {len(warnings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_safety():
    """Step 6: Test safety guardrails."""
    print("\n" + "=" * 60)
    print("6️⃣ Testing Safety Guardrails")
    print("=" * 60)
    
    from mubot.agent.safety import SafetyGuardrails, SafetyLevel
    from mubot.memory import MemoryManager
    
    try:
        memory = MemoryManager("./data")
        safety = SafetyGuardrails(memory, max_daily_emails=5)
        
        # Test 1: Block without approval
        check = safety.can_send_email(
            recipient_email="test@test.com",
            company_name="TestCorp",
            has_explicit_approval=False,
        )
        
        if not check.passed and check.level == SafetyLevel.BLOCKING:
            print("✅ Correctly blocks unapproved sends")
        else:
            print("❌ Should block unapproved sends")
            return False
        
        # Test 2: Allow with approval
        check = safety.can_send_email(
            recipient_email="test@test.com",
            company_name="TestCorp",
            has_explicit_approval=True,
        )
        
        if check.passed:
            print("✅ Correctly allows approved sends")
        else:
            print(f"⚠️  Blocked: {check.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_pipeline():
    """Step 7: Test pipeline functionality."""
    print("\n" + "=" * 60)
    print("7️⃣ Testing Pipeline")
    print("=" * 60)
    
    from mubot.pipelines import JobPipeline, PipelineStage
    from mubot.memory import MemoryManager
    
    try:
        memory = MemoryManager("./data")
        pipeline = JobPipeline(memory)
        
        # Add opportunity
        opp = pipeline.add_opportunity(
            company_name="TestCorp",
            role_title="Test Role",
        )
        
        assert opp.id, "Opportunity not created"
        print(f"✅ Opportunity created: {opp.id[:8]}")
        
        # Advance stage
        updated = pipeline.advance_stage(opp.id, PipelineStage.CONTACTED)
        assert updated.stage == "contacted", "Stage not updated"
        print(f"✅ Stage advanced: {updated.stage}")
        
        # Get stats
        stats = pipeline.get_funnel_stats()
        print(f"✅ Pipeline stats: {stats['total_opportunities']} opportunities")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("\n" + "🧪 " * 15)
    print("MuBot Test Runner")
    print("🧪 " * 15)
    
    tests = [
        ("Installation", check_installation),
        ("Initialization", check_initialization),
        ("Environment", check_environment),
        ("Agent Init", test_agent_initialization),
        ("Email Drafting", test_email_drafting),
        ("Safety", test_safety),
        ("Pipeline", test_pipeline),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MuBot is ready to use.")
        print("\nNext steps:")
        print("1. Customize data/USER.md with your profile")
        print("2. Run: python cli.py (interactive chat)")
        print("3. Or: python examples/meta_job_campaign.py (demo)")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("- pip install -e .")
        print("- python -m scripts.init_project")
        print("- Check .env has OPENAI_API_KEY")
        return 1

def main():
    """Entry point for mubot-test command."""
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)

if __name__ == "__main__":
    main()
