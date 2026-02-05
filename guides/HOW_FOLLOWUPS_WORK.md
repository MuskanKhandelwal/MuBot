# How Follow-Ups Work

This guide explains how MuBot schedules and sends follow-up emails automatically.

---

## 📅 Follow-Up Schedule

When you send an email, MuBot schedules **3 follow-ups**:

| Follow-up | Working Days | Calendar Days* | Purpose |
|-----------|--------------|----------------|---------|
| **#1** | 4 | ~5-6 | Gentle reminder |
| **#2** | 8 | ~10-12 | Add value/context |
| **#3** | 10 | ~14 | Final attempt |

*Depends on weekends

**Working days** = Monday-Friday (skips Saturday & Sunday)

### Example Timeline

**Email sent: Monday, Feb 3, 2025**

| Date | Day | Action |
|------|-----|--------|
| Feb 3 | Monday | Original email sent |
| Feb 7 | Friday | Follow-up #1 (4 working days) |
| Feb 13 | Thursday | Follow-up #2 (8 working days) |
| Feb 17 | Monday | Follow-up #3 (10 working days) |

---

## 🔧 How Follow-Ups Are Stored

Follow-ups are saved in `data/heartbeat-state.json`:

```json
{
  "scheduled_followups": [
    {
      "entry_id": "uuid-123",
      "company": "Netflix",
      "role": "Data Scientist",
      "email": "hiring@netflix.com",
      "due_at": "2025-02-07T09:00:00",
      "followup_name": "Follow-up 1",
      "sent": false
    }
  ]
}
```

---

## 🚀 How to Send Follow-Ups

### Option 1: Automatic (Heartbeat)

Run the heartbeat daily to check and send due follow-ups:

```bash
# Manual check
python -m scripts.run_heartbeat

# Or run the auto campaign which checks follow-ups
python auto_campaign.py --followups-only
```

### Option 2: Check & Send Manually

```bash
# Start chat
python mubot_chat_enhanced.py
```

Then type:
```
You: Check follow-ups
🤖 Bot: 📅 3 pending follow-ups:
      • Netflix - Follow-up #1 - Due today
      • Google - Follow-up #2 - Due tomorrow
      • Stripe - Follow-up #3 - Due in 3 days

You: Send Netflix follow-up
🤖 Bot: ✉️ Follow-up sent!
```

### Option 3: Scheduled (Cron)

Add to crontab for automatic daily checks:

```bash
# Edit crontab
crontab -e

# Add this line - runs every weekday at 10 AM
0 10 * * 1-5 cd /path/to/mubot && python auto_campaign.py --followups-only >> logs/followups.log 2>&1
```

---

## ✉️ What Follow-Up Emails Look Like

### Follow-Up #1 (4 working days)

```
Subject: Re: Interest in Data Scientist Role

Hi [Name],

I hope this message finds you well. I wanted to follow up on my 
email from [date] regarding the Data Scientist position at [Company].

I understand you have a busy inbox. I remain very interested in 
the opportunity and would welcome the chance to discuss how my 
background in [skills] could contribute to your team.

Is there a better way to reach you, or would you prefer I check 
back at a later time?

Best regards,
Muskan
```

### Follow-Up #2 (8 working days)

```
Subject: Following up - Data Scientist Role

Hi [Name],

I wanted to make sure my message didn't get buried. I'm still 
very interested in the Data Scientist role and would love to 
connect when you have a moment.

I recently [brief update - new achievement/certification] which 
I believe strengthens my candidacy for this position.

Thank you for your time.

Best,
Muskan
```

### Follow-Up #3 (10 working days)

```
Subject: Final follow-up - Data Scientist

Hi [Name],

I hope you're doing well. This will be my final follow-up regarding 
the Data Scientist position, as I don't want to clutter your inbox.

If the timing isn't right, I completely understand. I'd appreciate 
staying in touch for future opportunities.

Thank you for your consideration.

Best regards,
Muskan
```

---

## 🎯 How It Works (Technical)

```
1. Send Email
   └─→ MuBot schedules 3 follow-ups in heartbeat-state.json

2. Daily Check (run_heartbeat or auto_campaign)
   └─→ Read heartbeat-state.json
   └─→ Check which follow-ups are due (due_at <= now)
   
3. Send Due Follow-Ups
   └─→ Draft follow-up email based on original
   └─→ Ask for confirmation (or auto-send if configured)
   └─→ Mark as sent: "sent": true
   
4. Auto-Cancel on Reply
   └─→ If recipient replies, all pending follow-ups cancelled
```

---

## 🛠️ Managing Follow-Ups

### Check Pending Follow-Ups

```bash
# Via chat
python mubot_chat_enhanced.py
> Check follow-ups

# Via script
python auto_campaign.py --followups-only --dry-run
```

### Cancel a Follow-Up

Currently manual - edit `data/heartbeat-state.json` and remove the entry, or wait for reply (auto-cancels).

### View in Heartbeat State

```bash
cat data/heartbeat-state.json | jq '.scheduled_followups'
```

---

## ❓ Troubleshooting

### Follow-ups not sending?

1. **Check heartbeat state:**
   ```bash
   cat data/heartbeat-state.json
   ```

2. **Verify follow-ups are scheduled:**
   Look for `"scheduled_followups"` array with your jobs

3. **Check if already sent:**
   Look for `"sent": true` - if true, already sent

4. **Run manually to see errors:**
   ```bash
   python auto_campaign.py --followups-only
   ```

### How to re-send a follow-up?

1. Edit `data/heartbeat-state.json`
2. Find the follow-up entry
3. Change `"sent": true` to `"sent": false`
4. Run `python auto_campaign.py --followups-only`

---

## 📝 Summary

| What | How |
|------|-----|
| **Schedule** | Auto-scheduled when you send email |
| **Timing** | 4, 8, 10 working days |
| **Storage** | `data/heartbeat-state.json` |
| **Send** | Via heartbeat or auto_campaign script |
| **Auto-cancel** | On reply received |
| **Max** | 3 follow-ups per job |

---

**Questions?** Check `FOLLOWUP_GUIDE.md` for more details!
