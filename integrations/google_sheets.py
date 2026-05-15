"""
Google Sheets Integration for MuBot

Reads job applications from a Google Sheet and manages outreach.

Expected Sheet Structure:
| Company | Role | Recipient Name | Email | Job Description | Status | Last Contact | Follow-up # | Notes |

Status values:
- Pending / To Do / Not Started
- Sent
- FU1 Sent / FU2 Sent / FU3 Sent (follow-up tracking)
- Replied
- No Response
- Rejected
- Send Failed
- Cancelled
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
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
        
        # Track follow-ups
        await sheets.update_followup_count(row_number, 1)  # Follow-up 1 sent
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
        worksheet_name: str = "Sheet1",
        heartbeat_path: str = "./data/heartbeat-state.json"
    ):
        self.credentials_path = credentials_path
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = worksheet_name
        self.heartbeat_path = Path(heartbeat_path)
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
    
    async def get_pending_jobs(self, limit: int = 20) -> list[dict]:
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
            
            # Include if status is Pending, blank, failed, or not set
            if status in ["pending", "", "not started", "to do", "send failed", "failed", "retry"]:
                job = {
                    "row_number": i,
                    "company": record.get("Company", ""),
                    "role": record.get("Role", ""),
                    "recipient_name": record.get("Recipient Name", ""),
                    "email": record.get("Email", ""),
                    "job_description": record.get("Job Description", ""),
                    "status": record.get("Status", "Pending"),
                    "last_contact": record.get("Last Contact", ""),
                    "followup_count": record.get("Follow-up #", ""),
                    "notes": record.get("Notes", ""),
                    "resume": record.get("Resume", "").strip(),  # optional per-job resume path
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
            status: New status (e.g., "Sent", "Replied", "No Response", "FU1 Sent")
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
    
    async def update_followup_count(self, row_number: int, followup_num: int):
        """
        Update the follow-up count in the sheet.
        
        Args:
            row_number: The row number in the sheet
            followup_num: Which follow-up was sent (1, 2, or 3)
        """
        if not self.sheet:
            return False
        
        try:
            headers = [h.strip() for h in self.sheet.row_values(1)]
            
            # Find Follow-up # column
            try:
                fu_col_idx = headers.index("Follow-up #") + 1
            except ValueError:
                # Try alternative names
                for alt in ["Followup #", "Follow-up Count", "FU Count"]:
                    try:
                        fu_col_idx = headers.index(alt) + 1
                        break
                    except ValueError:
                        continue
                else:
                    print("⚠️  'Follow-up #' column not found in sheet")
                    return False
            
            self.sheet.update_cell(row_number, fu_col_idx, followup_num)
            return True
            
        except Exception as e:
            print(f"❌ Error updating follow-up count: {e}")
            return False
    
    async def update_notes(self, row_number: int, notes: str):
        """Add notes to a job entry."""
        if not self.sheet:
            return False
        
        try:
            headers = [h.strip() for h in self.sheet.row_values(1)]
            
            try:
                notes_col_idx = headers.index("Notes") + 1
            except ValueError:
                notes_col_idx = 9  # Default to column I
            
            self.sheet.update_cell(row_number, notes_col_idx, notes)
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
                "",  # Follow-up #
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
    
    # ======================================================================
    # Follow-up Sync Methods
    # ======================================================================
    
    def load_heartbeat_state(self) -> dict:
        """Load heartbeat state from JSON file."""
        if not self.heartbeat_path.exists():
            return {"scheduled_followups": []}
        
        with open(self.heartbeat_path) as f:
            return json.load(f)
    
    def save_heartbeat_state(self, state: dict):
        """Save heartbeat state to JSON file."""
        self.heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.heartbeat_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def sync_followups_to_sheet(self, dry_run: bool = False) -> dict:
        """
        Sync follow-up status from heartbeat-state.json to Google Sheets.
        
        This updates the 'Status' and 'Follow-up #' columns based on
        which follow-ups have been sent.
        
        Args:
            dry_run: If True, show what would be updated without making changes
            
        Returns:
            Dict with sync statistics
        """
        if not self.sheet:
            return {"error": "Not connected to sheet"}
        
        print("🔄 Syncing follow-ups to Google Sheets...")
        
        # Load heartbeat state
        state = self.load_heartbeat_state()
        followups = state.get("scheduled_followups", [])
        
        # Group by company and get latest follow-up status
        company_status = {}
        for fu in followups:
            company = fu.get("company", "Unknown").strip()
            followup_name = fu.get("followup_name", "")
            is_sent = fu.get("sent", False)
            
            if company not in company_status:
                company_status[company] = {"sent": [], "pending": []}
            
            if is_sent:
                company_status[company]["sent"].append(followup_name)
            else:
                company_status[company]["pending"].append(followup_name)
        
        # Get all sheet records
        raw_records = self.sheet.get_all_records()
        records = []
        for raw_record in raw_records:
            cleaned_record = {k.strip(): v for k, v in raw_record.items()}
            records.append(cleaned_record)
        
        stats = {
            "total_rows": len(records),
            "updated": 0,
            "skipped": 0,
            "not_found": 0,
            "errors": []
        }
        
        print(f"   Found {len(records)} rows in sheet, {len(company_status)} companies with follow-ups")
        
        # Update each row
        for i, record in enumerate(records, start=2):
            company = str(record.get("Company", "")).strip()
            current_status = str(record.get("Status", "")).strip()
            
            if not company or company not in company_status:
                stats["skipped"] += 1
                continue
            
            fu_data = company_status[company]
            sent_fus = fu_data["sent"]
            pending_fus = fu_data["pending"]
            
            # Determine new status
            new_status = current_status
            followup_count = 0
            
            if "Follow-up 3" in sent_fus:
                new_status = "FU3 Sent"
                followup_count = 3
            elif "Follow-up 2" in sent_fus:
                new_status = "FU2 Sent"
                followup_count = 2
            elif "Follow-up 1" in sent_fus:
                new_status = "FU1 Sent"
                followup_count = 1
            elif sent_fus and current_status in ["Pending", "", "Not Started", "To Do"]:
                # Initial email sent but not tracked in Status
                new_status = "Sent"
            
            # Only update if status changed
            if new_status != current_status or followup_count > 0:
                if dry_run:
                    print(f"   [DRY RUN] Row {i} ({company}): {current_status} → {new_status} (FU: {followup_count})")
                else:
                    try:
                        # Update status
                        await self.update_job_status(i, new_status)
                        
                        # Update follow-up count
                        if followup_count > 0:
                            await self.update_followup_count(i, followup_count)
                        
                        print(f"   ✅ Updated {company}: {new_status}")
                        stats["updated"] += 1
                    except Exception as e:
                        print(f"   ❌ Error updating {company}: {e}")
                        stats["errors"].append(f"{company}: {e}")
            else:
                stats["skipped"] += 1
        
        # Report companies in heartbeat but not in sheet
        sheet_companies = {str(r.get("Company", "")).strip() for r in records}
        for company in company_status:
            if company not in sheet_companies:
                stats["not_found"] += 1
                print(f"   ⚠️  Company in heartbeat but not in sheet: {company}")
        
        print(f"\n📊 Sync Complete:")
        print(f"   Total rows: {stats['total_rows']}")
        print(f"   Updated: {stats['updated']}")
        print(f"   Skipped (no change): {stats['skipped']}")
        print(f"   Not found in sheet: {stats['not_found']}")
        if stats["errors"]:
            print(f"   Errors: {len(stats['errors'])}")
        
        return stats
    
    async def get_followup_summary(self) -> dict:
        """
        Get a summary of follow-up status from both heartbeat and sheet.
        
        Returns:
            Dict with summary statistics
        """
        state = self.load_heartbeat_state()
        followups = state.get("scheduled_followups", [])
        
        unsent = [f for f in followups if not f.get('sent', False)]
        sent = [f for f in followups if f.get('sent', False)]
        
        # Group by follow-up number
        fu_counts = {"Follow-up 1": {"sent": 0, "pending": 0},
                     "Follow-up 2": {"sent": 0, "pending": 0},
                     "Follow-up 3": {"sent": 0, "pending": 0}}
        
        for f in followups:
            name = f.get('followup_name', "")
            if name in fu_counts:
                if f.get('sent', False):
                    fu_counts[name]["sent"] += 1
                else:
                    fu_counts[name]["pending"] += 1
        
        return {
            "total": len(followups),
            "sent": len(sent),
            "pending": len(unsent),
            "by_type": fu_counts
        }


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
    
    # Sync follow-ups
    print("\n" + "="*60)
    await sheets.sync_followups_to_sheet(dry_run=True)


if __name__ == "__main__":
    asyncio.run(main())
