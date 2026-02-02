# 🤖 MuBot — Job Search Cold Emailing Agent

> An AI-powered Gmail agent that helps you find job opportunities, craft personalized cold emails, send them safely, track outcomes, and follow up intelligently.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is MuBot?

MuBot is an **agent-based AI system** designed specifically for **job search cold emailing**. Unlike generic email tools, MuBot:

- 🧠 **Understands your job search goals** from `USER.md` and `MEMORY.md`
- ✍️ **Drafts personalized cold emails** using company research and your background
- 🛡️ **Enforces safety guardrails** — no emails sent without your explicit approval
- 📊 **Tracks your pipeline** from first contact to offer
- 🔄 **Manages follow-ups** automatically based on response patterns
- 📈 **Learns from outcomes** to improve future outreach

### Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Safety First** | Explicit approval required for every send, rate limiting, unsubscribe support |
| **Memory-Driven** | File-based memory system (`USER.md`, `MEMORY.md`, `TOOLS.md`) |
| **Context-Aware** | RAG (Retrieval-Augmented Generation) for learning from past emails |
| **Transparent** | All decisions logged, drafts shown before sending |
| **Extensible** | MCP-compatible tool interface, optional Notion integration |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                │
│                    (CLI, Web UI, or IDE Integration)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    JOB SEARCH AGENT (src/mubot/agent/core.py)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   Receive    │→│    Recall    │→│    Reason    │→│    Check    │ │
│  │  User Input  │  │    Memory    │  │     LLM      │  │   Safety    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                              │          │
│         ┌────────────────────────────────────────────────────┘          │
│         ▼                                                               │
│  ┌──────────────┐  ┌──────────────┐                                    │
│  │     Act      │→│    Learn     │                                    │
│  │  (Execute)   │  │   (Update)   │                                    │
│  └──────────────┘  └──────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐        ┌─────────────────┐        ┌──────────────────┐
│    MEMORY     │        │  REASONING      │        │     TOOLS        │
│  (mubot/memory/)│       │ (mubot/agent/)  │        │  (mubot/tools/)  │
│               │        │                 │        │                  │
│ • USER.md     │        │ • LLM client    │        │ • GmailClient    │
│ • MEMORY.md   │        │ • Prompts       │        │ • RAGEngine      │
│ • TOOLS.md    │        │ • Streaming     │        │ • Scheduler      │
│ • Daily logs  │        │                 │        │                  │
│ • heartbeat   │        │                 │        │                  │
└───────────────┘        └─────────────────┘        └──────────────────┘
        │                                                    │
        ▼                                                    ▼
┌──────────────────────────────────┐          ┌──────────────────────────┐
│  RAG Vector Store (ChromaDB)     │          │   Gmail API (OAuth)      │
│                                  │          │                          │
│ • Past email embeddings          │          │ • Send/receive emails    │
│ • Semantic search                │          │ • Apply labels           │
│ • Similarity matching            │          │ • Thread management      │
└──────────────────────────────────┘          └──────────────────────────┘
```

---

## 📁 Project Structure

```
MuBot/
├── README.md                    # This file
├── AGENTS.md                    # Agent behavior documentation
├── pyproject.toml               # Python dependencies and config
├── .env.example                 # Environment variables template
│
├── src/
│   └── mubot/                   # Main Python package
│       ├── __init__.py          # Package exports
│       ├── cli.py               # Interactive chat interface
│       ├── test_runner.py       # Test suite runner
│       │
│       ├── agent/               # Core agent intelligence
│       │   ├── __init__.py
│       │   ├── core.py          # JobSearchAgent main orchestrator
│       │   ├── nlp_interface.py # Natural language interface
│       │   ├── reasoning.py     # LLM interaction engine
│       │   └── safety.py        # Safety guardrails
│       │
│       ├── config/              # Configuration management
│       │   ├── __init__.py
│       │   ├── settings.py      # Pydantic settings (env vars)
│       │   └── prompts.py       # LLM prompt templates
│       │
│       ├── memory/              # Persistence layer
│       │   ├── __init__.py
│       │   ├── manager.py       # MemoryManager (central interface)
│       │   ├── models.py        # Pydantic data models
│       │   └── persistence.py   # File storage (Markdown + JSON)
│       │
│       ├── tools/               # External tool integrations
│       │   ├── __init__.py
│       │   ├── gmail_client.py  # Gmail API client
│       │   ├── rag_engine.py    # ChromaDB vector search
│       │   └── scheduler.py     # APScheduler wrapper
│       │
│       ├── pipelines/           # Job search pipeline tracking
│       │   ├── __init__.py
│       │   └── job_pipeline.py  # PipelineStage, JobPipeline
│       │
│       ├── utils/               # Helper utilities
│       │   ├── __init__.py
│       │   ├── validators.py    # Input validation
│       │   └── helpers.py       # Text processing, IDs, etc.
│       │
│       ├── templates/           # Email templates
│       │   ├── __init__.py
│       │   └── email_templates.py
│       │
│       ├── scripts/             # CLI scripts
│       │   ├── __init__.py
│       │   ├── init_project.py  # mubot-init command
│       │   └── run_heartbeat.py # mubot-heartbeat command
│       │
│       └── tests/               # Test suite
│           ├── __init__.py
│           └── test_memory.py   # Memory system tests
│
├── examples/                    # Usage examples
│   ├── basic_usage.py
│   ├── meta_job_campaign.py
│   ├── meta_quick_start.py
│   └── natural_language_demo.py
│
├── data/                        # Runtime data (created on init)
│   ├── USER.md                  # Your profile & preferences
│   ├── MEMORY.md                # Job search context & learnings
│   ├── TOOLS.md                 # Resources & configurations
│   ├── heartbeat-state.json     # Scheduled tasks state
│   ├── memory/                  # Daily activity logs
│   ├── vector_store/            # ChromaDB files
│   └── pipelines/               # Job opportunities
│
├── guides/                      # 📚 Documentation
│   ├── CUSTOMIZATION_GUIDE.md   # How to customize templates
│   └── FOLLOWUP_GUIDE.md        # Follow-up management
│
└── [other files...]
    ├── USER.md                  # Your profile & preferences
    ├── MEMORY.md                # Job search context & learnings
    ├── TOOLS.md                 # Resources & configurations
    ├── heartbeat-state.json     # Scheduled tasks state
    ├── memory/                  # Daily activity logs
    │   └── YYYY-MM-DD.md
    ├── vector_store/            # ChromaDB files
    └── pipelines/               # Job opportunities
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mubot.git
cd mubot

# Create virtual environment (recommended)
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Install dependencies (requires Python 3.11+)
pip install -e ".[dev]"
```

### 2. Initialize Project

```bash
# Set up directory structure and memory files
mubot-init
```

This creates:
- `data/USER.md` — Your profile and preferences
- `data/MEMORY.md` — Job search goals and learnings
- `data/TOOLS.md` — Resources and configurations
- `.env` — Environment variables (from template)

### 3. Configure Environment

Edit `.env` with your credentials:

```bash
# LLM Provider
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4-turbo-preview

# Gmail API
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
SENDER_EMAIL=your.email@gmail.com

# Your settings
MAX_DAILY_EMAILS=20
REQUIRE_SEND_APPROVAL=true
```

### 4. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Gmail API**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download and save as `./credentials/gmail_credentials.json`

### 5. Personalize Your Profile

Edit `data/USER.md`:

```markdown
# User Profile

## Identity
- **Name**: Jane Smith
- **Email**: jane.smith@email.com
- **Timezone**: America/New_York

## Professional Background
- **Current Title**: Senior Software Engineer
- **Summary**: Full-stack developer with 8 years experience in fintech
- **Key Skills**: Python, React, AWS, System Design

## Preferences
- **Email Tone**: friendly
- **Daily Email Limit**: 15
```

### 6. Run MuBot (Natural Language Chat)

**New: Just talk to MuBot!** No need to write Python code.

```bash
# Start the enhanced interactive chat (recommended)
python mubot_chat_enhanced.py

# Or use the built-in command
mubot-chat
```

**✨ Enhanced Chat Features:**
- Multi-turn JD collection — paste full job descriptions
- JD-optimized email drafting
- Automatic follow-up scheduling
- Better conversation flow

### 7. Additional Scripts

```bash
# Quick email with JD support
python email_with_jd.py

# Schedule follow-ups manually
python schedule_followup.py

# Run tests
mubot-test

# Daily heartbeat (check replies, send follow-ups)
mubot-heartbeat
```

**Example conversation:**

```
🤖 MuBot: Welcome! How can I help with your job search today?

You: Add Meta to my pipeline
🤖 MuBot: ✅ Added Meta - Software Engineer to your pipeline!
       ID: abc-123
       Stage: identified

You: Draft a cold email for the infrastructure role at Meta
🤖 MuBot: ✉️ Drafted email for Meta!
       
       Subject: Interest in Infrastructure Role
       
       [Email body shown here]
       
       💡 To send: Type 'send the email' after reviewing

You: Send the email
🤖 MuBot: 🚀 Ready to send to Meta!
       
       Subject: Interest in Infrastructure Role
       To: hiring@meta.com
       
       Type 'yes' to confirm sending, or 'edit' to modify.

You: yes
🤖 MuBot: ✅ Email sent to Meta!

You: What's in my pipeline?
🤖 MuBot: 📊 Pipeline Summary
       [Shows all opportunities and stages]
```

**Available commands:**
- `Draft a cold email for [role] at [company]` — Now with **JD support**! Paste the full job description for optimized emails
- `Add [company] to my pipeline`
- `Move [company] to [stage]`
- `Check if anyone replied`
- `Show my daily summary`
- `What's in my pipeline?`
- `Check follow-ups` — See pending follow-up emails
- `Help`

### 🎯 Enhanced Features

#### Job Description (JD) Support
When drafting emails, MuBot now accepts full job descriptions and creates tailored emails:

```
You: Draft an email for the Data Scientist role at Netflix
🤖 Bot: Please paste the job description...

You: [Paste full JD with requirements]
You: DONE

🤖 Bot: ✉️ JD-Enhanced Draft Created!
      
      Subject: Interest in Personalization Team - Data Science Role
      
      [Email body with JD keywords matched to your profile]
```

**Benefits:**
- Matches your skills to JD requirements
- Mentions specific technologies from JD
- Shows why you're a good fit
- No generic "I'm interested" emails

#### Automatic Follow-Ups
MuBot schedules follow-ups automatically:

```
You: Send the email
🤖 Bot: ✅ Email sent!
      📅 Follow-up scheduled for 5 days later

You: Check follow-ups
🤖 Bot: 📅 3 pending follow-ups:
      • Netflix - Due tomorrow
      • Google - Due in 3 days
      • Meta - Due next week
```

**Features:**
- Auto-schedules after each send
- 3 follow-ups max (gentle, value-add, final)
- Auto-cancels if recipient replies
- Sends via heartbeat or manual trigger

---

### Alternative: Python API

For advanced use cases, use MuBot programmatically:

```python
import asyncio
from mubot import JobSearchAgent

async def main():
    agent = JobSearchAgent()
    await agent.initialize()
    
    draft, warnings = await agent.draft_email(
        company_name="Stripe",
        role_title="Staff Engineer",
    )
    
    print(f"Subject: {draft.subject}")
    print(f"\n{draft.body}")
    
    success, message = await agent.send_email(draft, approved=True)

asyncio.run(main())
```

---

## 🆕 What's New

### Latest Features (v0.1.0+)

| Feature | Description | Command/File |
|---------|-------------|--------------|
| **JD-Enhanced Emails** | Paste full job descriptions for tailored emails | `mubot_chat_enhanced.py` |
| **Multi-Turn Chat** | Interactive JD collection, recipient details | Enhanced NL executor |
| **Auto Follow-Ups** | Automatic scheduling after each send | Built-in |
| **Follow-Up Manager** | Check, send, cancel pending follow-ups | `Check follow-ups` |
| **Better Formatting** | Proper paragraph spacing in emails | All drafts |
| **Gmail Headers** | Improved email deliverability | `gmail_client.py` |
| **New Guides** | Documentation for customization | `guides/*.md` |

---

## 📖 Core Concepts

### The REACT Loop

MuBot follows a structured workflow for every request:

```
Receive → Recall → Reason → Check → Act → Learn
```

1. **Receive**: Accept user input (natural language)
2. **Recall**: Load relevant memory (USER.md, company history)
3. **Reason**: Plan approach using LLM
4. **Check**: Validate safety constraints
5. **Act**: Execute approved actions
6. **Learn**: Update memory with outcomes

### Memory System

MuBot uses a **file-backed memory system** that persists across sessions:

| File | Purpose | Updated By |
|------|---------|------------|
| `USER.md` | Your profile, preferences, goals | You + Agent |
| `MEMORY.md` | Learnings, what's working, rules | Agent |
| `TOOLS.md` | Labels, templates, resources | You + Agent |
| `memory/YYYY-MM-DD.md` | Daily activity logs | Agent |
| `heartbeat-state.json` | Scheduled tasks | Scheduler |

**Key Principle**: *The agent only remembers what's written to files.*

### Safety Guardrails

Every potentially impactful action goes through safety checks:

```python
# Before sending any email
safety_result = safety.can_send_email(
    recipient_email="hiring@company.com",
    company_name="Company",
    has_explicit_approval=user_approved,
)

if not safety_result.passed:
    # Action blocked
    print(f"Blocked: {safety_result.message}")
```

Checks include:
- ✅ Explicit user approval required
- ✅ Daily email limits enforced
- ✅ Rate limiting between sends
- ✅ Duplicate outreach detection
- ✅ Follow-up limits (max 3)
- ✅ Unsubscribe language required

### RAG (Retrieval-Augmented Generation)

MuBot uses semantic search to find similar past emails:

```python
# Find successful templates for similar roles
results = await rag.search_similar(
    query="Senior Engineer at fintech startup",
    filter_criteria={"response_category": "positive"},
    n_results=5,
)

# Use these as inspiration for new drafts
```

This enables:
- Learning from successful outreach
- Avoiding repetitive messaging
- Context-aware personalization

---

## 🛠️ API Reference

### JobSearchAgent

The main interface for all operations.

```python
agent = JobSearchAgent(memory_path="./data")
await agent.initialize()

# Email operations
draft, warnings = await agent.draft_email(...)
success, message = await agent.send_email(draft, approved=True)
await agent.schedule_followup(entry, days_delay=5)

# Response handling
category, data = await agent.process_response(entry, response_body)

# Queries and summaries
summary = await agent.get_daily_summary()
context = agent.get_company_context("Company Name")

# Campaign management
agent.pause_campaign(reason="Traveling")
agent.resume_campaign()
```

### MemoryManager

Interface for persistent storage.

```python
memory = MemoryManager("./data")

# User profile
profile = memory.load_user_profile()

# Outreach tracking
memory.save_outreach_entry(entry)
history = memory.get_company_history("Company")
stats = memory.get_daily_stats()

# Heartbeat state
state = memory.load_heartbeat_state()
memory.save_heartbeat_state(state)
```

### GmailClient

Gmail API wrapper.

```python
gmail = GmailClient(settings)
await gmail.authenticate()

# Send email
message_id = await gmail.send_email(
    to="recipient@company.com",
    subject="Subject",
    body="<p>HTML body</p>",
    apply_label=True,
)

# Check for replies
replies = await gmail.check_for_replies(message_id, thread_id)

# Search
results = await gmail.search_messages(
    query="from:company.com subject:interview newer_than:7d"
)
```

### RAGEngine

Semantic search over past outreach.

```python
rag = RAGEngine(settings)
await rag.initialize()

# Index emails
await rag.index_outreach(entry)

# Search
results = await rag.search_similar(
    query="machine learning engineer",
    n_results=5,
)

# Get successful templates
templates = await rag.get_successful_templates(role_type="engineer")
```

### JobPipeline

Track opportunities through stages.

```python
pipeline = JobPipeline(memory_manager)

# Add opportunity
opp = pipeline.add_opportunity(
    company_name="Company",
    role_title="Engineer",
    job_url="https://...",
)

# Advance stage
pipeline.advance_stage(opp.id, PipelineStage.INTERVIEW)

# Get stats
stats = pipeline.get_funnel_stats()
print(pipeline.get_pipeline_summary())
```

---

## 🔄 Heartbeat & Scheduling

The heartbeat runs periodically to:
- Check for email replies
- Send pending follow-ups
- Generate daily summaries

### Run Manually

```bash
mubot-heartbeat
```

### Schedule with Cron

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/mubot && python -m scripts.run_heartbeat
```

### Programmatic Usage

```python
from mubot.tools import Scheduler

scheduler = Scheduler(settings, memory, agent)
await scheduler.start()

# Schedule daily heartbeat
scheduler.schedule_daily_heartbeat(hour=9, minute=0)

# Schedule email
scheduler.schedule_email(entry, send_at=datetime(2024, 1, 15, 9, 0))

# Get pending tasks
pending = scheduler.get_pending_tasks()
```

---

## 🧪 Testing

```bash
# Run quick test suite (recommended)
mubot-test

# Or run directly
python -m mubot.test_runner

# Run all tests with pytest
pytest src/mubot/tests/

# Run with coverage
pytest --cov=src/mubot --cov-report=html
```

---

## 📚 Educational Resources

This codebase demonstrates several software engineering concepts:

### Architecture Patterns
- **Agent-Based Architecture**: REACT loop for decision making
- **Repository Pattern**: MemoryManager abstracts storage
- **Factory Pattern**: Template generation with context

### AI/ML Engineering
- **Prompt Engineering**: Structured prompts with context
- **RAG**: Vector search for context retrieval
- **Safety Guardrails**: Multi-layered validation

### Python Best Practices
- **Type Hints**: Full type annotations
- **Pydantic**: Data validation and serialization
- **Async/Await**: Non-blocking I/O
- **Dependency Injection**: Settings and clients injected

---

## 📝 Quick Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| `mubot` | Show usage info |
| `mubot-init` | Initialize project (creates data files) |
| `mubot-chat` | Start interactive chat mode |
| `mubot-heartbeat` | Run scheduled tasks |
| `mubot-test` | Run test suite |

### Python Imports

```python
# Main agent
from mubot import JobSearchAgent

# Submodules
from mubot.agent import JobSearchAgent
from mubot.pipelines import JobPipeline, PipelineStage
from mubot.memory import MemoryManager
from mubot.tools import GmailClient, RAGEngine, Scheduler
```

### Project Structure

| Path | Description |
|------|-------------|
| `src/mubot/` | Main Python package |
| `data/` | User data (created on init) |
| `examples/` | Usage examples |
| `tests/` | Test files |

---

## 🔒 Security & Privacy

- **API Keys**: Stored in `.env` (never commit)
- **Gmail OAuth**: User-controlled, revocable
- **Data Local**: All data stored locally in `./data/`
- **Approval Required**: No emails sent without explicit consent
- **Rate Limiting**: Prevents accidental spam

---

## 🗺️ Roadmap

- [ ] Web UI for non-technical users
- [ ] Notion database integration
- [ ] LinkedIn profile enrichment
- [ ] A/B testing framework
- [ ] Analytics dashboard
- [ ] Multi-language support
- [ ] Calendar integration for interview scheduling

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- Built with [OpenAI](https://openai.com/) GPT models
- Vector search powered by [ChromaDB](https://www.trychroma.com/)
- Embeddings from [Sentence Transformers](https://www.sbert.net/)
- Scheduling via [APScheduler](https://apscheduler.readthedocs.io/)

---

**Built with ❤️ for job seekers everywhere.**

*Remember: MuBot is a copilot, not an autopilot. Always review emails before sending.*
