"""
Slack Reporter - Extract deployment messages and track with Dry.ai

Usage:
    python slack_reporter.py                # Sync + report for last week
    python slack_reporter.py 2025-08-05     # Sync + report for specific week

Prerequisites:
- Set SLACK_BOT_TOKEN environment variable or in .env file
- Set SLACK_CHANNEL_ID environment variable or in .env file (channel to read deployments from)
- Set SLACK_REPORT_CHANNEL_ID environment variable or in .env file (channel to post reports to)
- Install: pip install -r requirements-slack.txt
- Required Slack OAuth scopes: channels:history, channels:read, groups:history, groups:read, users:read, chat:write
"""

import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from drydotai import create_space

load_dotenv()

SPACE_NAME = 'Deployment Tracker'


def get_slack_config():
    """Get Slack client and channel IDs from environment"""
    token = os.getenv('SLACK_BOT_TOKEN')
    channel_id = os.getenv('SLACK_CHANNEL_ID')
    report_channel_id = os.getenv('SLACK_REPORT_CHANNEL_ID')

    if not token or not channel_id:
        print("❌ SLACK_BOT_TOKEN and SLACK_CHANNEL_ID must be set in .env")
        sys.exit(1)

    return WebClient(token=token), channel_id, report_channel_id


def create_dry_space():
    """Create or get existing Dry.ai space and setup deployment type"""
    space = create_space(SPACE_NAME)
    # Setup Deployment type - this is idempotent
    space.add_type("Create a Deployment type with fields: deployment_date (type: date/time), features (type: longText), frontend_commit_id, backend_commit_id")
    print(f"✓ Dry.ai space ready: {SPACE_NAME}")
    return space


def get_most_recent_deployment_datetime(space):
    """Get the most recent deployment datetime from the space"""
    deployments = space.search("all Deployment items")

    if not deployments:
        return None

    # Find most recent deployment by deployment_date
    most_recent = None
    for deployment in deployments:
        # Try different key formats
        dt_str = deployment.get('Deployment Date') or deployment.get('deployment_date')
        if dt_str:
            try:
                # Parse the date format from Dry.ai: "Wed Jul 16 2025 12:21:00 PM"
                dt = datetime.strptime(dt_str, '%a %b %d %Y %I:%M:%S %p')
                if most_recent is None or dt > most_recent:
                    most_recent = dt
            except (ValueError, TypeError):
                continue

    return most_recent


def get_user_name(client, user_id, user_cache):
    """Get username from user ID, with caching"""
    if user_id in user_cache:
        return user_cache[user_id]

    try:
        user_info = client.users_info(user=user_id)
        name = user_info['user'].get('real_name') or user_info['user'].get('name', user_id)
        user_cache[user_id] = name
        return name
    except SlackApiError as e:
        # If lookup fails, cache the user_id itself to avoid repeated failures
        print(f"    ⚠️  Could not resolve user {user_id}: {e.response.get('error', 'unknown error')}")
        user_cache[user_id] = user_id
        return user_id


def resolve_user_mentions(text, client, user_cache):
    """Replace user ID mentions with actual names"""
    def replace_mention(match):
        user_id = match.group(1)
        return f"@{get_user_name(client, user_id, user_cache)}"

    return re.sub(r'<@([A-Z0-9]+)>', replace_mention, text)


def fetch_messages(client, channel_id, since_datetime):
    """Fetch messages from Slack channel since given datetime"""
    try:
        print(f"Fetching messages since {since_datetime.strftime('%Y-%m-%d %H:%M')}...")

        messages = []
        cursor = None

        while True:
            response = client.conversations_history(
                channel=channel_id,
                oldest=str(since_datetime.timestamp()),
                cursor=cursor,
                limit=200
            )
            messages.extend(response['messages'])
            cursor = response.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break

        messages.sort(key=lambda m: float(m['ts']))
        print(f"Found {len(messages)} message(s)\n")
        return messages

    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        sys.exit(1)


def process_messages(space, client, messages):
    """Process messages with Dry.ai to extract deployment information"""
    if not messages:
        return 0

    print(f"🤖 Processing {len(messages)} message(s) with Dry.ai...")
    print()

    total_deployments = 0
    user_cache = {}

    # Process each message individually
    for i, msg in enumerate(messages, 1):
        timestamp = datetime.fromtimestamp(float(msg['ts'])).strftime('%Y-%m-%d %H:%M:%S')
        user_id = msg.get('user', 'Unknown')
        text = msg.get('text', '')

        # Resolve user mentions in the message
        text_resolved = resolve_user_mentions(text, client, user_cache)

        # Get the user name who posted
        user_name = get_user_name(client, user_id, user_cache) if user_id != 'Unknown' else 'Unknown'

        print(f"[{i}/{len(messages)}] {timestamp}")
        print(f"  User: {user_name}")

        # Process with Dry.ai
        result = space.prompt(f"""
If this message describes a deployment with details about what was deployed, create a Deployment item with:
- deployment_date: {timestamp}
- features: description of what was deployed (longText format)
- frontend_commit_id: if mentioned
- backend_commit_id: if mentioned

IGNORE messages that are:
- "Known issue" announcements
- Simple deployment announcements with only environment name (e.g. "deployProd") but no feature details

Message: {text_resolved}
""")

        deployments_added = len(result)
        total_deployments += deployments_added

        if deployments_added > 0:
            print(f"  ✅ Added {deployments_added} deployment(s)")
        else:
            print(f"  ⏭️  Skipped")
        print()

    return total_deployments


def post_to_slack(client, report_channel_id, report):
    """Post report to Slack channel"""
    if not report_channel_id:
        return

    try:
        client.chat_postMessage(channel=report_channel_id, text=report)
        print("✅ Report posted to Slack")
    except SlackApiError as e:
        print(f"❌ Failed to post to Slack: {e.response['error']}")


def generate_report(space, start_date, end_date):
    """Generate text report for deployments in the given date range"""
    week_display = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

    return space.report(f"""
Generate a weekly product improvement report for {week_display}.

Include all deployments from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}.

Format as plain text with:
- Executive summary of product improvements
- Features and improvements grouped by product area or category (not by date)
- Focus on user-facing features and product capabilities, not technical implementation details
- Do NOT include commit hashes, commit IDs, or other technical identifiers
- Use bullet points

Title: Product Improvement Report - {week_display}
""")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Slack Deployment Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('start_date', nargs='?', help='Week start date (YYYY-MM-DD), defaults to last Monday')

    args = parser.parse_args()

    print("📊 Slack Deployment Tracker")
    print()

    # Setup Dry.ai space
    space = create_dry_space()
    print()

    # Get most recent deployment
    most_recent = get_most_recent_deployment_datetime(space)

    if most_recent:
        print(f"📍 Most recent deployment: {most_recent.strftime('%Y-%m-%d %H:%M:%S')}")
        # Add 1 minute to avoid re-processing messages from the same minute
        since_datetime = most_recent + timedelta(minutes=1)
    else:
        print("📍 No existing deployments found - fetching last 90 days")
        since_datetime = datetime.now() - timedelta(days=90)

    print()

    # Setup Slack
    client, channel_id, report_channel_id = get_slack_config()

    # Fetch messages
    messages = fetch_messages(client, channel_id, since_datetime)

    if messages:
        # Process with Dry.ai
        process_messages(space, client, messages)
    else:
        print("✓ No new messages found")

    # Always generate report
    # Parse start date or default to last Monday
    if args.start_date:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']:
            try:
                start_date = datetime.strptime(args.start_date, fmt)
                break
            except ValueError:
                continue
        else:
            print(f"❌ Invalid date format: {args.start_date}")
            print("📝 Supported formats: YYYY-MM-DD, MM/DD/YYYY, M/D/YY")
            sys.exit(1)
    else:
        today = datetime.now()
        days_since_monday = today.weekday()
        start_date = (today - timedelta(days=days_since_monday + 7)).replace(hour=0, minute=0, second=0, microsecond=0)

    end_date = start_date + timedelta(days=7)

    report = generate_report(space, start_date, end_date)

    if report:
        print(report)
        post_to_slack(client, report_channel_id, report)


if __name__ == '__main__':
    main()