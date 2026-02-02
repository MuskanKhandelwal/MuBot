"""
Enhanced Prompts with Job Description Support

These prompts are optimized to extract and use key information from job descriptions.
Add this to your prompts.py or import these separately.
"""

# Enhanced email drafting prompt that better utilizes JD
EMAIL_DRAFT_WITH_JD_PROMPT = """Draft a professional cold email for a job opportunity, HEAVILY customizing based on the job description provided.

USER PROFILE:
Name: {user_name}
Background: {user_background}
Key Skills: {user_skills}
Years Experience: {user_experience}

TARGET ROLE:
Role Title: {target_role}
Target Company: {target_company}
Company Context: {company_context}

JOB DESCRIPTION ANALYSIS:
{job_description}

From the JD above, identify:
- Must-have requirements (extract 3-5 key requirements)
- Preferred qualifications (nice-to-haves)
- Specific technologies/tools mentioned
- Team/company culture indicators
- Specific responsibilities of the role

RECIPIENT:
Name: {recipient_name}
Title: {recipient_title}

INSTRUCTIONS FOR JD-AWARE EMAIL:
1. SUBJECT LINE: Reference specific team (from JD) or key technology
   Example: "Interest in Personalization Team - Data Science Role" instead of generic "Data Scientist Application"

2. OPENING HOOK: Mention something SPECIFIC from JD:
   - Company mission mentioned in JD
   - Specific team you'd join
   - Interesting project mentioned
   - Recent company news related to the role

3. BODY - REQUIREMENT MATCHING:
   For each key requirement in JD, match to user's experience:
   
   JD Requirement: "4+ years ML experience"
   Your Response: "Over the past {user_experience} years, I've built..."
   
   JD Requirement: "Python, SQL"
   Your Response: "My technical toolkit includes Python and SQL..."
   
   JD Requirement: "Recommendation systems"
   Your Response: "I'm particularly drawn to the recommendation systems work..."

4. SPECIFIC VALUE ADD:
   - Mention specific metrics/impact from background
   - Connect to specific JD responsibilities
   - Show you understand what the role entails

5. CULTURE FIT:
   Reference company values from JD (e.g., "innovation", "freedom & responsibility")

6. CALL TO ACTION:
   Reference specific next steps mentioned in JD or typical for this role type

TONE: {tone_preference} (formal/friendly/bold)

OUTPUT FORMAT (STRICT - DO NOT INCLUDE ANALYSIS IN EMAIL BODY):

Subject: [specific, reference JD keywords]

[Email body - 150-200 words, professional]

CRITICAL FORMATTING RULE (MUST FOLLOW):
You MUST use DOUBLE NEWLINES (blank lines) between EVERY paragraph.
This is ESSENTIAL for email readability.

✅ CORRECT FORMAT:
Dear [Name],

[Paragraph 1 - opening]

[Paragraph 2 - experience]

[Paragraph 3 - JD match]

[Paragraph 4 - closing]

Best regards,
[Your name]

❌ INCORRECT FORMAT (do NOT do this):
Dear [Name],
[Paragraph 1]
[Paragraph 2]
[Paragraph 3]

REMEMBER: After EVERY period that ends a paragraph, press Enter TWICE to create a blank line.

---
FOR AGENT ANALYSIS (not part of email):
JD Keywords Used: [list key terms from JD incorporated]
Requirements Matched: [map JD requirements to your experience]
Why this fits: [1 sentence on alignment]
"""


# Template for extracting key info from JD
JD_ANALYSIS_PROMPT = """Analyze this job description and extract key information:

JOB DESCRIPTION:
{job_description}

Extract and format:

MUST-HAVE REQUIREMENTS (hard requirements):
- 
- 
-

PREFERRED QUALIFICATIONS (nice-to-haves):
- 
- 

KEY TECHNOLOGIES/TOOLS:
- 
-

TEAM STRUCTURE:
[What team, reporting structure, size]

COMPANY CULTURE KEYWORDS:
[Values, work style mentioned]

SPECIFIC PROJECTS/RESPONSIBILITIES:
- 
-

UNIQUE SELLING POINTS:
[What makes this role attractive]

IDEAL CANDIDATE PROFILE:
[Based on requirements, what person are they looking for?]
"""


# Template for matching user skills to JD
SKILL_MATCH_PROMPT = """Given a job description and user profile, create a matching statement.

JOB DESCRIPTION REQUIREMENTS:
{jd_requirements}

USER PROFILE:
{user_background}

USER SKILLS:
{user_skills}

Create 3 bullet points that:
1. Match each key JD requirement to user's experience
2. Use specific examples from user background
3. Quantify where possible

Format:
"JD asks for [requirement] → I bring [specific experience with metric]"

Example:
"JD requires '4+ years ML experience' → I bring 3 years building production ML models that increased conversion by 20%"
"""


# Follow-up template that references JD
FOLLOWUP_WITH_JD_PROMPT = """Draft a follow-up email referencing the original job description.

ORIGINAL EMAIL:
{original_email}

ORIGINAL JD REQUIREMENTS:
{job_requirements}

DAYS SINCE: {days_elapsed}

FOLLOW-UP STRATEGY:
- Reference specific JD requirement you match strongly
- Add new relevant information (recent project, certification)
- Keep it brief and focused on value

TONE: Polite, professional, assume they're busy

OUTPUT:
Subject: [reference previous + add value]

[Short body referencing JD fit + new info]
"""
