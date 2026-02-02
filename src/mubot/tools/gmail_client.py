"""
Gmail Client Module

This module provides a high-level interface for interacting with Gmail
via the Google API. It handles:
- OAuth authentication
- Sending emails
- Reading inbox and replies
- Applying labels for organization
- Thread management

The GmailClient is designed to be used by the JobSearchAgent and follows
the Model Context Protocol (MCP) pattern for tool integration.
"""

import base64
import pickle
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mubot.config.settings import Settings


# Gmail API scopes required for MuBot functionality
# If modifying these scopes, delete the token.pickle file
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

# Default labels for organizing outreach emails
OUTREACH_LABELS = {
    "sent": "outreach/sent",
    "replied": "outreach/replied",
    "no_response": "outreach/no-response",
    "rejected": "outreach/rejected",
    "converted": "outreach/converted",
    "followup": "outreach/followup",
}


class GmailClient:
    """
    Client for interacting with Gmail API.
    
    This class handles authentication, email operations, and organization
    of job search outreach emails through labels.
    
    Usage:
        client = GmailClient(settings)
        await client.authenticate()
        
        # Send an email
        message_id = await client.send_email(
            to="hiring@company.com",
            subject="Interest in Senior Engineer role",
            body="Hello...",
        )
        
        # Check for replies
        replies = await client.get_replies(message_id)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the Gmail client.
        
        Args:
            settings: Application settings (uses default if not provided)
        """
        self.settings = settings or Settings()
        self.credentials_path = self.settings.gmail_credentials_path
        self.token_path = self.settings.gmail_token_path
        self.sender_email = self.settings.sender_email
        
        self.service = None
        self._labels_cache = {}
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth.
        
        This method:
        1. Checks for existing valid credentials
        2. Refreshes expired tokens if possible
        3. Initiates OAuth flow if needed
        4. Builds the Gmail service
        
        Returns:
            True if authentication successful
        """
        creds = None
        
        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get them
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                creds.refresh(Request())
            else:
                # Need to run OAuth flow
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found at {self.credentials_path}. "
                        "Please download credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    GMAIL_SCOPES,
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for future runs
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)
        
        # Build Gmail service
        self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        
        # Verify we can access the API
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            print(f"✓ Gmail authenticated as: {profile['emailAddress']}")
            return True
        except HttpError as e:
            print(f"✗ Gmail authentication failed: {e}")
            return False
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        thread_id: Optional[str] = None,
        apply_label: bool = True,
    ) -> Optional[str]:
        """
        Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: CC recipients
            bcc: BCC recipients
            thread_id: Thread ID for replies
            apply_label: Whether to apply the outreach/sent label
        
        Returns:
            Message ID if sent successfully, None otherwise
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        from datetime import datetime
        import uuid
        
        # Create MIME message
        message = MIMEMultipart("alternative")
        message["To"] = to
        message["From"] = self.sender_email
        message["Subject"] = subject
        
        # Add headers to avoid spam warnings
        message["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        message["Message-ID"] = f"<{uuid.uuid4()}@gmail.com>"
        message["MIME-Version"] = "1.0"
        message["Content-Type"] = 'multipart/alternative; boundary="boundary"'
        
        # Add Reply-To if different from sender
        message["Reply-To"] = self.sender_email
        
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        
        # Add body (as both plain text and HTML)
        plain_body = self._html_to_text(body)
        message.attach(MIMEText(plain_body, "plain", "utf-8"))
        
        # Wrap HTML body in proper HTML structure if not already
        if not body.strip().startswith("<"):
            html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>{body.replace(chr(10), '<br>')}</p>
</body>
</html>"""
        else:
            html_body = body
        
        message.attach(MIMEText(html_body, "html", "utf-8"))
        
        # Encode for Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        body_payload = {"raw": raw_message}
        if thread_id:
            body_payload["threadId"] = thread_id
        
        try:
            result = self.service.users().messages().send(
                userId="me",
                body=body_payload,
            ).execute()
            
            message_id = result.get("id")
            
            # Apply label if requested
            if apply_label and message_id:
                await self.apply_label(message_id, OUTREACH_LABELS["sent"])
            
            return message_id
            
        except HttpError as e:
            print(f"Error sending email: {e}")
            return None
    
    async def get_message(self, message_id: str) -> Optional[dict]:
        """
        Retrieve a specific message by ID.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Message dict with headers and body
        """
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ).execute()
            
            return self._parse_message(message)
            
        except HttpError as e:
            print(f"Error getting message: {e}")
            return None
    
    async def get_replies(
        self,
        thread_id: str,
        since_message_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Get replies in a thread.
        
        Args:
            thread_id: Thread ID to check
            since_message_id: Only get messages after this one
        
        Returns:
            List of message dicts
        """
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            thread = self.service.users().threads().get(
                userId="me",
                id=thread_id,
            ).execute()
            
            messages = []
            found_since = since_message_id is None
            
            for msg in thread.get("messages", []):
                if msg["id"] == since_message_id:
                    found_since = True
                    continue
                
                if found_since:
                    parsed = self._parse_message(msg)
                    if parsed:
                        messages.append(parsed)
            
            return messages
            
        except HttpError as e:
            print(f"Error getting thread: {e}")
            return []
    
    async def check_for_replies(
        self,
        sent_message_id: str,
        sent_thread_id: str,
    ) -> list[dict]:
        """
        Check if there are new replies to a sent message.
        
        Args:
            sent_message_id: The original message ID
            sent_thread_id: The thread ID
        
        Returns:
            List of new reply messages
        """
        replies = await self.get_replies(sent_thread_id, sent_message_id)
        
        # Filter to only incoming messages (not from us)
        incoming = [
            r for r in replies 
            if r.get("from") != self.sender_email
        ]
        
        return incoming
    
    async def search_messages(
        self,
        query: str,
        max_results: int = 50,
    ) -> list[dict]:
        """
        Search Gmail using a query.
        
        Args:
            query: Gmail search query (same as search box)
            max_results: Maximum results to return
        
        Returns:
            List of message metadata dicts
        """
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results,
            ).execute()
            
            messages = results.get("messages", [])
            
            # Fetch full message details
            full_messages = []
            for msg_meta in messages:
                msg = await self.get_message(msg_meta["id"])
                if msg:
                    full_messages.append(msg)
            
            return full_messages
            
        except HttpError as e:
            print(f"Error searching messages: {e}")
            return []
    
    async def get_or_create_label(self, label_name: str) -> Optional[str]:
        """
        Get or create a Gmail label.
        
        Args:
            label_name: Name of the label
        
        Returns:
            Label ID if successful
        """
        if label_name in self._labels_cache:
            return self._labels_cache[label_name]
        
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            # List existing labels
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            
            # Check if label exists
            for label in labels:
                if label["name"] == label_name:
                    self._labels_cache[label_name] = label["id"]
                    return label["id"]
            
            # Create new label
            label_body = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            }
            
            created = self.service.users().labels().create(
                userId="me",
                body=label_body,
            ).execute()
            
            label_id = created["id"]
            self._labels_cache[label_name] = label_id
            return label_id
            
        except HttpError as e:
            print(f"Error with label {label_name}: {e}")
            return None
    
    async def apply_label(
        self,
        message_id: str,
        label_name: str,
    ) -> bool:
        """
        Apply a label to a message.
        
        Args:
            message_id: Message to label
            label_name: Label to apply
        
        Returns:
            True if successful
        """
        label_id = await self.get_or_create_label(label_name)
        if not label_id:
            return False
        
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [label_id]},
            ).execute()
            return True
            
        except HttpError as e:
            print(f"Error applying label: {e}")
            return False
    
    async def setup_outreach_labels(self) -> bool:
        """
        Create all standard outreach labels.
        
        Returns:
            True if all labels created successfully
        """
        for label_name in OUTREACH_LABELS.values():
            label_id = await self.get_or_create_label(label_name)
            if not label_id:
                return False
        
        print(f"✓ Created {len(OUTREACH_LABELS)} outreach labels")
        return True
    
    # ======================================================================
    # Helper Methods
    # ======================================================================
    
    def _parse_message(self, message: dict) -> Optional[dict]:
        """
        Parse a Gmail API message into a clean dict.
        
        Args:
            message: Raw Gmail API message
        
        Returns:
            Parsed message dict
        """
        try:
            headers = message.get("payload", {}).get("headers", [])
            header_dict = {h["name"].lower(): h["value"] for h in headers}
            
            # Extract body
            body = self._extract_body(message.get("payload", {}))
            
            return {
                "id": message["id"],
                "threadId": message["threadId"],
                "labelIds": message.get("labelIds", []),
                "snippet": message.get("snippet", ""),
                "from": header_dict.get("from", ""),
                "to": header_dict.get("to", ""),
                "subject": header_dict.get("subject", ""),
                "date": header_dict.get("date", ""),
                "body": body,
            }
            
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
    
    def _extract_body(self, payload: dict) -> str:
        """
        Extract the message body from payload.
        
        Handles both single-part and multi-part messages.
        """
        if "body" in payload and payload["body"].get("data"):
            # Single part
            data = payload["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        
        if "parts" in payload:
            # Multi-part: find text or html
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain" and part.get("body", {}).get("data"):
                    data = part["body"]["data"]
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                elif mime_type == "text/html" and part.get("body", {}).get("data"):
                    data = part["body"]["data"]
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    return self._html_to_text(html)
        
        return ""
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion."""
        # Basic HTML tag removal
        import re
        text = re.sub(r"<[^>]+>", "", html)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        return text.strip()
