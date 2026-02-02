"""
Prompt Templates for MuBot

This module contains all LLM prompts used by the agent. Centralizing prompts
makes it easier to:
- Iterate on prompt engineering
- Maintain consistency across the application
- A/B test different prompt variations
- Localize for different languages

Each prompt is designed to be used with Python's str.format() method.
"""

# =============================================================================
# Core System Prompt
# =============================================================================
# This is the foundational prompt that defines the agent's identity,
# capabilities, and behavioral constraints. It's included in every conversation.
# =============================================================================

SYSTEM_PROMPT = """You are MuBot, an AI-powered job search assistant specializing in cold email outreach.

YOUR MISSION:
Help the user find job opportunities, craft personalized cold emails, send them safely, track outcomes, and follow up intelligently while continuously improving messaging based on responses.

YOUR ROLE:
- Act as a job-search copilot, NOT an autonomous spammer
- Prioritize quality over quantity in outreach
- Respect recipient privacy and preferences
- Learn from responses to improve future emails

CORE CAPABILITIES:
1. Email Creation: Draft personalized cold emails for specific roles/companies
2. Personalization: Enrich emails using recipient background and company context
3. A/B Testing: Generate multiple variants optimized for response rates
4. Scheduling: Send emails at optimal times, schedule follow-ups
5. Inbox Monitoring: Check replies, classify responses, summarize activity
6. Pipeline Management: Track applications, remind about next steps

SAFETY & ETHICS RULES (NON-NEGOTIABLE):
- NEVER send emails without explicit user approval
- NEVER scrape personal email addresses from the web
- ALWAYS include unsubscribe language by default
- ALWAYS respect rate limits (max {max_daily_emails} emails/day)
- NEVER mass-blast identical emails
- ALWAYS pause if recipient shows no-contact signals
- ALWAYS allow one-click opt-out

MEMORY SYSTEM:
You have access to file-backed memory:
- USER.md: User preferences, tone, signature, limits
- MEMORY.md: Career goals, target roles, outreach rules
- TOOLS.md: Gmail labels, resume versions, portfolio links
- memory/YYYY-MM-DD.md: Daily activity logs
- heartbeat-state.json: Scheduled tasks and follow-ups

Before drafting or sending, you MUST:
1. Load USER.md for tone and signature preferences
2. Check MEMORY.md for career goals and constraints
3. Look up prior contact with the same company
4. Verify outreach limits haven't been exceeded

RESPONSE FORMAT:
- Be concise but thorough
- Show your reasoning when asked
- Present email drafts in clean, copy-pasteable format
- Highlight personalization elements you used
- Flag any safety concerns immediately

Current date: {current_date}
User timezone: {timezone}
Today's email count: {today_email_count}/{max_daily_emails}
"""


# =============================================================================
# Email Drafting Prompt
# =============================================================================
# Used when creating a new cold email from scratch.
# =============================================================================

EMAIL_DRAFT_PROMPT = """Draft a professional cold email for a job opportunity.

USER CONTEXT:
Name: {user_name}
Background: {user_background}
Target Role: {target_role}
Target Company: {target_company}
Company Context: {company_context}
Tone Preference: {tone_preference}

RECIPIENT CONTEXT:
Name: {recipient_name}
Title: {recipient_title}
Background: {recipient_background}
Connection: {connection_type}

JOB CONTEXT:
Role Title: {job_title}
Job Description Summary: {job_summary}
Why Interested: {interest_reason}

OUTREACH HISTORY WITH THIS COMPANY:
{company_history}

INSTRUCTIONS:
1. Write a compelling subject line (max 60 chars)
2. Keep the email body concise (150-200 words max)
3. Lead with a personalized hook based on recipient/company
4. Briefly mention relevant experience/achievements
5. Include specific ask (call, referral, advice)
6. Add professional signature with contact info
7. Include one-click unsubscribe option
8. FORMATTING: Add blank lines between paragraphs for readability

TONE GUIDELINES:
- Formal: Polished, traditional, conservative language
- Friendly: Warm, conversational, approachable
- Bold: Confident, direct, stands out

OUTPUT FORMAT:
Subject: [subject line]

[email body ONLY - with proper paragraph spacing, blank lines between paragraphs]

---
FOR AGENT REFERENCE (NOT PART OF EMAIL):
Personalization elements used:
1. [element 1]
2. [element 2]

Why this should work: [brief reasoning]
"""


# =============================================================================
# Email Personalization Prompt
# =============================================================================
# Used to enhance an existing email draft with more personalization.
# =============================================================================

EMAIL_PERSONALIZE_PROMPT = """Enhance this cold email with deeper personalization.

ORIGINAL EMAIL:
{original_email}

ADDITIONAL CONTEXT DISCOVERED:
Recipient Recent Activity: {recipient_activity}
Company Recent News: {company_news}
Shared Connections: {shared_connections}
Mutual Interests: {mutual_interests}

PERSONALIZATION STRATEGY:
1. Reference specific, recent recipient achievement or post
2. Connect company news to user's skills/interests
3. Mention mutual connections naturally (if appropriate)
4. Show genuine research without being creepy

CONSTRAINTS:
- Keep the same overall length
- Maintain original tone
- Don't force connections that don't exist
- Be specific but respectful of privacy

OUTPUT:
Provide the enhanced email with [brackets] around new personalization elements so the user can see what was added.
"""


# =============================================================================
# Follow-Up Drafting Prompt
# =============================================================================
# Used to create polite follow-up emails when no response received.
# =============================================================================

FOLLOWUP_PROMPT = """Draft a polite follow-up email for an unresponded cold outreach.

ORIGINAL EMAIL:
{original_email}

ORIGINAL SEND DATE: {original_date}
DAYS SINCE: {days_elapsed}
FOLLOW-UP NUMBER: {followup_number} of {max_followups}

CONVERSATION HISTORY:
{thread_history}

FOLLOW-UP STRATEGY:
- 1st follow-up (3-5 days): Gentle reminder, add value
- 2nd follow-up (7-10 days): Brief, assume busy
- 3rd follow-up (14+ days): Final attempt, graceful exit

TONE ADJUSTMENTS:
- Never sound annoyed or demanding
- Assume the recipient is busy, not ignoring
- Add new value or context in each follow-up
- Make it easy to respond (yes/no question)

OUTPUT:
Subject: [follow-up subject line]

[follow-up body]

Note: This will be the {followup_number} follow-up. After {max_followups}, we should stop unless there's a response.
"""


# =============================================================================
# Response Classification Prompt
# =============================================================================
# Used to categorize incoming replies for pipeline tracking.
# =============================================================================

RESPONSE_CLASSIFY_PROMPT = """Classify this email response to a job outreach.

ORIGINAL EMAIL SENT:
{original_email}

INCOMING RESPONSE:
{response_email}

CLASSIFICATION CATEGORIES:
1. POSITIVE: Interested, wants to talk, asking for next steps, asking for resume
2. NEUTRAL: Acknowledged, forwarded to someone, needs time, vague
3. REJECTION: Not hiring, not interested, role filled, no fit
4. NO-RESPONSE: Automated reply, out-of-office, bounce
5. NEEDS-REPLY: Asking question, requesting info, scheduling

EXTRACT:
- Sentiment score (-1 to +1)
- Key action items (if any)
- Suggested next step
- Urgency level (low/medium/high)

OUTPUT FORMAT:
Category: [CATEGORY]
Sentiment: [score]/1.0
Urgency: [level]

Key Points:
- [point 1]
- [point 2]

Suggested Next Action: [action]

Draft Response (if needed): [optional draft reply]
"""


# =============================================================================
# A/B Test Generation Prompt
# =============================================================================
# Used to create multiple variants of an email for testing.
# =============================================================================

AB_TEST_PROMPT = """Generate {num_variants} distinct variants of this cold email for A/B testing.

BASE EMAIL:
{base_email}

VARIATION STRATEGIES TO APPLY:
1. Subject line angles: Question vs. Statement vs. Value prop
2. Opening hooks: Personal achievement vs. Company news vs. Shared interest
3. Call-to-action: Direct ask vs. Soft ask vs. Advice request
4. Length: Detailed vs. Ultra-concise

DISTRIBUTION RULES:
- Each variant should differ in ONE major element
- Keep the core message consistent
- Ensure all variants maintain professionalism
- Label each variant clearly

OUTPUT:
For each variant, provide:
- Variant Name (e.g., "A: Question Subject")
- What was changed and why
- The full email text

TESTING NOTES:
What to measure: [open rate, reply rate, positive response rate]
Minimum sample size: 20 sends per variant
Statistical significance threshold: 95% confidence
"""


# =============================================================================
# Daily Summary Prompt
# =============================================================================
# Used to generate daily activity summaries for the user.
# =============================================================================

DAILY_SUMMARY_PROMPT = """Summarize today's job outreach activity.

DATE: {date}

EMAILS SENT TODAY:
{emails_sent}

REPLIES RECEIVED:
{replies_received}

POSITIVE RESPONSES:
{positive_responses}

REJECTIONS:
{rejections}

PIPELINE CHANGES:
{pipeline_changes}

FOLLOW-UPS SCHEDULED:
{scheduled_followups}

SUMMARY REQUIREMENTS:
1. Highlight wins and positive momentum
2. Flag any urgent replies needing response
3. Note patterns in what's working
4. Suggest adjustments for tomorrow
5. Keep it scannable (bullet points)

OUTPUT:
## Today's Summary ({date})

### 📊 Stats
- Emails sent: X
- Replies: X (X% response rate)
- Positive: X | Rejections: X

### 🎉 Wins
- [highlight positive developments]

### ⚡ Action Needed
- [urgent items requiring user attention]

### 📈 Insights
- [patterns in what's working]

### 🎯 Tomorrow's Suggestions
- [recommended next steps]
"""


# =============================================================================
# Memory Update Prompt
# =============================================================================
# Used to extract learnings and update memory files.
# =============================================================================

MEMORY_UPDATE_PROMPT = """Extract learnings from this interaction and suggest memory updates.

INTERACTION:
{interaction_description}

OUTCOME:
{outcome}

CURRENT MEMORY STATE:
{current_memory}

EXTRACTION TASKS:
1. Identify what worked well
2. Identify what didn't work
3. Extract recipient/company-specific insights
4. Suggest template improvements
5. Update outreach rules if needed

MEMORY UPDATE RULES:
- Only add factual, observable information
- Separate personal preferences from universal truths
- Tag insights by company, role, or industry when relevant
- Include date stamps for time-sensitive info

OUTPUT:
Suggested updates to:
- MEMORY.md (career goals, target roles, outreach rules)
- TOOLS.md (templates, labels, resources)
- Company-specific notes (if applicable)
- Template improvements (if applicable)
"""
