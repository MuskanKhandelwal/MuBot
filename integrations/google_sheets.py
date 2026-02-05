"""
Google Sheets Integration for MuBot

Reads job applications from a Google Sheet and manages outreach.

Expected Sheet Structure:
| Company | Role | Recipient Name | Email | Job Description | Status | Last Contact | Notes |
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsIntegration:
    """
    Integration with Google Sheets for job application management.
    
    Usage:
        sheets = GoogleSheetsIntegration(
            credentials_path="credentials/sheets_credentials.json",
            spreadsheet_name="Job Applications"
        )
        
        # Get pending jobs
        jobs = await sheets.get_pending_jobs()
        
        # Process each job
        for job in jobs:
            await process_job(job)
            
        # Update status
        await sheets.update_job_status(row_number, "Sent", datetime.now())
    """
    
    # Scopes needed for Google Sheets
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    
    def __init__(
        self,
        credentials_path: str = "./credentials/sheets_credentials.json",
        spreadsheet_name: str = "Job Applications",
        worksheet_name: str = "Sheet1"
    ):
        self.credentials_path = credentials_path
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = worksheet_name
        self.client = None
        self.sheet = None
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets API."""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
            
            # Open spreadsheet
            spreadsheet = self.client.open(self.spreadsheet_name)
            self.sheet = spreadsheet.worksheet(self.worksheet_name)
            
            print(f"✅ Connected to Google Sheet: {self.spreadsheet_name}")
            
        except FileNotFoundError:
            print(f"❌ Credentials file not found: {self.credentials_path}")
            print("   Please download from Google Cloud Console")
            raise
        except gspread.SpreadsheetNotFound:
            print(f"❌ Spreadsheet not found: {self.spreadsheet_name}")
            print("   Make sure the sheet exists and is shared with the service account")
            raise
    
    async def get_pending_jobs(self, limit: int = 10) -> list[dict]:
        """
        Get jobs with status "Pending" or empty.
        
        Returns:
            List of job dictionaries with row numbers
        """
        if not self.sheet:
            return []
        
        # Get all records with cleaned headers
        raw_records = self.sheet.get_all_records()
        
        # Clean up record keys (strip whitespace from headers)
        records = []
        for raw_record in raw_records:
            cleaned_record = {k.strip(): v for k, v in raw_record.items()}
            records.append(cleaned_record)
        
        pending_jobs = []
        for i, record in enumerate(records, start=2):  # start=2 because row 1 is headers
            status = str(record.get("Status", "")).strip().lower()
            
            # Include if status is Pending, blank, or not set
            if status in ["pending", "", "not started", "to do"]:
                job = {
                    "row_number": i,
                    "company": record.get("Company", ""),
                    "role": record.get("Role", ""),
                    "recipient_name": record.get("Recipient Name", ""),
                    "email": record.get("Email", ""),
                    "job_description": record.get("Job Description", ""),
                    "status": record.get("Status", "Pending"),
                    "last_contact": record.get("Last Contact", ""),
                    "notes": record.get("Notes", ""),
                }
                pending_jobs.append(job)
                
                if len(pending_jobs) >= limit:
                    break
        
        return pending_jobs
    
    async def update_job_status(
        self,
        row_number: int,
        status: str,
        last_contact: Optional[datetime] = None
    ):
        """
        Update the status and last contact date for a job.
        
        Args:
            row_number: The row number in the sheet
            status: New status (e.g., "Sent", "Replied", "No Response")
            last_contact: Timestamp of last contact
        """
        if not self.sheet:
            return False
        
        try:
            # Get headers to find correct column indices
            headers = [h.strip() for h in self.sheet.row_values(1)]
            
            # Find column indices (1-based for gspread)
            try:
                status_col_idx = headers.index("Status") + 1
                last_contact_col_idx = headers.index("Last Contact") + 1
            except ValueError:
                # Fallback to default positions
                status_col_idx = 6  # Column F
                last_contact_col_idx = 7  # Column G
            
            # Convert to A1 notation
            def col_idx_to_letter(idx):
                """Convert 1-based column index to letter."""
                result = ""
                while idx > 0:
                    idx, remainder = divmod(idx - 1, 26)
                    result = chr(65 + remainder) + result
                return result
            
            status_col = col_idx_to_letter(status_col_idx)
            last_contact_col = col_idx_to_letter(last_contact_col_idx)
            
            # Update status
            self.sheet.update_cell(row_number, status_col_idx, status)
            
            # Update last contact
            if last_contact:
                date_str = last_contact.strftime("%Y-%m-%d %H:%M")
                self.sheet.update_cell(row_number, last_contact_col_idx, date_str)
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating row {row_number}: {e}")
            return False
    
    async def update_notes(self, row_number: int, notes: str):
        """Add notes to a job entry."""
        if not self.sheet:
            return False
        
        try:
            # Notes is column I (9)
            self.sheet.update_acell(f"I{row_number}", notes)
            return True
        except Exception as e:
            print(f"❌ Error updating notes for row {row_number}: {e}")
            return False
    
    async def add_job(self, job_data: dict) -> bool:
        """
        Add a new job to the sheet.
        
        Args:
            job_data: Dict with keys matching column names
        """
        if not self.sheet:
            return False
        
        try:
            row = [
                job_data.get("Company", ""),
                job_data.get("Role", ""),
                job_data.get("Recipient Name", ""),
                job_data.get("Email", ""),
                job_data.get("Job Description", ""),
                job_data.get("Status", "Pending"),
                "",  # Last Contact
                job_data.get("Notes", ""),
            ]
            
            self.sheet.append_row(row)
            return True
            
        except Exception as e:
            print(f"❌ Error adding job: {e}")
            return False
    
    def get_sheet_url(self) -> str:
        """Get the URL of the spreadsheet."""
        if self.sheet:
            return f"https://docs.google.com/spreadsheets/d/{self.sheet.spreadsheet.id}"
        return ""


# Helper function to calculate working days
def add_working_days(start_date: datetime, working_days: int) -> datetime:
    """
    Add working days (excluding weekends) to a date.
    
    Args:
        start_date: Starting date
        working_days: Number of working days to add
    
    Returns:
        Date after adding working days
    """
    current = start_date
    days_added = 0
    
    while days_added < working_days:
        current += timedelta(days=1)
        # Skip weekends (5=Saturday, 6=Sunday)
        if current.weekday() < 5:
            days_added += 1
    
    return current


# Example usage
async def main():
    """Example of using Google Sheets integration."""
    sheets = GoogleSheetsIntegration(
        credentials_path="./credentials/sheets_credentials.json",
        spreadsheet_name="Job Applications"
    )
    
    # Get pending jobs
    pending = await sheets.get_pending_jobs(limit=5)
    print(f"Found {len(pending)} pending jobs")
    
    for job in pending:
        print(f"\n📧 {job['company']} - {job['role']}")
        print(f"   To: {job['recipient_name']} <{job['email']}>")
        print(f"   JD Length: {len(job['job_description'])} chars")
        print(f"   Row: {job['row_number']}")


if __name__ == "__main__":
    asyncio.run(main())
