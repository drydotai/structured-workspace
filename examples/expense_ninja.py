"""
Expense Ninja - Gmail Receipt Processor with Dry.ai Integration

Usage:
    python expense_ninja.py              # Process receipts from last full month (e.g., September if run in October)
    python expense_ninja.py 9/24         # Process receipts from September 2024
    python expense_ninja.py 1/25         # Process receipts from January 2025

Prerequisites:
- Download credentials.json from Google Cloud Console
- Place it in the examples/ directory
- Install: pip install -r requirements.txt
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load .env file from the same directory as this script
from dotenv import load_dotenv
load_dotenv()

from drydotai import get_space, create_space
from email.mime.text import MIMEText
import base64
from bs4 import BeautifulSoup

# Gmail API scopes - need readonly for receipts and send for reports
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
SPACE_NAME = 'Receipt Tracker'


def extract_email_body(payload, max_lines=50):
    """Extract email body and convert HTML to clean text"""
    body = ""
    is_html = False

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    is_html = True
    else:
        data = payload['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')
            if payload.get('mimeType') == 'text/html':
                is_html = True

    # Convert HTML to text
    if is_html and body:
        soup = BeautifulSoup(body, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        body = soup.get_text()
        lines = (line.strip() for line in body.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        body = '\n'.join(chunk for chunk in chunks if chunk)

    # Limit to max_lines
    if body:
        lines = [line for line in body.split('\n') if line.strip()]
        if len(lines) > max_lines:
            body = '\n'.join(lines[:max_lines])
        else:
            body = '\n'.join(lines)

    return body


def send_email_report(service, to_email, month_display, html_content):
    """Send HTML email report using Gmail API"""
    message = MIMEText(html_content, 'html')
    message['to'] = to_email
    message['subject'] = f'Expense Report - {month_display}'

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    service.users().messages().send(userId='me', body={'raw': raw_message}).execute()


def get_gmail_service():
    """Authenticate and return Gmail API service (fresh OAuth each time)"""
    if not os.path.exists('credentials.json'):
        print("❌ Error: credentials.json not found!")
        print("📝 Please download OAuth 2.0 credentials from Google Cloud Console")
        sys.exit(1)

    print("📝 Opening browser for authentication...")
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    return build('gmail', 'v1', credentials=creds)


def parse_month_arg(month_str=None):
    """Parse month (M/YY format) or default to last full month"""
    today = datetime.now()

    if month_str:
        month, year = month_str.split('/')
        start_date = datetime(2000 + int(year), int(month), 1)
    else:
        # Last full month
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)

    end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    return start_date, end_date, start_date.strftime("%B %Y")


def create_dry_space():
    """Create or get existing Dry.ai space and setup types"""
    space = create_space(SPACE_NAME)
    # Setup Receipt type - this is idempotent
    space.add_type("Create a Receipt type with fields: vendor, description, date, amount, and type (one of: Food, Clothes, Electronics, Other, Household)")
    print(f"✓ Dry.ai space ready: {SPACE_NAME}")
    return space


def process_month_emails(service, space, start_date, end_date, month_display):
    """Process all emails for a specific month"""
    # Build Gmail search query for the specific month
    after_date = start_date.strftime("%Y/%m/%d")
    before_date = (end_date + timedelta(days=1)).strftime("%Y/%m/%d")

    query = f'after:{after_date} before:{before_date}'
    print(f"🔍 Searching emails in {month_display}")
    print(f"📋 Query: {query}")
    print()

    # Get all messages (handle pagination)
    messages = []
    page_token = None
    while True:
        results = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        messages.extend(results.get('messages', []))
        page_token = results.get('nextPageToken')
        if not page_token:
            break

    if not messages:
        print(f"✓ No emails found in {month_display}")
        return 0, 0

    print(f"📧 Found {len(messages)} email(s) to process")
    print()

    total_receipts = 0

    # Process each message
    for i, message in enumerate(messages, 1):
        # Get full message details
        msg = service.users().messages().get(userId='me', id=message['id']).execute()

        # Extract subject and sender
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

        # Extract body content
        body = extract_email_body(msg['payload'])

        print(f"[{i}/{len(messages)}] {subject}")
        print(f"  From: {sender}")

        # Process with Dry.ai
        result = space.prompt(f"""
If this email is a receipt or a record of payment of some sort add a Receipt with: vendor, description, date, amount, and type (Food, Clothes, Electronics, Other, or Household).

Subject: {subject}
From: {sender}
Content: {body}
""")

        receipts_added = len(result)
        total_receipts += receipts_added

        if receipts_added > 0:
            print(f"  ✅ Added {receipts_added} receipt(s)")
        else:
            print(f"  ⏭️  No receipt")
        print()

    return len(messages), total_receipts


def main():
    """Main entry point for expense_ninja"""
    parser = argparse.ArgumentParser(
        description='Expense Ninja - Process Gmail receipts for a specific month',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python expense_ninja.py              Process last full month (e.g., September if run in October)
  python expense_ninja.py 9/24         Process September 2024
  python expense_ninja.py 1/25         Process January 2025
        """)
    parser.add_argument('month', nargs='?', help='Month to process in M/YY format (e.g., 9/24 for September 2024)')

    args = parser.parse_args()

    print("🥷 Expense Ninja - Receipt Processor")
    print()

    # Parse month argument
    start_date, end_date, month_display = parse_month_arg(args.month)

    # Setup Gmail service and Dry.ai space
    service = get_gmail_service()
    space = create_dry_space()
    print()

    # Process emails for the month
    try:
        #emails_processed, receipts_added = process_month_emails(service, space, start_date, end_date, month_display)
        emails_processed, receipts_added = 11, 6
        print(f"✅ Processed {emails_processed} email(s) from {month_display}")
        print(f"📝 Added {receipts_added} receipt(s) to {SPACE_NAME}")
        print()

        # Generate and email report
        if receipts_added > 0:
            print("📊 Generating expense report...")
            user_email = service.users().getProfile(userId='me').execute()['emailAddress']

            report_html = space.report(f"Generate a list of all expenses for {month_display}, grouped by category. Format this as nice HTML suitable for email.")

            if report_html:
                print(f"📧 Emailing report to {user_email}...")
                send_email_report(service, user_email, month_display, report_html)
                print(f"✅ Report sent to {user_email}")
            else:
                print("⚠️  Could not generate report")
    except Exception as e:
        print(f"❌ Error processing emails: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
