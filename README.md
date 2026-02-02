# 🤖 MuBot — My Personal Job Search Assistant

> An AI-powered Gmail agent that helps me craft personalized cold emails, track applications, and manage follow-ups — all through natural conversation.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What is MuBot?

**MuBot is my personal AI assistant for job hunting.** Instead of manually writing cold emails and tracking spreadsheets, I just chat with MuBot:

```
Me: "Draft an email for the Data Scientist role at Netflix"
MuBot: "Please paste the job description..."

[I paste the full JD]

MuBot: "✉️ Done! Here's your tailored email matching your Python/ML 
        experience to their requirements..."
```

### Current Features (Mini Version)

| Feature | What It Does |
|---------|--------------|
| 💬 **Chat Interface** | Talk naturally — no code needed |
| 📄 **JD Support** | Paste full job descriptions for tailored emails |
| 📅 **Auto Follow-ups** | Schedules follow-ups automatically after sending |
| 📊 **Pipeline Tracking** | Track applications from first contact to offer |
| 🛡️ **Safety First** | Explicit approval required for every send |
| 🧠 **Memory** | Remembers my profile and past outreach |

### Coming Soon

- [ ] LinkedIn integration for company research
- [ ] Web UI for easier job tracking
- [ ] Resume tailoring based on JD
- [ ] Interview scheduler
- [ ] A/B testing for email templates
- [ ] Notion database sync

---

## 🏗️ How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Me Chat   │────▶│  MuBot AI   │────▶│   Gmail     │
│  (Natural   │     │  (Understand│     │  (Sends     │
│   Language) │     │   + Draft)  │     │   Emails)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  USER.md   │  │  MEMORY    │  │  Pipeline  │
    │  (Profile) │  │  (History) │  │  (Tracker) │
    └────────────┘  └────────────┘  └────────────┘
```

**The Flow:**
1. **I chat** with MuBot in plain English
2. **MuBot reads** my profile (USER.md) and past outreach
3. **MuBot drafts** personalized emails using job descriptions
4. **I approve** before sending (safety first!)
5. **MuBot tracks** everything in my pipeline
6. **MuBot reminds** me to follow up

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/MuskanKhandelwal/MuBot.git
cd MuBot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e "."
```

### 2. Set Up

```bash
# Initialize MuBot
python -m mubot.scripts.init_project

# Edit environment variables
nano .env  # Add your OPENAI_API_KEY
```

### 3. Personalize

Edit `data/USER.md` with your details:
```markdown
## Identity
- **Name**: Your Name
- **Email**: your.email@gmail.com
- **Current Title**: Data Scientist

## Background
- **Summary**: I have 3 years of experience in...
- **Key Skills**: Python, SQL, ML, GenAI
```

### 4. Chat with MuBot

```bash
python mubot_chat_enhanced.py
```

**Example conversation:**
```
🤖 MuBot: Hi! How can I help with your job search?

You: Draft an email for Data Scientist at Stripe

🤖 MuBot: Please paste the job description...

You: [paste JD]
You: DONE

🤖 MuBot: ✉️ Draft ready! 
      Subject: Excited to Contribute to Stripe's Data Team
      
      [Email body with JD keywords matched to your profile]
      
      Type 'send' to send, or 'redraft' to try again.

You: send
🤖 MuBot: 🚀 Ready to send! Type 'yes' to confirm.

You: yes
🤖 MuBot: ✅ Sent! 📅 Follow-up scheduled in 5 days.
```

---

## 📁 Project Structure

```
MuBot/
├── mubot_chat_enhanced.py      # 💬 Main chat interface (use this!)
├── interactive_bot.py          # 🗣️ Simple chat bot
├── schedule_followup.py        # 📅 Manual follow-up scheduler
│
├── src/mubot/                  # 🤖 Core code
│   ├── agent/                  #    AI agent & reasoning
│   ├── memory/                 #    File-based memory system
│   ├── tools/                  #    Gmail, RAG, Scheduler
│   └── config/                 #    Prompts & settings
│
├── guides/                     # 📚 Documentation
│   ├── CUSTOMIZATION_GUIDE.md  #    Customize templates
│   └── FOLLOWUP_GUIDE.md       #    Manage follow-ups
│
├── data/                       # 💾 Your data (ignored by git)
│   ├── USER.md                 #    Your profile
│   ├── MEMORY.md               #    Learnings & rules
│   └── heartbeat-state.json    #    Scheduled tasks
│
└── examples/                   # 📖 Example scripts
```

---

## 🎯 Commands

### Email Management
| Command | Description |
|---------|-------------|
| `Draft an email for [role] at [company]` | Creates JD-optimized draft |
| `send` | Sends the last draft (asks confirmation) |
| `Check follow-ups` | Shows pending follow-ups |

### Pipeline Management
| Command | Description |
|---------|-------------|
| `Add [company] to my pipeline` | Track a new opportunity |
| `What's in my pipeline?` | View all opportunities |
| `Move [company] to [stage]` | Update pipeline stage |

### Info
| Command | Description |
|---------|-------------|
| `Show my daily summary` | Emails sent, replies, etc. |
| `Help` | Show all commands |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | OpenAI GPT-4 |
| **Memory** | File-based (Markdown + JSON) |
| **Vector Search** | ChromaDB + Sentence Transformers |
| **Email** | Gmail API (OAuth) |
| **Scheduling** | APScheduler |
| **Language** | Python 3.11+ |

---

## 📝 Why I Built This

Job searching is tedious. I was:
- ❌ Copy-pasting the same email template
- ❌ Forgetting to follow up
- ❌ Losing track of where I applied
- ❌ Not tailoring emails to job descriptions

**MuBot fixes this.** Now I just chat, review, and approve. The AI handles personalization, scheduling, and tracking.

---

## 🚧 Roadmap

### v0.1 (Current) ✅
- Basic chat interface
- JD-enhanced email drafting
- Automatic follow-ups
- Pipeline tracking

### v0.2 (Coming Soon)
- [ ] LinkedIn integration
- [ ] Web UI dashboard
- [ ] Interview scheduling

### v0.3 (Future)
- [ ] Resume tailoring
- [ ] A/B testing templates
- [ ] Multi-provider LLM support

---

## 🤝 Contributing

This is my personal project, but feel free to fork and customize! Open an issue if you find bugs.

---

## 📄 License

MIT License — use it, modify it, make it yours!

---

<p align="center">
  <b>Built with ❤️ for my job search</b><br>
  <i>More features coming soon...</i>
</p>
