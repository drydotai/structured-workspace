"""
Gmail Email Processor with Dry.ai Integration

Usage:
    python gmail_processor.py setup   # One-time setup: authenticate and create label
    python gmail_processor.py run     # Process unread emails (runs every 5 minutes)

Prerequisites:
- Download credentials.json from Google Cloud Console
- Place it in the examples/ directory
- Install: pip install -r requirements.txt
"""

import sys
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load .env file from the same directory as this script
from dotenv import load_dotenv
load_dotenv()

from drydotai import get_space, create_space

# Gmail API scopes - need modify to add labels
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
PROCESSED_LABEL_NAME = 'DryAI-Processed'
SPACE_NAME = 'Receipt Tracker'


def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ Error: credentials.json not found!")
                print("📝 Please download OAuth 2.0 credentials from Google Cloud Console")
                sys.exit(1)

            print("📝 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def get_or_create_label(service, label_name):
    """Get existing label or create it if it doesn't exist"""
    # List all labels
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    # Check if label already exists
    for label in labels:
        if label['name'] == label_name:
            print(f"✓ Found existing label: {label_name}")
            return label['id']

    # Create new label
    print(f"📝 Creating new label: {label_name}")
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }

    created_label = service.users().labels().create(
        userId='me',
        body=label_object
    ).execute()

    print(f"✅ Created label: {label_name}")
    return created_label['id']


def get_or_create_space():
    """Get or create Coupon Tracker space in Dry.ai"""
    print(f"🔍 Looking for '{SPACE_NAME}' space...")

    space = get_space(SPACE_NAME)
    if space:
        print(f"✓ Found existing space: {SPACE_NAME}")
    else:
        print(f"📝 Creating new space: {SPACE_NAME}")
        space = create_space(SPACE_NAME)
        if not space:
            print("❌ Failed to create space")
            sys.exit(1)
        print(f"✅ Created space: {SPACE_NAME}")

    print(f"🔗 Space URL: {space.url}")
    return space


def setup_space_types(space):
    """Setup Receipt type in the space"""
    print()
    print("🏗️  Setting up space types...")

    # Check if Receipt type exists
    receipt_type = space.get_type('Receipt')
    if not receipt_type:
        print("📝 Creating Receipt type...")
        space.add_type("Create a Receipt type with fields: vendor, description, date, amount, and type (one of: Food, Clothes, Electronics, Other, Household)")
        print("✅ Created Receipt type")
    else:
        print("✓ Receipt type already exists")


def setup():
    """Setup: authenticate Gmail, create label, and setup Dry.ai space"""

    # Gmail setup
    print("🔑 Authenticating with Gmail...")
    service = get_gmail_service()
    print("✅ Authentication successful!")
    print()

    # Create or verify label exists
    label_id = get_or_create_label(service, PROCESSED_LABEL_NAME)
    print(f"📌 Label ID: {label_id}")
    print()

    # Dry.ai setup
    print("🎯 Setting up Dry.ai space...")
    space = get_or_create_space()
    setup_space_types(space)
    print()

    print("✅ Setup complete!")
    print("💡 Run 'python gmail_processor.py run' to process emails")


def extract_email_body(payload, max_lines=20):
    """Extract the email body from the payload and convert to clean text

    Args:
        payload: Email payload from Gmail API
        max_lines: Maximum number of non-empty lines to extract (default: 20)
    """
    import base64
    from bs4 import BeautifulSoup

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
            # Check if it's HTML
            if payload.get('mimeType') == 'text/html':
                is_html = True

    # If HTML, extract text only
    if is_html and body:
        soup = BeautifulSoup(body, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text and clean up whitespace
        body = soup.get_text()
        lines = (line.strip() for line in body.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        body = '\n'.join(chunk for chunk in chunks if chunk)

    # Limit to first N non-empty lines
    if body:
        lines = [line for line in body.split('\n') if line.strip()]
        if len(lines) > max_lines:
            body = '\n'.join(lines[:max_lines]) + f"\n\n[... truncated {len(lines) - max_lines} more lines]"
        else:
            body = '\n'.join(lines)

    return body


def format_email_content(msg):
    """Format email into a nice string with all details"""
    headers = msg['payload']['headers']

    # Extract headers
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
    to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')

    # Extract body
    body = extract_email_body(msg['payload'])

    # Format as string
    formatted = f"""
From: {sender}
To: {to}
Date: {date}
Subject: {subject}
{body}
"""
    return formatted.strip()


def process_emails_once(service, label_id, space):
    """Process unread emails one time"""
    # Search for unread emails that haven't been processed (last 2 weeks only)
    query = f'is:unread -label:{PROCESSED_LABEL_NAME} newer_than:14d'
    print(f"📋 Query: {query}")

    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    print(f"📊 Total messages returned: {len(messages)}")

    if not messages:
        print("✓ No unread emails to process")
        return 0

    print(f"📧 Found {len(messages)} unread email(s) to process")
    print()

    # Process each message
    for i, message in enumerate(messages, 1):
        msg_id = message['id']

        # Get full message details
        msg = service.users().messages().get(userId='me', id=msg_id).execute()

        # Format email content
        email_content = format_email_content(msg)

        # Extract subject and sender for logging
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

        print(f"[{i}/{len(messages)}] Processing email:")
        print(f"  From: {sender}")
        print(f"  Subject: {subject}")
        print(f"  ⚙️  Processing with AI...")

        # Process with Dry.ai
        processing_query = f"""
Assess the following email. If the email is a receipt for goods or services, continue. Otherwise take no further action.

Add a new Receipt item with the vendor name, description of what was purchased, date, amount, and type (one of: Food, Clothes, Electronics, Other, Household).

Email content:
{email_content}
"""

        # Use search to trigger the AI processing
        result = space.search(processing_query)

        print(f"  ✅ Processed by AI - {len(result)} item(s) created/updated")

        # Mark as processed by adding label
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [label_id]}
        ).execute()

        print(f"  ✅ Marked as processed")
        print()

    return len(messages)


def run():
    """Process unread emails in a loop every 5 minutes"""
    print("🚀 Starting email processor (runs every 5 minutes)")
    print("⏹️  Press Ctrl+C to stop")
    print()

    # Get service, label ID, and space once
    service = get_gmail_service()
    label_id = get_or_create_label(service, PROCESSED_LABEL_NAME)
    space = get_or_create_space()
    print()

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] 🔍 Checking for unread emails...")

            processed_count = process_emails_once(service, label_id, space)

            if processed_count > 0:
                print(f"✅ Processed {processed_count} email(s)")

            print(f"⏰ Waiting 5 minutes until next check...")
            print()
            time.sleep(300)  # 5 minutes = 300 seconds

    except KeyboardInterrupt:
        print()
        print("⏹️  Stopping email processor...")
        print("✅ Goodbye!")


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python gmail_processor.py setup   # One-time setup")
        print("  python gmail_processor.py run     # Process emails")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'setup':
        setup()
    elif command == 'run':
        run()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: setup, run")
        sys.exit(1)


if __name__ == '__main__':
    main()
