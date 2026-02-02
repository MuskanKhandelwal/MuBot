# 🧪 MuBot Testing Guide

Complete step-by-step guide to test MuBot before using it for real job searches.

---

## ✅ Pre-Flight Checklist

Before testing, ensure you have:
- [ ] Python 3.11+ installed
- [ ] OpenAI API key (or Anthropic/Kimi)
- [ ] GitHub account (for testing OAuth flow)

---

## 🚀 Phase 1: Installation & Setup (5 min)

### Step 1: Install Dependencies

```bash
cd /Users/muskankhandelwal/Documents/MuBot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install MuBot
pip install -e "."

# Verify installation
python -c "from agent import JobSearchAgent; print('✅ Installation OK')"
```

**Expected:** No errors, "✅ Installation OK" printed.

---

### Step 2: Initialize Project

```bash
# Run initialization
python -m scripts.init_project
```

**Verify these files were created:**
```bash
ls -la data/
# Should see: USER.md, MEMORY.md, TOOLS.md, heartbeat-state.json

ls -la credentials/
# Should see: empty directory (ready for gmail_credentials.json)
```

---

### Step 3: Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit with your API key
nano .env  # or code .env, vim .env
```

**Minimum required in `.env`:**
```bash
OPENAI_API_KEY=sk-your-actual-key-here
LLM_MODEL=gpt-4o-mini  # Cheaper for testing
SENDER_EMAIL=test@example.com  # Can be fake for testing
REQUIRE_SEND_APPROVAL=true  # IMPORTANT: Keep this true!
```

---

## 🧪 Phase 2: Unit Tests (2 min)

### Run Automated Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_memory.py -v
```

**Expected output:**
```
tests/test_memory.py::TestMemoryManager::test_initialization_creates_files PASSED
tests/test_memory.py::TestMemoryManager::test_save_and_retrieve_outreach PASSED
...
✅ 5 passed in 0.5s
```

---

## 🎮 Phase 3: Interactive Testing (10 min)

### Test 1: Natural Language Chat

```bash
# Start the chat interface
python cli.py
```

**Try these commands one by one:**

```
You: help
🤖 Should show: List of available commands

You: Add TestCorp to my pipeline
🤖 Should show: ✅ Added TestCorp - Software Engineer to your pipeline!

You: What's in my pipeline?
🤖 Should show: Pipeline summary with TestCorp

You: Draft a cold email for the engineer role at TestCorp
🤖 Should show: ✉️ Drafted email with subject and body

You: Show my daily summary
🤖 Should show: Today's stats (0 emails sent, etc.)
```

**Exit:** Type `exit` or `quit`

---

### Test 2: Python API (Programmatic)

Create `test_mubot.py`:

```python
import asyncio
from agent import JobSearchAgent
from pipelines import JobPipeline, PipelineStage

async def test_basic_flow():
    """Test basic MuBot functionality."""
    
    print("=" * 60)
    print("🧪 Testing MuBot Basic Flow")
    print("=" * 60)
    
    # 1. Initialize
    print("\n1️⃣ Initializing agent...")
    agent = JobSearchAgent()
    success = await agent.initialize()
    assert success, "❌ Failed to initialize"
    print("✅ Agent initialized")
    
    # 2. Check user profile loaded
    print("\n2️⃣ Checking user profile...")
    if agent.user_profile:
        print(f"✅ Profile loaded: {agent.user_profile.name}")
    else:
        print("⚠️ No profile found (expected for fresh install)")
    
    # 3. Draft an email (TEST MODE - no sending)
    print("\n3️⃣ Drafting test email...")
    draft, warnings = await agent.draft_email(
        company_name="TestCorp",
        role_title="Software Engineer",
        company_context="A test company for testing purposes",
        job_description="Looking for a software engineer to test our testing system",
        recipient_name="Test User",
        recipient_email="test@example.com",
    )
    
    assert draft.subject, "❌ No subject generated"
    assert draft.body, "❌ No body generated"
    print(f"✅ Draft created: {draft.subject[:50]}...")
    
    if warnings:
        print(f"⚠️ Warnings: {warnings}")
    
    # 4. Check safety (should NOT send without approval)
    print("\n4️⃣ Testing safety guardrails...")
    from agent.safety import SafetyGuardrails
    
    safety = SafetyGuardrails(agent.memory)
    check = safety.can_send_email(
        recipient_email="test@example.com",
        company_name="TestCorp",
        has_explicit_approval=False,  # Testing WITHOUT approval
    )
    
    assert not check.passed, "❌ Safety should block unapproved sends"
    print(f"✅ Safety correctly blocked: {check.message}")
    
    # 5. Test pipeline
    print("\n5️⃣ Testing pipeline...")
    pipeline = JobPipeline(agent.memory)
    
    opp = pipeline.add_opportunity(
        company_name="TestCorp",
        role_title="Software Engineer",
        notes="Test opportunity",
    )
    
    assert opp.id, "❌ Opportunity not created"
    print(f"✅ Opportunity added: {opp.id[:8]}...")
    
    # Advance stage
    updated = pipeline.advance_stage(opp.id, PipelineStage.CONTACTED)
    assert updated.stage == "contacted", "❌ Stage not updated"
    print(f"✅ Stage advanced to: {updated.stage}")
    
    # 6. Check memory persistence
    print("\n6️⃣ Testing memory persistence...")
    stats = agent.memory.get_daily_stats()
    print(f"✅ Daily stats retrieved: {stats.date}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_basic_flow())
```

Run it:
```bash
python test_mubot.py
```

**Expected:** All 6 tests pass with ✅

---

## 📧 Phase 4: Email Testing (SAFE - No Real Sending)

### Test Draft Generation Quality

```python
import asyncio
from agent import JobSearchAgent

async def test_email_quality():
    """Test that emails are well-formed and personalized."""
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    test_cases = [
        {
            "company": "Stripe",
            "role": "Senior Engineer",
            "context": "Payments infrastructure company",
        },
        {
            "company": "OpenAI",
            "role": "Research Engineer",
            "context": "AI research company",
        },
    ]
    
    for test in test_cases:
        print(f"\n📝 Testing: {test['company']} - {test['role']}")
        
        draft, warnings = await agent.draft_email(
            company_name=test["company"],
            role_title=test["role"],
            company_context=test["context"],
        )
        
        # Quality checks
        assert len(draft.subject) < 100, "Subject too long"
        assert len(draft.body) > 100, "Body too short"
        assert len(draft.body) < 2000, "Body too long"
        assert test["company"] in draft.body or test["role"] in draft.body, \
            "Not personalized to company/role"
        assert len(draft.personalization_elements) > 0, "No personalization"
        
        print(f"✅ Subject: {draft.subject}")
        print(f"✅ Body length: {len(draft.body)} chars")
        print(f"✅ Personalization: {len(draft.personalization_elements)} elements")

asyncio.run(test_email_quality())
```

---

### Test Safety Guardrails

```python
import asyncio
from agent import JobSearchAgent
from agent.safety import SafetyGuardrails, SafetyLevel

async def test_safety():
    """Test that safety guardrails work correctly."""
    
    agent = JobSearchAgent()
    await agent.initialize()
    
    safety = SafetyGuardrails(
        memory=agent.memory,
        max_daily_emails=3,  # Low limit for testing
        min_interval_seconds=60,
    )
    
    print("\n🛡️ Testing Safety Guardrails")
    print("=" * 60)
    
    # Test 1: No approval
    print("\n1️⃣ Testing: Send without approval")
    check = safety.can_send_email(
        recipient_email="test@example.com",
        company_name="TestCorp",
        has_explicit_approval=False,
    )
    assert not check.passed, "Should block without approval"
    assert check.level == SafetyLevel.BLOCKING
    print(f"✅ Correctly blocked: {check.message}")
    
    # Test 2: With approval
    print("\n2️⃣ Testing: Send with approval")
    check = safety.can_send_email(
        recipient_email="test@example.com",
        company_name="TestCorp",
        has_explicit_approval=True,
    )
    assert check.passed, "Should allow with approval"
    print(f"✅ Correctly allowed: {check.message}")
    
    # Test 3: Content check
    print("\n3️⃣ Testing: Email content validation")
    
    # Bad email (no unsubscribe)
    bad_check = safety.check_email_content(
        subject="Great opportunity!",
        body="Act now! Limited time! Buy now!",
    )
    assert not bad_check.passed, "Should flag spammy content"
    print(f"✅ Correctly flagged bad content: {bad_check.message}")
    
    # Good email
    good_check = safety.check_email_content(
        subject="Interest in engineering role",
        body="Hi, I'm interested in the role. If you'd prefer not to receive further messages, just reply with 'unsubscribe'.",
    )
    assert good_check.passed, "Should allow good content"
    print(f"✅ Correctly approved good content")
    
    print("\n" + "=" * 60)
    print("✅ All safety tests passed!")

asyncio.run(test_safety())
```

---

## 🔄 Phase 5: End-to-End Workflow Test

### Complete Job Search Simulation

```python
import asyncio
from datetime import datetime
from agent import JobSearchAgent
from pipelines import JobPipeline, PipelineStage

async def test_full_workflow():
    """
    Simulate a complete job search workflow:
    1. Add company to pipeline
    2. Draft email
    3. Save draft (don't send in test)
    4. Schedule follow-up
    5. Check pipeline status
    """
    
    print("=" * 60)
    print("🎬 Full Workflow Simulation")
    print("=" * 60)
    
    agent = JobSearchAgent()
    await agent.initialize()
    pipeline = JobPipeline(agent.memory)
    
    # Step 1: Add opportunity
    print("\n📌 Step 1: Add Meta to pipeline")
    meta = pipeline.add_opportunity(
        company_name="Meta",
        role_title="Software Engineer",
        job_url="https://metacareers.com/jobs/123",
        notes="Test opportunity - DO NOT SEND REAL EMAILS",
    )
    print(f"✅ Added: {meta.company_name} - {meta.role_title}")
    
    # Step 2: Draft email
    print("\n✉️ Step 2: Draft cold email")
    draft, warnings = await agent.draft_email(
        company_name="Meta",
        role_title="Software Engineer",
        company_context="Social media and metaverse company",
        recipient_name="Test Recruiter",
        recipient_email="TEST-ONLY@example.com",  # TEST EMAIL
    )
    print(f"✅ Drafted: {draft.subject}")
    print(f"   Body preview: {draft.body[:200]}...")
    
    # Step 3: Review (simulated)
    print("\n👀 Step 3: Review draft")
    print("   ⚠️  In real usage, YOU would review here!")
    print("   ⚠️  Check: Tone, accuracy, personalization")
    
    # Step 4: Link to pipeline (don't actually send)
    print("\n🔗 Step 4: Link to pipeline")
    pipeline.link_outreach(meta.id, draft)
    pipeline.advance_stage(meta.id, PipelineStage.CONTACTED)
    print(f"✅ Pipeline updated to: {PipelineStage.CONTACTED.value}")
    
    # Step 5: Schedule follow-up
    print("\n📅 Step 5: Schedule follow-up")
    draft.sent_at = datetime.utcnow()  # Pretend it was sent
    success, msg = await agent.schedule_followup(draft, days_delay=5)
    print(f"✅ {msg}")
    
    # Step 6: Check status
    print("\n📊 Step 6: Final status")
    print(pipeline.get_pipeline_summary())
    
    # Step 7: Verify daily stats
    stats = agent.memory.get_daily_stats()
    print(f"\n📈 Daily stats: {stats.emails_sent} emails, {stats.replies_received} replies")
    
    print("\n" + "=" * 60)
    print("✅ Workflow simulation complete!")
    print("=" * 60)
    print("""
📝 Summary:
• Company added to pipeline
• Email drafted (NOT sent - test mode)
• Pipeline stage updated
• Follow-up scheduled
• Stats tracked

In production:
• Review email carefully
• Use approved=True to actually send
• Run heartbeat daily to check replies
""")

asyncio.run(test_full_workflow())
```

Save as `test_workflow.py` and run:
```bash
python test_workflow.py
```

---

## 🐛 Phase 6: Troubleshooting Common Issues

### Issue 1: "No module named 'frontmatter'"

```bash
pip install python-frontmatter
```

### Issue 2: "No USER.md found"

```bash
# Run initialization
python -m scripts.init_project
```

### Issue 3: "OpenAI API error"

```bash
# Check your .env file
cat .env | grep OPENAI

# Should show: OPENAI_API_KEY=sk-...
# If not set, edit: nano .env
```

### Issue 4: Tests fail with "AssertionError"

Check which test failed:
```python
# Add detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## ✅ Final Verification Checklist

Before using MuBot for real:

- [ ] **Installation**: `pip install -e .` works without errors
- [ ] **Initialization**: `python -m scripts.init_project` creates all files
- [ ] **Unit tests**: `pytest tests/` passes all tests
- [ ] **Chat interface**: `python cli.py` starts and responds to "help"
- [ ] **Email drafting**: Can draft emails without errors
- [ ] **Safety blocks**: Unapproved sends are blocked
- [ ] **Pipeline works**: Can add and update opportunities
- [ ] **Memory persists**: Data saves to files in `data/`
- [ ] **No real emails sent**: All tests use fake/test emails only

---

## 🚀 Ready for Production?

Once all tests pass:

1. **Set real credentials** in `.env`
2. **Customize `data/USER.md`** with your real profile
3. **Review `data/MEMORY.md`** goals
4. **Start with ONE test email** to yourself
5. **Review carefully** before approving send
6. **Gradually scale up**

---

**Questions?** Check the main README.md or run:
```bash
python -m agent.core  # Shows usage info
```
