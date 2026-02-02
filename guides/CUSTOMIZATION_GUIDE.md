# MuBot Customization Guide

## 1. Where to Add Custom Templates

### Option A: Simple Templates (for basic customization)
**File:** `src/mubot/templates/email_templates.py`

Add your custom template at the bottom:

```python
# =============================================================================
# Your Custom Templates
# =============================================================================

DATA_SCIENTIST_JD_TEMPLATE = """Hi {recipient_name},

{personalized_hook}

I came across the {role_title} position at {company_name} and was particularly drawn to {jd_highlight}.

With my background in {relevant_skills}, I've {key_achievement}. 

{jd_specific_value}

{culture_fit}

Would you be open to a brief conversation about how my experience with {jd_requirement_match} aligns with what you're looking for?

{signature}

{unsubscribe}
"""
```

### Option B: Advanced Templates (AI-powered with JD)
**File:** `src/mubot/config/prompts.py`

Modify the `EMAIL_DRAFT_PROMPT` to emphasize JD:

```python
# In EMAIL_DRAFT_PROMPT, find the JOB CONTEXT section and enhance it:

JOB CONTEXT:
Role Title: {job_title}
Job Description Summary: {job_summary}
Key Requirements from JD: {jd_requirements}  # <-- ADD THIS
Preferred Qualifications: {jd_qualifications}  # <-- ADD THIS
Why Interested: {interest_reason}
```

## 2. How to Use Job Description in Emails

### Method 1: Pass JD to draft_email()

```python
from mubot.agent import JobSearchAgent

agent = JobSearchAgent()
await agent.initialize()

# Paste the full JD here
job_description = """
About the Role:
We're looking for a Senior Data Scientist to join our Analytics team...

Requirements:
- 5+ years experience in data science
- Strong Python and SQL skills
- Experience with ML models in production

Preferred:
- Experience with recommendation systems
- Background in streaming/media industry
"""

draft, warnings = await agent.draft_email(
    company_name="Netflix",
    role_title="Senior Data Scientist",
    job_description=job_description,  # <-- Pass JD here
    company_context="Leading streaming platform with strong data culture",
    recipient_name="Hiring Manager",
    recipient_email="hiring@netflix.com"
)
```

### Method 2: Create a JD-Aware Script

See `email_with_jd.py` (created for you) for a complete example.

## 3. Template Variables Available

| Variable | Description | Example |
|----------|-------------|---------|
| `{recipient_name}` | Recipient's name | "Sarah" |
| `{company_name}` | Company name | "Netflix" |
| `{role_title}` | Job title | "Senior Data Scientist" |
| `{personalized_hook}` | Custom opening | "I loved your recent article on..." |
| `{relevant_experience}` | Your background | "5 years building ML models..." |
| `{value_proposition}` | What you bring | "I can help optimize..." |
| `{signature}` | Your signature | "Best, Muskan" |
| `{unsubscribe}` | Unsubscribe text | Auto-generated |
| `{why_interested}` | Why this role | "Passionate about streaming..." |

## 4. Advanced: Create Template Selector

Add to `src/mubot/templates/email_templates.py`:

```python
def get_template_for_role(role_type: str, tone: str = "friendly") -> str:
    """Get template based on role type."""
    templates = {
        "data_scientist": DATA_SCIENTIST_JD_TEMPLATE,
        "software_engineer": COLD_OUTREACH_TEMPLATE,
        "product_manager": PRODUCT_MANAGER_TEMPLATE,
        # Add your custom templates here
    }
    return templates.get(role_type.lower(), COLD_OUTREACH_TEMPLATE)
```

## 5. Quick Reference

### Add a New Template:

1. Open `src/mubot/templates/email_templates.py`
2. Add your template string at the bottom
3. Update `EmailTemplateType` enum if needed
4. Use it in your code

### Use JD in Drafting:

```python
await agent.draft_email(
    company_name="...",
    role_title="...",
    job_description="""PASTE FULL JD HERE""",  # <-- Key parameter
    company_context="...",
)
```

The AI will automatically:
- Extract key requirements from JD
- Match your skills to requirements
- Mention specific technologies
- Show why you're a good fit
