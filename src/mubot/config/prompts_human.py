"""
Human-Style Email Prompts for MuBot (XML Format)

These prompts create shorter, more conversational, and human-like emails.
Using XML structure for better LLM parsing.
"""

# JD-matched email with strict constraints (XML format)
EMAIL_DRAFT_JD_MATCH_PROMPT = """<role>
You are an expert at writing short, polite cold emails for job applications.
</role>

<context>
<user_profile>
<name>{user_name}</name>
<background>{user_background}</background>
<skills>{user_key_skills}</skills>
<resume_highlights>{user_resume_highlights}</resume_highlights>
<phone>{user_phone}</phone>
<linkedin>{user_linkedin}</linkedin>
</user_profile>

<job_details>
<company>{target_company}</company>
<role>{target_role}</role>
<job_reference>{job_reference}</job_reference>
<recipient>{recipient_name}</recipient>
<requirements>{jd_requirements}</requirements>
</job_details>

<resume_attachment>{resume_filename}</resume_attachment>
</context>

<critical>
ONLY use facts, achievements, and numbers that appear explicitly in the profile above.
Do NOT invent metrics, projects, companies, or experiences. If a number is not in the profile, do not include one.
Do NOT combine two separate facts to create a new claim. Example: if the profile lists "RAG" as a skill and "AWS" as a skill, you CANNOT write "deployed RAG on AWS" — that specific combination was never stated. Each sentence must be traceable to a single explicit statement in the profile.
</critical>

<instructions>
<word_count>UNDER 120 WORDS TOTAL</word_count>

<subject_rule>Use exactly: {subject_instruction}. If a job_reference is provided, it MUST appear in the subject.</subject_rule>

<forbidden_phrases>
<phrase>"Your mission to revolutionize..."</phrase>
<phrase>"I was inspired by your vision..."</phrase>
<phrase>"I have a track record in..."</phrase>
<phrase>"With my extensive background..."</phrase>
<phrase>"I would be an asset..."</phrase>
<phrase>"I am excited to apply..."</phrase>
<phrase>"developing and deploying"</phrase>
<phrase>"focusing on creating"</phrase>
<phrase>"end-to-end, production-ready systems"</phrase>
<word>leverage</word>
<word>spearheaded</word>
<word>pivotal</word>
<word>innovative</word>
<word>strategic</word>
<word>utilize</word>
<punctuation>em dashes (— or –) — use plain hyphens or rewrite the sentence</punctuation>
</forbidden_phrases>

<use_instead>
<alternative>"I came across the posting for [Role]"</alternative>
<alternative>"I've done X for Y years" (specific, only if stated in profile)</alternative>
<alternative>"Built/made/created [thing] that [result]" (only real results from profile)</alternative>
<alternative>"Looking forward to hearing from you"</alternative>
</use_instead>

<matching_instructions>
BEFORE writing the email, do this mental step:
1. Look at the JD requirements (especially DIFFERENTIATORS)
2. Find the 1-2 places where the candidate's profile EXPLICITLY mentions something that matches
3. Lead the email body with THAT specific match — not generic achievements
4. If no exact match exists, use the closest real fact from the profile — never invent one

Example: if JD mentions "knowledge graphs" and profile mentions "KG-RAG", that IS a match — use it.
Example: if JD mentions "multimodal" and profile does NOT mention it — do NOT claim multimodal experience.
</matching_instructions>

<format>
<greeting>Hi [actual name],</greeting>
<blank_line />
<body>[I came across the role + the MOST SPECIFIC match between my background and their requirements]</body>
<blank_line />
<ask>[Simple ask]</ask>
<blank_line />
<sign_off>
Best,
{user_first_name}
{user_phone} | {user_linkedin}
</sign_off>
</format>

<rules>
<rule>Use active verbs: "Built" not "I've built several"</rule>
<rule>Only include numbers explicitly stated in the profile — never invent them</rule>
<rule>Only claim skills/experience that appear in the profile — never invent matches to JD requirements</rule>
<rule>NEVER combine years of experience with specific tools unless the profile explicitly links them (e.g. do NOT write "3+ years with Snowflake" just because the profile says "3+ years" and lists Snowflake separately)</rule>
<rule>Do NOT say "I've attached my resume" - it's obvious</rule>
<rule>NO filler words: "several", "various", "multiple", "enhanced", "optimized" (unless you have a real number from the profile)</rule>
<rule>Sign-off MUST be on new lines: "Best," then name on next line</rule>
<rule>NEVER write disclaimers, apologies, or negations about missing skills. Do NOT write phrases like "my current experience is in X rather than Y", "Note: I haven't used Z but I'm comfortable learning", or any acknowledgment of gaps. If a JD requirement is not in the profile, simply omit it — never explain or apologize for it.</rule>
<rule>NEVER invent a deployment platform (AWS, GCP, Azure) unless it is explicitly stated in context of a specific project. Do NOT assume cloud platform from a skill list item alone.</rule>
</rules>
</instructions>

<example>
<subject>Data Scientist II - R2619158 at {target_company}</subject>  <!-- include job_reference if present -->
<email>
Hi Tanmai,

I came across the Data Scientist role at ZS and wanted to express my interest.

I have 3+ years of experience building Python-based AI systems, including models that reduced latency by 40%.

I'd love to learn more about the team. Looking forward to hearing from you.

Best,
Muskan Khandelwal
+1 8574235724 | https://www.linkedin.com/in/muskan-khandelwal/
</email>
</example>

<output_format>
<subject>[natural subject line]</subject>
<email_body>
[email content here - greeting, body, ask, sign-off]
</email_body>
</output_format>

---
For tracking: Which of my skills matched their requirements
"""


# Ultra-short email for quick sends (XML format)
EMAIL_DRAFT_SHORT_PROMPT = """<role>
Write a brief cold email under 80 words.
</role>

<context>
<user>{user_name}, {user_background}</user>
<company>{target_company}</company>
<role>{target_role}</role>
</context>

<requirements>
<word_count>Max 80 words</word_count>
<tone>Casual like texting</tone>
<achievement>One specific achievement with number</achievement>
<ask>Simple ask at the end</ask>
<sign_off>Sign with -{user_first_name}</sign_off>
</requirements>

<example>
<email>
Hi John,

Came across the Data Scientist role. Built recommendation systems serving 2M+ users, improved CTR by 15%.

Worth a quick chat?

-Muskan
</email>
</example>

<output>
<subject>[subject]</subject>
<email>[email body]</email>
</output>
"""


# Human-style generic email (XML format)
EMAIL_DRAFT_HUMAN_PROMPT = """<role>
Write a short, casual cold email like you're texting a friend about a job.
</role>

<context>
<name>{user_name}</name>
<background>{user_background}</background>
<experience>{user_experience}</experience>
<skills>{user_skills}</skills>

<target>
<role>{target_role}</role>
<company>{target_company}</company>
<recipient>{recipient_name}</recipient>
<requirements>{job_summary}</requirements>
</target>

<attachment>{resume_filename}</attachment>
</context>

<critical>
ONLY use facts and achievements from the context above. Do NOT invent numbers, projects, companies, or results.
If no specific metric is provided, describe the work without fabricating a number.
Do NOT combine two separate facts to create a new claim. Example: if the profile lists "RAG" as a skill and "AWS" as a skill, you CANNOT write "deployed RAG on AWS" — that specific combination was never stated. Each sentence must be traceable to a single explicit statement in the profile.
</critical>

<constraints>
<word_count>MAXIMUM 100 WORDS TOTAL</word_count>
<paragraphs>MAX 3 short paragraphs, 1-2 sentences each</paragraphs>
<attachment_note>Do NOT say "I've attached my resume" - that's obvious</attachment_note>
</constraints>

<forbidden>
<phrase>"I am writing to"</phrase>
<phrase>"I would like to express"</phrase>
<phrase>"I have a track record"</phrase>
<phrase>"Your mission to..."</phrase>
<phrase>"I was inspired by your vision"</phrase>
<word>leverage</word>
<word>spearheaded</word>
<word>pivotal</word>
<word>innovative</word>
<punctuation>em dashes (— or –) — use plain hyphens or rewrite the sentence</punctuation>
</forbidden>

<guidelines>
<start>Start with something REAL: "Saw the posting", "Came across the role"</start>
<match>Mention ONE specific thing from my background that matches their job — facts only, no invented metrics</match>
<question>End with ONE simple question</question>
<sign>-{user_first_name}</sign>
</guidelines>

<no_disclaimers>
NEVER write disclaimers, apologies, or negations about missing skills or platforms.
Do NOT write: "my current experience is in AWS rather than GCP", "Note: I haven't worked with X but...", or any acknowledgment of skill gaps.
If a requirement is not in the profile, omit it entirely. Never explain or apologize for the omission.
NEVER invent a cloud platform (AWS, GCP, Azure) for a specific project unless explicitly stated.
</no_disclaimers>

<example>
<email>
Hi Sarah,

Saw the Data Scientist posting. I've spent 3 years building ML systems across healthcare and telecom — reduced outages for 1M+ users and cut operational uncertainty by 22%.

Worth a quick chat?

-Muskan
</email>
</example>

<output>
<subject>[natural subject]</subject>
<email_body>[casual, short, real email]</email_body>
</output>
"""


# Follow-up email (XML format)
FOLLOWUP_PROMPT_XML = """<role>
You are an expert at writing polite, effective follow-up emails for job applications.
</role>

<context>
<original_email>
{original_email}
</original_email>

<send_date>{original_date}</send_date>
<days_elapsed>{days_elapsed}</days_elapsed>
<followup_number>{followup_number}</followup_number>
<max_followups>{max_followups}</max_followups>

<thread_history>
{thread_history}
</thread_history>
</context>

<strategy>
<first_followup>
<when>3-5 days after initial email</when>
<tone>Gentle reminder, add value</tone>
<approach>Brief, assume they're busy</approach>
</first_followup>

<second_followup>
<when>7-10 days after initial email</when>
<tone>Even briefer</tone>
<approach>One-line check-in</approach>
</second_followup>

<third_followup>
<when>14+ days after initial email</when>
<tone>Final attempt, graceful</tone>
<approach>Last try, leave on good terms</approach>
</third_followup>
</strategy>

<rules>
<rule>Never sound annoyed or demanding</rule>
<rule>Assume the recipient is busy, not ignoring</rule>
<rule>Add new value or context in each follow-up</rule>
<rule>Make it easy to respond (yes/no question)</rule>
<rule>This is follow-up {followup_number} of {max_followups}</rule>
</rules>

<format>
<greeting>Hi [name],</greeting>
<blank_line />
<body>Reference the original email + new value/context</body>
<blank_line />
<question>Simple yes/no question</question>
<blank_line />
<sign_off>Best, [Your Name]</sign_off>
</format>

<example>
<subject>Following Up on Data Scientist Application</subject>
<email_body>
Hi Sarah,

I hope you're doing well. I wanted to follow up on my email from last week about the Data Scientist role at Stripe.

I recently completed a project that reduced model inference time by 35% using similar techniques to what Stripe uses for fraud detection. I'd love to share how this could apply to your team.

Would you be open to a quick 15-minute call this week?

Best,
Muskan
</email_body>
</example>

<output>
<subject>[follow-up subject line]</subject>
<email_body>
[follow-up body with proper spacing]
</email_body>
</output>
"""
