# 🗣️ Natural Language Interface Guide

MuBot now supports **conversational interactions**! Just tell it what you want in plain English.

---

## 🚀 Quick Start

```bash
# 1. Initialize (if not done already)
mubot-init

# 2. Start chatting
mubot-chat
```

---

## 💬 Example Conversations

### Drafting and Sending Emails

```
You: Draft a cold email for the senior engineer role at Stripe

🤖 MuBot: ✉️  Drafted email for Stripe!

       Subject: Interest in Senior Engineer Role
       
       Hi there,
       
       I'm reaching out because I'm interested in the Senior Engineer 
       role at Stripe. With my background in payment systems and 
       distributed architecture, I believe I could contribute...
       
       Personalization:
         • Referenced company's payment infrastructure focus
         • Mentioned relevant 8 years experience
       
       💡 To send: Type 'send the email' after reviewing

You: Send the email

🤖 MuBot: 🚀 Ready to send to Stripe!
       
       Subject: Interest in Senior Engineer Role
       To: hiring@stripe.com
       
       Type 'yes' to confirm sending, or 'edit' to modify.

You: yes

🤖 MuBot: ✅ Email sent to Stripe!
```

### Managing Your Pipeline

```
You: Add Meta to my pipeline

🤖 MuBot: ✅ Added Meta - Software Engineer to your pipeline!
       ID: abc-123
       Stage: identified

You: Add Google - Staff Engineer with salary 200k-300k

🤖 MuBot: ✅ Added Google - Staff Engineer to your pipeline!
       ID: def-456
       Stage: identified

You: What's in my pipeline?

🤖 MuBot: 📊 Job Pipeline Summary
       ============================================================
       
       Total Opportunities: 2
       Active: 2 | Closed: 0
       
       Stage Breakdown:
         identified: 2
         contacted: 0
         replied: 0
         interview: 0
         offer: 0
       
       Active Opportunities:
         • Meta - Software Engineer (identified)
         • Google - Staff Engineer (identified)

You: Move Meta to contacted stage

🤖 MuBot: ✅ Updated Meta to contacted stage!
```

### Checking Status

```
You: Show my daily summary

🤖 MuBot: 📊 Today's Summary

       • Emails sent: 3/20
       • Replies received: 1
       • Positive: 1
       • Daily limit: ✅ OK

You: Check if anyone replied

🤖 MuBot: 📬 Reply Check

       Today's activity:
       • Emails sent: 3
       • Replies received: 1
       • Positive responses: 1

You: What do I know about Stripe?

🤖 MuBot: 🏢 Stripe - Outreach History

       • Total outreach: 2
       • Responses received: 1
       • Last contact: 2024-01-15
       • Do not contact: No

       What worked:
         • Mentioning specific product features
         • Keeping email under 150 words
```

### Managing Campaigns

```
You: Pause all emails

🤖 MuBot: ⏸️  Campaign paused. Reason: User requested

       No emails will be sent until you resume.

You: Resume campaign

🤖 MuBot: ▶️  Campaign resumed! Emails can now be sent.
```

---

## 📚 Complete Command Reference

### Email Commands

| Say This | What It Does |
|----------|--------------|
| "Draft a cold email for [role] at [company]" | Creates personalized email draft |
| "Draft an email to [name] at [company]" | Draft with specific recipient |
| "Send the email" | Sends last drafted email (asks confirmation) |
| "Send the email to [company]" | Sends email to specific company |
| "Schedule a follow-up in [N] days" | Schedules follow-up |
| "Check if anyone replied" | Checks Gmail for responses |
| "Check replies from [company]" | Checks specific company replies |

### Pipeline Commands

| Say This | What It Does |
|----------|--------------|
| "Add [company] to my pipeline" | Adds new opportunity |
| "Add [company] - [role]" | Adds with specific role |
| "Add [company] with salary [range]" | Adds with salary info |
| "What's in my pipeline?" | Shows all opportunities |
| "Show my pipeline" | Same as above |
| "Move [company] to [stage]" | Updates opportunity stage |
| "Update [company] stage to [stage]" | Same as above |
| "Remove [company] from pipeline" | Deletes opportunity |

### Stage Names

Valid stages for the `Move` command:
- `identified` — Found the role
- `researched` — Researched company
- `contacted` — Sent cold email
- `applied` — Formal application
- `replied` — Received response
- `phone_screen` — Phone/video screen
- `interview` — In interviews
- `final_round` — Final round
- `offer` — Have offer
- `negotiating` — Negotiating
- `accepted` — Accepted offer
- `rejected` — Rejected

### Information Commands

| Say This | What It Does |
|----------|--------------|
| "Show my daily summary" | Today's stats |
| "Weekly summary" | Past week stats |
| "What do I know about [company]?" | Company outreach history |
| "Tell me about [company]" | Same as above |
| "Help" | Shows available commands |

### Control Commands

| Say This | What It Does |
|----------|--------------|
| "Pause all emails" | Stops sending |
| "Pause campaign" | Same as above |
| "Resume campaign" | Re-enables sending |
| "Resume emails" | Same as above |
| "Exit" or "quit" | Closes MuBot |

---

## 🔄 Interactive Flows

### Email Sending Flow

1. **Draft** → `"Draft an email for Google"`
2. **Review** ← MuBot shows the draft
3. **Send** → `"Send the email"`
4. **Confirm** ← MuBot asks for confirmation
5. **Yes** → `"yes"`
6. **Done** ← ✅ Email sent!

### Multi-Contact Campaign

```
You: Add Meta to my pipeline
You: Draft an email for the engineer role at Meta to Sarah Chen
You: Send the email
You: yes
You: Draft an email for the engineer role at Meta to the recruiter
You: Send the email
You: yes
You: Draft an email for the engineer role at Meta to David Park
You: Send the email
You: yes
You: Schedule follow-ups in 5 days
```

---

## 🎯 Tips for Best Results

### Be Specific

✅ **Good:**
- "Draft an email for the Senior Engineer role at Stripe"
- "Add Google - Staff Engineer to my pipeline"
- "Move Meta to interview stage"

❌ **Vague:**
- "Draft an email" (missing company and role)
- "Add company" (missing company name)
- "Update stage" (missing company and target stage)

### Use Natural Language

MuBot understands variations:

- "Draft a cold email..."
- "Write an email..."
- "Create an email..."
- "Prepare an email..."

- "Add to pipeline..."
- "Put in pipeline..."
- "Track opportunity..."

### Confirmation Required

For **sending emails**, MuBot always asks for confirmation:

```
🤖 MuBot: Type 'yes' to confirm sending, or 'edit' to modify.

You: yes
```

This is a **safety feature** — you'll never accidentally send an email.

---

## 🛠️ Behind the Scenes

### How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   You Type   │────▶│  Intent Parser   │────▶│    LLM Parse    │
│  "Draft..."  │     │   (NLP + LLM)    │     │  Intent + Params │
└──────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                       ┌──────────────────┐              │
                       │   MuBot Replies  │◀─────────────┘
                       │  "✉️ Drafted..."  │     ┌──────────────────┐
                       └──────────────────┘     │   Execute Action  │
                                                 │   agent.draft...  │
                                                 └──────────────────┘
```

1. **Parse**: LLM converts natural language to structured intent
2. **Execute**: MuBot calls the appropriate agent method
3. **Respond**: Formatted response shown to you

### Context Awareness

MuBot remembers:
- Last drafted email (for "send the email")
- Your profile from USER.md
- Company history
- Daily email count

---

## 🐛 Troubleshooting

### "I'm not sure what you'd like to do"

MuBot didn't understand. Try:
- Being more specific (include company name, role)
- Using simpler language
- Checking the command reference above

### "I need to know which company"

You didn't specify a company. Add it:
- ❌ "Draft an email"
- ✅ "Draft an email for Google"

### "Draft one first"

You're trying to send but haven't drafted yet:
```
You: Send the email
🤖 MuBot: ❌ I don't know which email to send. Draft one first...

You: Draft an email for Stripe
[Draft shown]

You: Send the email
[Works!]
```

### "Run 'mubot-init' first"

You haven't set up MuBot yet:
```bash
mubot-init
```

---

## 💡 Advanced: Combining with Python

For complex workflows, use the chat for quick actions, then Python for automation:

```bash
# Quick actions in chat
mubot-chat
> Add Meta to my pipeline
> Draft an email for Meta

# Complex automation in Python
python my_campaign.py
```

---

**Happy job hunting! 🚀**

Type `mubot-chat` and start talking to your job search assistant!
