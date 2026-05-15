#!/usr/bin/env python3
"""Diagnose Google Sheets connectivity issues."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_credentials():
    """Check if credentials file is valid."""
    creds_path = Path("./credentials/sheets_credentials.json")
    
    print("=" * 60)
    print("🔍 Checking Google Sheets Credentials")
    print("=" * 60)
    
    if not creds_path.exists():
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    try:
        with open(creds_path) as f:
            creds = json.load(f)
        
        print(f"✅ Credentials file exists")
        
        # Check for service account format
        if "type" in creds:
            print(f"   Type: {creds.get('type')}")
        if "client_email" in creds:
            client_email = creds.get('client_email')
            print(f"   Service Account: {client_email}")
            print(f"\n📋 IMPORTANT: Share your spreadsheet with:")
            print(f"   {client_email}")
        if "project_id" in creds:
            print(f"   Project ID: {creds.get('project_id')}")
            
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False


def test_connection():
    """Test connection to Google Sheets."""
    print("\n" + "=" * 60)
    print("🔍 Testing Google Sheets Connection")
    print("=" * 60)
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        
        credentials = Credentials.from_service_account_file(
            "./credentials/sheets_credentials.json",
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        print("✅ Successfully authenticated with Google")
        
        # Try to list spreadsheets
        print("\n📊 Trying to list your spreadsheets...")
        try:
            spreadsheets = client.list_spreadsheet_files()
            print(f"✅ Found {len(spreadsheets)} spreadsheets:")
            for i, sheet in enumerate(spreadsheets[:10], 1):  # Show first 10
                print(f"   {i}. {sheet['name']}")
            
            if len(spreadsheets) > 10:
                print(f"   ... and {len(spreadsheets) - 10} more")
                
        except Exception as e:
            print(f"❌ Error listing spreadsheets: {e}")
        
        # Try to open specific spreadsheet
        spreadsheet_name = "Job Applications"
        print(f"\n📋 Trying to open '{spreadsheet_name}'...")
        try:
            spreadsheet = client.open(spreadsheet_name)
            print(f"✅ Successfully opened '{spreadsheet_name}'")
            print(f"   URL: {spreadsheet.url}")
            
            # List worksheets
            worksheets = spreadsheet.worksheets()
            print(f"\n📑 Worksheets:")
            for ws in worksheets:
                print(f"   - {ws.title} ({ws.row_count} rows)")
                
        except gspread.SpreadsheetNotFound:
            print(f"❌ Spreadsheet '{spreadsheet_name}' not found!")
            print(f"\n💡 Solutions:")
            print(f"   1. Create a spreadsheet named '{spreadsheet_name}'")
            print(f"   2. Share it with the service account email shown above")
            print(f"   3. Or update the spreadsheet_name in auto_campaign.py")
            return False
        except Exception as e:
            print(f"❌ Error opening spreadsheet: {e}")
            return False
            
        return True
        
    except ImportError:
        print("❌ gspread not installed. Run: pip install gspread")
        return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False


def main():
    print("\n🤖 MuBot Google Sheets Diagnostic Tool\n")
    
    creds_ok = check_credentials()
    if not creds_ok:
        print("\n❌ Please fix credentials issue before continuing")
        return
    
    test_connection()
    
    print("\n" + "=" * 60)
    print("📝 Next Steps")
    print("=" * 60)
    print("""
If the spreadsheet wasn't found:

1. Go to https://sheets.new and create a spreadsheet
2. Name it "Job Applications" (or update the name in auto_campaign.py)
3. Add these column headers in row 1:
   Company | Role | Recipient Name | Email | Job Description | Status | Last Contact | Follow-up # | Notes
4. Share the spreadsheet with the service account email shown above
   (Click Share → Add the service account email as Editor)
5. Add your job applications starting from row 2

If you see a 500 error, try again in a few minutes - Google's API may be temporarily down.
""")


if __name__ == "__main__":
    main()
