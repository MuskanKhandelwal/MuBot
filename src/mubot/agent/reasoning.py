"""
Reasoning Engine Module

The ReasoningEngine handles all LLM interactions and decision-making logic.
It provides a clean interface for:
- Generating email drafts
- Personalizing content
- Classifying responses
- Planning next actions

The engine is designed to be provider-agnostic, supporting OpenAI,
Anthropic, and other LLM providers through a unified interface.
"""

import uuid
from datetime import datetime
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from mubot.config import (
    EMAIL_DRAFT_PROMPT,
    FOLLOWUP_PROMPT,
    RESPONSE_CLASSIFY_PROMPT,
    SYSTEM_PROMPT,
    EMAIL_DRAFT_JD_MATCH_PROMPT,
    EMAIL_DRAFT_HUMAN_PROMPT,
)
from mubot.config.prompts_human import FOLLOWUP_PROMPT_XML
from mubot.config.prompts_jd_enhanced import EMAIL_DRAFT_WITH_JD_PROMPT
from mubot.config.settings import Settings
from mubot.memory.models import (
    EmailTone,
    OutreachEntry,
    OutreachStatus,
    ResponseCategory,
    UserProfile,
)


class ReasoningEngine:
    """
    LLM-powered reasoning and content generation engine.
    
    This class handles all interactions with the language model,
    including prompt construction, API calls, and response parsing.
    
    Usage:
        engine = ReasoningEngine(settings)
        
        draft = await engine.draft_email(
            user_profile=profile,
            company_name="TechCorp",
            role_title="Senior Engineer",
            # ... other params
        )
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the reasoning engine.
        
        Args:
            settings: Application configuration
        """
        self.settings = settings
        self.client = self._initialize_client()
        self.model = settings.llm_model
    
    def _initialize_client(self) -> AsyncOpenAI:
        """Initialize the appropriate LLM client based on settings."""
        if self.settings.llm_provider == "openai":
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            return AsyncOpenAI(api_key=self.settings.openai_api_key)
        
        # TODO: Add support for Anthropic, Kimi, etc.
        raise NotImplementedError(f"Provider {self.settings.llm_provider} not yet supported")
    
    def _build_system_prompt(self, context: dict) -> str:
        """
        Build the system prompt with current context.
        
        Args:
            context: Dictionary of context variables
        
        Returns:
            Formatted system prompt string
        """
        return SYSTEM_PROMPT.format(
            current_date=datetime.utcnow().isoformat(),
            timezone=context.get("timezone", "UTC"),
            today_email_count=context.get("today_email_count", 0),
            max_daily_emails=self.settings.max_daily_emails,
        )
    
    async def _generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            messages: List of message dicts (role, content)
            temperature: Creativity (0-1)
            max_tokens: Maximum response length
        
        Returns:
            Generated text
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content or ""
    
    # ======================================================================
    # Email Drafting
    # ======================================================================
    
    async def draft_email(
        self,
        user_profile: UserProfile,
        company_name: str,
        role_title: str,
        company_context: str,
        job_description: str,
        recipient_name: Optional[str] = None,
        recipient_title: Optional[str] = None,
        connection_type: Optional[str] = None,
        company_history: Optional[str] = None,
    ) -> OutreachEntry:
        """
        Generate a personalized cold email draft.
        
        Args:
            user_profile: User's profile and preferences
            company_name: Target company name
            role_title: Job title
            company_context: Context about the company
            job_description: Job description or summary
            recipient_name: Recipient's name (if known)
            recipient_title: Recipient's title (if known)
            connection_type: How user is connected (if any)
            company_history: Previous contact history
        
        Returns:
            OutreachEntry with generated email
        """
        # Build resume highlights for better context
        resume_highlights = self._build_resume_highlights(user_profile)
        
        # Extract first name for casual sign-offs
        first_name = user_profile.name.split()[0] if user_profile.name else "Muskan"
        
        # Use human-style prompt for more natural emails
        recipient = recipient_name if recipient_name else "Hiring Manager"
        resume_filename = user_profile.resume_path.name if user_profile.resume_path else "resume.pdf"
        prompt = EMAIL_DRAFT_HUMAN_PROMPT.format(
            user_name=user_profile.name,
            user_first_name=first_name,
            user_background=user_profile.summary or "Data Scientist with ML experience",
            user_experience=user_profile.years_experience or "3+ years",
            user_skills=", ".join(user_profile.key_skills) if user_profile.key_skills else "Python, ML",
            user_resume=resume_highlights,
            target_role=role_title,
            target_company=company_name,
            company_context=company_context,
            recipient_name=recipient,
            job_summary=job_description[:600] if job_description else "",
            resume_filename=resume_filename,
        )
        
        # Generate with human-style system prompt
        messages = [
            {"role": "system", "content": "You are a helpful assistant that writes natural, conversational cold emails. Be brief, human, and specific."},
            {"role": "user", "content": prompt},
        ]
        
        # Lower max_tokens to force shorter emails (100 words ≈ 130 tokens)
        response = await self._generate(messages, temperature=0.75, max_tokens=800)
        
        # Parse the response to extract subject and body
        subject, body, personalization = self._parse_email_response(response)
        
        # Create the outreach entry
        entry = OutreachEntry(
            id=str(uuid.uuid4()),
            recipient_email="",  # To be filled when known
            recipient_name=recipient_name,
            recipient_title=recipient_title,
            company_name=company_name,
            role_title=role_title,
            subject=subject,
            body=body,
            personalization_elements=personalization,
            status=OutreachStatus.DRAFT,
            drafted_at=datetime.utcnow(),
            max_followups=self.settings.max_followups,
        )
        
        return entry
    
    async def draft_email_with_jd(
        self,
        user_profile: UserProfile,
        company_name: str,
        role_title: str,
        company_context: str,
        job_description: str,
        recipient_name: Optional[str] = None,
        recipient_title: Optional[str] = None,
        company_history: Optional[str] = None,
    ) -> OutreachEntry:
        """
        Generate a JD-optimized cold email draft using human-style prompts.
        
        Creates shorter, more conversational emails that specifically match
        the user's resume to the job description requirements.
        """
        from datetime import datetime
        import uuid
        from mubot.memory.models import OutreachEntry, OutreachStatus
        
        # Build resume highlights for better matching
        resume_highlights = self._build_resume_highlights(user_profile)
        
        # Extract first name for casual sign-offs
        first_name = user_profile.name if user_profile.name else "Muskan"
        
        # Use human-style JD matching prompt
        recipient = recipient_name if recipient_name else "Hiring Manager"
        resume_filename = user_profile.resume_path.name if user_profile.resume_path else "resume.pdf"
        prompt = EMAIL_DRAFT_JD_MATCH_PROMPT.format(
            user_name=user_profile.name,
            user_first_name=first_name,
            user_linkedin=user_profile.linkedin_url or "",
            user_phone=user_profile.phone or "",
            user_background=user_profile.summary or "Data Scientist with ML experience",
            user_key_skills=", ".join(user_profile.key_skills) if user_profile.key_skills else "Python, ML",
            user_resume_highlights=resume_highlights,
            target_company=company_name,
            target_role=role_title,
            recipient_name=recipient,
            jd_requirements=job_description[:1000] if job_description else "",
            resume_filename=resume_filename,
        )
        
        # Generate with human-style system prompt
        messages = [
            {"role": "system", "content": "You are a helpful assistant that writes natural, conversational cold emails. Be brief, human, and specific."},
            {"role": "user", "content": prompt},
        ]
        
        # Lower max_tokens to force shorter emails (100 words ≈ 130 tokens)
        response = await self._generate(messages, temperature=0.75, max_tokens=1000)
        
        # Parse the response
        subject, body, personalization = self._parse_email_response(response)
        
        # Create entry
        entry = OutreachEntry(
            id=str(uuid.uuid4()),
            recipient_email="",
            recipient_name=recipient_name,
            recipient_title=recipient_title,
            company_name=company_name,
            role_title=role_title,
            subject=subject,
            body=body,
            personalization_elements=personalization,
            status=OutreachStatus.DRAFT,
            drafted_at=datetime.utcnow(),
            max_followups=self.settings.max_followups,
        )
        
        return entry
    
    def _build_resume_highlights(self, user_profile: UserProfile) -> str:
        """Build resume highlights string from user profile for matching."""
        highlights = []
        if user_profile.summary:
            highlights.append(user_profile.summary)
        if user_profile.years_experience:
            highlights.append(f"{user_profile.years_experience} years experience")
        if user_profile.key_skills:
            highlights.append(f"Skills: {', '.join(user_profile.key_skills)}")
        return "; ".join(highlights) if highlights else "Experienced professional"
    
    def _parse_email_response(self, response: str) -> tuple[str, str, list[str]]:
        """
        Parse LLM response to extract email components.
        
        Handles both XML and regular email formats.
        
        Args:
            response: Raw LLM output
        
        Returns:
            Tuple of (subject, body, personalization_elements)
        """
        import re
        
        subject = ""
        body = ""
        personalization = []
        
        # Try XML format first
        # Extract subject from <subject> tags
        subject_match = re.search(r'<subject>(.*?)</subject>', response, re.DOTALL | re.IGNORECASE)
        if subject_match:
            subject = subject_match.group(1).strip()
        
        # Extract body from <email_body>, <email>, or <email_body> tags
        body_match = re.search(r'<email_body>(.*?)</email_body>', response, re.DOTALL | re.IGNORECASE)
        if not body_match:
            body_match = re.search(r'<email>(.*?)</email>', response, re.DOTALL | re.IGNORECASE)
        if body_match:
            body = body_match.group(1).strip()
        
        # If XML parsing succeeded, return results
        if subject and body:
            body = self._fix_paragraph_spacing(body)
            return subject, body, personalization
        
        # Fallback: Parse non-XML format
        lines = response.split("\n")
        body_lines = []
        in_body = False
        in_personalization = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Extract subject
            if line_stripped.lower().startswith("subject:"):
                subject = line_stripped.split(":", 1)[1].strip()
                continue
            
            # Stop at separator (---)
            if line_stripped == "---":
                in_body = False
                in_personalization = False
                continue
            
            # Start of body (after subject)
            if subject and not in_body and not line_stripped.startswith("Personalization"):
                in_body = True
            
            # Personalization section
            if "personalization" in line_stripped.lower() or "why this should work" in line_stripped.lower():
                in_body = False
                in_personalization = True
                continue
            
            # JD Analysis section markers
            if any(marker in line_stripped.lower() for marker in [
                "jd keywords used:", "requirements matched:", "why this fits:", 
                "for agent analysis", "not part of email", "for tracking:",
                "matches made:", "---"
            ]):
                in_body = False
                in_personalization = False
                continue
            
            # Collect body lines
            if in_body and line_stripped:
                body_lines.append(line)
            
            # Collect personalization elements
            if in_personalization and line_stripped.startswith(("-", "1.", "2.", "3.")):
                elem = line_stripped.lstrip("- 1234567890.").strip()
                if elem:
                    personalization.append(elem)
        
        body = "\n".join(body_lines).strip()
        body = self._fix_paragraph_spacing(body)
        
        # Fallback if parsing failed
        if not subject:
            subject = "Interest in opportunities at your company"
        if not body:
            body = response
        
        return subject, body, personalization
    
    def _fix_paragraph_spacing(self, body: str) -> str:
        """
        Ensure proper paragraph spacing in email body.
        
        Adds blank lines between logical paragraphs if missing.
        """
        import re
        
        # Handle greetings that don't end with periods (Hi Name,)
        # Replace comma with period so it gets split properly
        body = re.sub(r'^(Hi\s+\w+),\s*', r'\1. ', body, flags=re.IGNORECASE)
        body = re.sub(r'^(Hello\s+\w+),\s*', r'\1. ', body, flags=re.IGNORECASE)
        body = re.sub(r'^(Dear\s+\w+),\s*', r'\1. ', body, flags=re.IGNORECASE)
        
        # Split into sentences
        # This regex splits at periods followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', body.strip())
        
        # Group sentences into paragraphs
        paragraphs = []
        current_para = []
        
        # Paragraph starters - sentences that typically start new paragraphs
        para_starters = [
            'dear ', 'hi ', 'hello ',
            'saw ', 'came across', 'noticed', 'read about',
            'over the past', 'with over', 'i have ', 'my experience', "i've ",
            'built ', 'created ', 'developed ', 'worked ', 'led ', 'managed ',
            'worth a', 'open to', 'would love', 'could we', 'let me',
            'additionally', 'furthermore', 'moreover', 'in my ', 'at ',
            'thank you', 'thanks', 'best', 'best regards', 'warm regards', 'sincerely',
            '-', '—', 'muskan', '[your name]'
        ]
        
        prev_was_greeting = False
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if this sentence starts a new paragraph
            starts_new_para = False
            sentence_lower = sentence.lower()
            
            for starter in para_starters:
                if sentence_lower.startswith(starter):
                    starts_new_para = True
                    break
            
            # Force new paragraph after greeting (Hi/Hello/Dear Name,)
            if prev_was_greeting and current_para:
                starts_new_para = True
            
            # Track if this sentence is a greeting
            prev_was_greeting = sentence_lower.startswith(('hi ', 'hello ', 'dear ')) and i == 0
            
            if starts_new_para and current_para:
                # Save current paragraph and start new one
                paragraphs.append(' '.join(current_para))
                current_para = [sentence]
            else:
                current_para.append(sentence)
        
        # Don't forget the last paragraph
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        # Clean up each paragraph
        cleaned = []
        for p in paragraphs:
            p = p.strip()
            if p:
                # Ensure paragraph ends with proper punctuation
                if not any(p.endswith(end) for end in ['.', '!', '?']):
                    p += '.'
                cleaned.append(p)
        
        # Join with double newlines
        result = '\n\n'.join(cleaned)
        
        # Restore greeting comma (Hi Name. -> Hi Name,)
        result = re.sub(r'^(Hi\s+\w+)\.', r'\1,', result, flags=re.IGNORECASE)
        result = re.sub(r'^(Hello\s+\w+)\.', r'\1,', result, flags=re.IGNORECASE)
        result = re.sub(r'^(Dear\s+\w+)\.', r'\1,', result, flags=re.IGNORECASE)
        
        # Strip markdown link formatting [text](url) -> url
        result = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\2', result)
        
        return result
    
    # ======================================================================
    # Follow-Up Generation
    # ======================================================================
    
    async def draft_followup(
        self,
        original_entry: OutreachEntry,
        days_elapsed: int,
    ) -> str:
        """
        Generate a polite follow-up email using XML prompt.
        
        Args:
            original_entry: The original outreach entry
            days_elapsed: Days since original was sent
        
        Returns:
            Follow-up email content
        """
        prompt = FOLLOWUP_PROMPT_XML.format(
            original_email=f"Subject: {original_entry.subject}\n\n{original_entry.body}",
            original_date=original_entry.sent_at.isoformat() if original_entry.sent_at else "Unknown",
            days_elapsed=days_elapsed,
            followup_number=original_entry.followup_count + 1,
            max_followups=original_entry.max_followups,
            thread_history="No replies received yet",
        )
        
        messages = [
            {"role": "system", "content": "You are an expert at writing polite, effective follow-up emails."},
            {"role": "user", "content": prompt},
        ]
        
        return await self._generate(messages, temperature=0.6)
    
    # ======================================================================
    # Response Classification
    # ======================================================================
    
    async def classify_response(
        self,
        original_email: OutreachEntry,
        response_body: str,
    ) -> tuple[ResponseCategory, dict]:
        """
        Classify an incoming email response.
        
        Args:
            original_email: The email that was sent
            response_body: The response received
        
        Returns:
            Tuple of (category, extracted_data)
        """
        prompt = RESPONSE_CLASSIFY_PROMPT.format(
            original_email=f"Subject: {original_email.subject}\n\n{original_email.body}",
            response_email=response_body,
        )
        
        messages = [
            {"role": "system", "content": "You are an expert at analyzing email responses."},
            {"role": "user", "content": prompt},
        ]
        
        result = await self._generate(messages, temperature=0.3)
        
        # Parse the classification
        category = self._parse_classification(result)
        
        extracted_data = {
            "raw_classification": result,
            "sentiment": self._extract_sentiment(result),
            "action_items": self._extract_action_items(result),
        }
        
        return category, extracted_data
    
    def _parse_classification(self, text: str) -> ResponseCategory:
        """Parse classification from LLM response."""
        text_lower = text.lower()
        
        if "category: positive" in text_lower:
            return ResponseCategory.POSITIVE
        elif "category: rejection" in text_lower:
            return ResponseCategory.REJECTION
        elif "category: no-response" in text_lower:
            return ResponseCategory.NO_RESPONSE
        elif "category: needs-reply" in text_lower:
            return ResponseCategory.NEEDS_REPLY
        else:
            return ResponseCategory.NEUTRAL
    
    def _extract_sentiment(self, text: str) -> float:
        """Extract sentiment score from classification."""
        # Simple parsing - look for "Sentiment: X.X" pattern
        import re
        match = re.search(r"sentiment:\s*([\d.-]+)", text.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.0
    
    def _extract_action_items(self, text: str) -> list[str]:
        """Extract action items from classification."""
        items = []
        lines = text.split("\n")
        in_action_section = False
        
        for line in lines:
            if "action" in line.lower() and ":" in line:
                in_action_section = True
                item = line.split(":", 1)[1].strip()
                if item and item.lower() not in ["none", "n/a"]:
                    items.append(item)
            elif in_action_section and line.strip().startswith(("-", "•")):
                items.append(line.strip().lstrip("- •").strip())
        
        return items
    
    # ======================================================================
    # Streaming Support
    # ======================================================================
    
    async def stream_draft(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """
        Stream email generation for real-time display.
        
        Args:
            messages: List of message dicts
        
        Yields:
            Text chunks as they're generated
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
