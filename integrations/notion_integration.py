"""
Notion Integration for MuBot

Reads job applications from a Notion database and manages outreach.

Expected Database Structure:
- Company (Title)
- Role (Text)
- Recipient Name (Text)
- Email (Email)
- Job Description (Text)
- Status (Select: Pending, Sent, Replied, No Response, Dead)
- Last Contact (Date)
- Follow-up Count (Number)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from notion_client import Client
from notion_client.errors import APIResponseError


class NotionIntegration:
    """
    Integration with Notion for job application management.
    
    Usage:
        notion = NotionIntegration(
            token="secret_xxx",
            database_id="xxx-xxx-xxx"
        )
        
        # Get pending jobs
        jobs = await notion.get_pending_jobs()
        
        # Process each job
        for job in job:
            await process_job(job)
            
        # Update status
        await notion.update_job_status(page_id, "Sent", datetime.now())
    """
    
    def __init__(
        self,
        token: str,
        database_id: str
    ):
        self.token = token
        self.database_id = database_id
        self.client = Client(auth=token)
        self._validate_connection()
    
    def _validate_connection(self):
        """Validate Notion connection."""
        try:
            # Try to fetch the database
            database = self.client.databases.retrieve(database_id=self.database_id)
            print(f"✅ Connected to Notion database: {database['title'][0]['plain_text']}")
        except APIResponseError as e:
            print(f"❌ Notion API error: {e}")
            raise
    
    async def get_pending_jobs(self, limit: int = 10) -> list[dict]:
        """
        Get jobs with status "Pending".
        
        Returns:
            List of job dictionaries with page IDs
        """
        try:
            # Query database for Pending jobs
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Status",
                    "select": {
                        "equals": "Pending"
                    }
                },
                page_size=limit
            )
            
            jobs = []
            for page in response["results"]:
                props = page["properties"]
                
                job = {
                    "page_id": page["id"],
                    "company": self._get_title(props.get("Company", {})),
                    "role": self._get_text(props.get("Role", {})),
                    "recipient_name": self._get_text(props.get("Recipient Name", {})),
                    "email": self._get_email(props.get("Email", {})),
                    "job_description": self._get_text(props.get("Job Description", {})),
                    "status": self._get_select(props.get("Status", {})),
                    "last_contact": self._get_date(props.get("Last Contact", {})),
                    "follow_up_count": self._get_number(props.get("Follow-up Count", {})),
                    "notes": self._get_text(props.get("Notes", {})),
                }
                jobs.append(job)
            
            return jobs
            
        except APIResponseError as e:
            print(f"❌ Error querying Notion: {e}")
            return []
    
    async def update_job_status(
        self,
        page_id: str,
        status: str,
        last_contact: Optional[datetime] = None
    ):
        """
        Update the status and last contact date for a job.
        
        Args:
            page_id: The Notion page ID
            status: New status
            last_contact: Timestamp of last contact
        """
        try:
            properties = {
                "Status": {"select": {"name": status}}
            }
            
            if last_contact:
                properties["Last Contact"] = {
                    "date": {"start": last_contact.isoformat()}
                }
            
            self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            return True
            
        except APIResponseError as e:
            print(f"❌ Error updating page {page_id}: {e}")
            return False
    
    async def increment_follow_up_count(self, page_id: str) -> int:
        """Increment the follow-up count for a job."""
        try:
            # Get current count
            page = self.client.pages.retrieve(page_id=page_id)
            current = self._get_number(page["properties"].get("Follow-up Count", {}))
            new_count = current + 1
            
            # Update
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Follow-up Count": {"number": new_count}
                }
            )
            
            return new_count
            
        except APIResponseError as e:
            print(f"❌ Error updating follow-up count: {e}")
            return 0
    
    async def add_note(self, page_id: str, note: str):
        """Add a note to the job's notes field."""
        try:
            # Get existing notes
            page = self.client.pages.retrieve(page_id=page_id)
            existing = self._get_text(page["properties"].get("Notes", {}))
            
            # Append new note
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_notes = f"{existing}\n[{timestamp}] {note}".strip()
            
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Notes": {"rich_text": [{"text": {"content": new_notes}}]}
                }
            )
            
            return True
            
        except APIResponseError as e:
            print(f"❌ Error adding note: {e}")
            return False
    
    async def create_job(self, job_data: dict) -> Optional[str]:
        """
        Create a new job entry in Notion.
        
        Returns:
            The new page ID if successful
        """
        try:
            properties = {
                "Company": {"title": [{"text": {"content": job_data.get("Company", "")}}]},
                "Role": {"rich_text": [{"text": {"content": job_data.get("Role", "")}}]},
                "Recipient Name": {"rich_text": [{"text": {"content": job_data.get("Recipient Name", "")}}]},
                "Email": {"email": job_data.get("Email", "")},
                "Job Description": {"rich_text": [{"text": {"content": job_data.get("Job Description", "")}}]},
                "Status": {"select": {"name": "Pending"}},
                "Follow-up Count": {"number": 0},
            }
            
            if job_data.get("Notes"):
                properties["Notes"] = {"rich_text": [{"text": {"content": job_data["Notes"]}}]}
            
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            return page["id"]
            
        except APIResponseError as e:
            print(f"❌ Error creating job: {e}")
            return None
    
    # Helper methods to extract property values
    def _get_title(self, prop: dict) -> str:
        """Extract title property."""
        if "title" in prop and prop["title"]:
            return prop["title"][0]["plain_text"]
        return ""
    
    def _get_text(self, prop: dict) -> str:
        """Extract rich_text property."""
        if "rich_text" in prop and prop["rich_text"]:
            return prop["rich_text"][0]["plain_text"]
        return ""
    
    def _get_email(self, prop: dict) -> str:
        """Extract email property."""
        return prop.get("email", "")
    
    def _get_select(self, prop: dict) -> str:
        """Extract select property."""
        select = prop.get("select")
        return select["name"] if select else ""
    
    def _get_date(self, prop: dict) -> Optional[datetime]:
        """Extract date property."""
        date = prop.get("date")
        if date and date.get("start"):
            return datetime.fromisoformat(date["start"].replace("Z", "+00:00"))
        return None
    
    def _get_number(self, prop: dict) -> int:
        """Extract number property."""
        return prop.get("number", 0) or 0
    
    def get_database_url(self) -> str:
        """Get the URL of the database."""
        return f"https://notion.so/{self.database_id.replace('-', '')}"


# Example usage
async def main():
    """Example of using Notion integration."""
    notion = NotionIntegration(
        token="secret_xxx",  # Replace with your token
        database_id="xxx-xxx-xxx"  # Replace with your database ID
    )
    
    # Get pending jobs
    pending = await notion.get_pending_jobs(limit=5)
    print(f"Found {len(pending)} pending jobs")
    
    for job in pending:
        print(f"\n📧 {job['company']} - {job['role']}")
        print(f"   To: {job['recipient_name']} <{job['email']}>")
        print(f"   Follow-ups sent: {job['follow_up_count']}")


if __name__ == "__main__":
    asyncio.run(main())
