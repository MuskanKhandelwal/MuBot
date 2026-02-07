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
<recipient>{recipient_name}</recipient>
<requirements>{jd_requirements}</requirements>
</job_details>

<resume_attachment>{resume_filename}</resume_attachment>
</context>

<instructions>
<word_count>UNDER 120 WORDS TOTAL</word_count>

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
</forbidden_phrases>

<use_instead>
<alternative>"I came across the posting for [Role]"</alternative>
<alternative>"I've done X for Y years" (specific)</alternative>
<alternative>"Built/made/created [thing] that [result with number]"</alternative>
<alternative>"Looking forward to hearing from you"</alternative>
</use_instead>

<format>
<greeting>Hi [actual name],</greeting>
<blank_line />
<body>[I came across the role + what you built with numbers]</body>
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
<rule>Include numbers when possible</rule>
<rule>NO filler words: "several", "various", "multiple", "enhanced", "optimized" (unless you have numbers)</rule>
<rule>Sign-off MUST be on new lines: "Best," then name on next line</rule>
</rules>
</instructions>

<example>
<subject>Data Scientist Role at {target_company}</subject>
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
</forbidden>

<guidelines>
<start>Start with something REAL: "Saw the posting", "Came across the role"</start>
<match>Mention ONE specific thing from my background that matches their job</match>
<question>End with ONE simple question</question>
<sign>-{user_first_name}</sign>
</guidelines>

<example>
<email>
Hi Sarah,

Saw the Data Scientist posting. I've spent 3 years building ML models at scale, recently cut prediction latency by 40%.

Worth a quick chat?

-Muskan
</email>
</example>

<output>
<subject>[natural subject]</subject>
<email_body>[casual, short, real email]</email_body>
</output>
"""
