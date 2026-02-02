# Follow-Up Emails - Complete Guide

## Automatic Follow-Ups (Recommended)

When you draft and send an email through MuBot, it automatically schedules a follow-up!

### How It Works:

1. **Draft & Send Email**
   ```
   You: Draft an email for Data Scientist at Netflix
   [Paste JD]
   [Add recipient]
   You: send
   You: yes
   ```

2. **MuBot Auto-Schedules Follow-Up**
   ```
   🤖 MuBot: ✅ Email sent! 
   📅 Follow-up scheduled for 5 days later.
   ```

3. **Check Pending Follow-Ups**
   ```
   You: Show my daily summary
   🤖 MuBot: 📬 3 pending follow-ups
   ```

## Manual Follow-Up Scheduling

### Option 1: During Drafting

When you create a draft, specify follow-up timing:

```python
# In your custom script
draft, warnings = await agent.draft_email(
    company_name="Netflix",
    role_title="Data Scientist",
    recipient_email="hiring@netflix.com"
)

# Schedule follow-up for 7 days
success, msg = await agent.schedule_followup(draft, days_delay=7)
```

### Option 2: Via Chat Command

```
You: Schedule follow-up for Netflix in 7 days
🤖 MuBot: 📅 Follow-up scheduled for 2024-02-09
```

### Option 3: Check & Send Pending Follow-Ups

```
You: Check follow-ups
🤖 MuBot: 📬 2 follow-ups pending:
   • Netflix - Due today
   • Google - Due tomorrow

You: Send Netflix follow-up
🤖 MuBot: ✉️ Follow-up sent to Netflix!
```

## Follow-Up Email Content

MuBot automatically generates follow-up emails based on the original:

### 1st Follow-Up (3-5 days):
```
Subject: Re: Interest in Data Scientist Role

Hi [Name],

I hope this message finds you well. I wanted to follow up on my email from [date] regarding the Data Scientist position.

I understand you have a busy inbox. I remain very interested in the opportunity and would welcome the chance to discuss how my background in [skills] could contribute to [Company].

Is there a better way to reach you, or would you prefer I check back at a later time?

Best regards,
Muskan
```

### 2nd Follow-Up (7-10 days):
```
Subject: Following up - Data Scientist Role

Hi [Name],

I wanted to make sure my message didn't get buried. I'm still very interested in the Data Scientist role and would love to connect when you have a moment.

I recently [brief update - new achievement/certification] which I believe strengthens my candidacy.

Thank you for your time.

Best,
Muskan
```

### 3rd Follow-Up (14+ days):
```
Subject: Final follow-up - Data Scientist

Hi [Name],

I hope you're doing well. This will be my final follow-up regarding the Data Scientist position, as I don't want to clutter your inbox.

If the timing isn't right, I completely understand. I'd appreciate staying in touch for future opportunities.

Thank you for your consideration.

Best regards,
Muskan
```

## Managing Follow-Ups

### Check All Pending:
```
You: What follow-ups do I have?
🤖 MuBot: 
📅 Pending Follow-ups:
1. Netflix (Data Scientist) - Due: Today
2. Google (ML Engineer) - Due: Feb 10
3. Meta (AI Researcher) - Due: Feb 12
```

### Cancel a Follow-Up:
```
You: Cancel follow-up for Netflix
🤖 MuBot: ✅ Cancelled follow-up for Netflix
```

### Reschedule:
```
You: Reschedule Netflix follow-up to Feb 15
🤖 MuBot: 📅 Rescheduled to Feb 15
```

## Smart Features

### Auto-Cancel on Reply
If the recipient replies to your original email, MuBot automatically cancels the scheduled follow-up:

```
📨 New reply from Netflix received!
🤖 MuBot: Cancelling scheduled follow-up (reply received)
```

### Daily Heartbeat Check
Run the heartbeat to check for replies and send pending follow-ups:

```bash
# Manual check
python -m scripts.run_heartbeat

# Or schedule daily (add to crontab)
0 9 * * * cd /path/to/mubot && python -m scripts.run_heartbeat
```

## Custom Follow-Up Templates

You can customize follow-up templates by editing:
`src/mubot/config/prompts.py`

Look for `FOLLOWUP_PROMPT` and modify:
```python
FOLLOWUP_PROMPT = """Draft a polite follow-up email...
[Your custom template here]
"""
```

## Best Practices

| Timing | Action |
|--------|--------|
| Day 1 | Send initial email |
| Day 3-5 | 1st follow-up (gentle reminder) |
| Day 7-10 | 2nd follow-up (add value) |
| Day 14+ | 3rd follow-up (final, graceful exit) |

### Tips:
- ✅ Space follow-ups 3-5 days apart
- ✅ Add new info/value in each follow-up
- ✅ Never send more than 3 follow-ups
- ✅ Cancel if they reply
- ✅ Be polite - assume they're busy, not ignoring you

## Troubleshooting

### Follow-up not sent?
Check if:
- Campaign is paused: `resume campaign`
- Daily limit reached: `show my daily summary`
- Email already has a reply (auto-cancelled)

### Change default delay?
Edit `.env`:
```bash
DEFAULT_FOLLOWUP_DELAY_DAYS=7  # Change from default 5
```

## Quick Reference

| Command | What It Does |
|---------|--------------|
| `Draft email for [role] at [company]` | Creates draft + auto-schedules follow-up |
| `Schedule follow-up for [company] in [X] days` | Manual scheduling |
| `Check follow-ups` | Lists pending follow-ups |
| `Send [company] follow-up` | Sends pending follow-up now |
| `Cancel follow-up for [company]` | Cancels scheduled follow-up |
| `Show my daily summary` | Shows pending follow-ups count |
