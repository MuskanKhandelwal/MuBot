"""
Follow-up Email Prompts (XML Format)

Three separate prompts for Follow-up 1, 2, and 3
"""

# Follow-up 1: Gentle reminder (3-5 days)
FOLLOWUP_1_PROMPT = """<role>
You are writing a gentle follow-up email for a job application.
</role>

<context>
<original_email>
{original_email}
</original_email>
<days_since>4 days</days_since>
<company>{company}</company>
<role>{role}</role>
<recipient_name>{recipient_name}</recipient_name>
<sender_name>{sender_name}</sender_name>
<sender_phone>{sender_phone}</sender_phone>
<sender_linkedin>{sender_linkedin}</sender_linkedin>
</context>

<instructions>
<purpose>Gentle reminder - they might be busy, not ignoring</purpose>
<tone>Polite, brief, add one new piece of value</tone>
<length>Under 80 words</length>

<structure>
1. Hi {recipient_name},
2. Quick reference to original email
3. ONE new achievement or value add
4. Simple question
5. Best, {sender_name} | Phone | LinkedIn
</structure>

<rules>
- Use actual name: {recipient_name} (NOT placeholders like [name])
- Use actual sender name: {sender_name}
- Include sender phone: {sender_phone}
- Include sender LinkedIn: {sender_linkedin}
- Under 80 words total
- Sound human, not corporate
</rules>
</instructions>

<output>
<subject>Following up on {role} application</subject>
<email_body>
[email with actual names, no placeholders]
</email_body>
</output>
"""


# Follow-up 2: Brief check-in (7-10 days)
FOLLOWUP_2_PROMPT = """<role>
You are writing a brief follow-up email for a job application.
</role>

<context>
<original_email>
{original_email}
</original_email>
<days_since>8 days</days_since>
<company>{company}</company>
<role>{role}</role>
<recipient_name>{recipient_name}</recipient_name>
<sender_name>{sender_name}</sender_name>
<sender_phone>{sender_phone}</sender_phone>
<sender_linkedin>{sender_linkedin}</sender_linkedin>
</context>

<instructions>
<purpose>Brief check-in - they're likely busy</purpose>
<tone>Even shorter, assume they're swamped</tone>
<length>Under 60 words</length>

<structure>
1. Hi {recipient_name},
2. Quick reference (1 sentence)
3. ONE specific value add or update
4. Simple yes/no question
5. Best, {sender_name} | Phone | LinkedIn
</structure>

<rules>
- Use actual name: {recipient_name} (NOT placeholders)
- Use actual sender name: {sender_name}
- Include phone and LinkedIn
- Under 60 words
- Shorter than follow-up 1
</rules>
</instructions>

<output>
<subject>Quick check-in: {role}</subject>
<email_body>
[brief email with actual names]
</email_body>
</output>
"""


# Follow-up 3: Final attempt (14+ days)
FOLLOWUP_3_PROMPT = """<role>
You are writing a final follow-up email for a job application.
</role>

<context>
<original_email>
{original_email}
</original_email>
<days_since>10+ days</days_since>
<company>{company}</company>
<role>{role}</role>
<recipient_name>{recipient_name}</recipient_name>
<sender_name>{sender_name}</sender_name>
<sender_phone>{sender_phone}</sender_phone>
<sender_linkedin>{sender_linkedin}</sender_linkedin>
</context>

<instructions>
<purpose>Final attempt - leave on good terms</purpose>
<tone>Graceful exit, professional, no pressure</tone>
<length>Under 50 words</length>

<structure>
1. Hi {recipient_name},
2. Brief reference
3. Graceful closing (keep door open)
4. Best wishes
5. Best, {sender_name} | Phone | LinkedIn
</structure>

<rules>
- Use actual name: {recipient_name} (NOT placeholders)
- Use actual sender name: {sender_name}
- Include contact info
- Under 50 words
- This is the LAST follow-up - be graceful
</rules>
</instructions>

<output>
<subject>Final follow-up: {role}</subject>
<email_body>
[short graceful email]
</email_body>
</output>
"""
