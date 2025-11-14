"""
Stock Picker - Automated stock monitoring and daily reporting

This example demonstrates how to set up automated rules in Dry.ai that:
1. Monitor top performing stocks hourly during market hours
2. Send a daily summary report when markets close

Usage:
    python stock_picker.py

The rules will run automatically on the Dry.ai platform - no need to keep the script running!
"""

from drydotai import create_space, set_verbose_logging


def main():
    print("📈 Stock Picker - Automated Stock Monitoring")
    print("=" * 50)

    # Enable verbose logging to see API call confirmations
    set_verbose_logging(True)

    # 1. Create the Stock Picker workspace
    print("\n1. Creating Stock Picker workspace")
    space = create_space("Stock Picker")
    print(f"✅ Created workspace: {space.name}")
    print(f"   Workspace ID: {space.id}")
    print(f"   View at: {space.url}")

    # 2. Define the Stock type
    print("\n2. Defining Stock type")
    stock_type = space.add_type("""
        Create a Stock type with fields:
        - ticker (text): Stock ticker symbol
        - company_name (text): Full company name
        - price (number): Current stock price
        - change_percent (number): Percentage change
        - timestamp (datetime): When the stock was picked
        - volume (number): Trading volume
        - market_cap (text): Market capitalization
    """)
    print("✅ Created Stock type definition")

    # 3. Create hourly stock picking rule
    print("\n3. Creating hourly stock picking rule")
    hourly_rule = space.add_item("""
        Create a Rule named "Hourly Top Stock Picker" that runs every hour.

        When it runs, it should:
        Condition: Check if the stock market is currently open
        Action: Identify one of the top performing stocks from the past hour and create a new stock item        
    """)
    print(f"✅ Created rule: {hourly_rule.name}")
    print(f"   This rule will fire every hour during market hours")

    # 4. Create end-of-day report rule
    print("\n4. Creating end-of-day report rule")
    daily_report_rule = space.add_item("""
        Create a Rule named "Daily Stock Report" that runs at 4:30 PM ET.

        When it runs, it should:
            Condition: Check if the stock market was open today
            Action: Review and summarize the picked stocks for the day and send the report to J.R.        
    """)
    print(f"✅ Created rule: {daily_report_rule.name}")
    print(f"   This rule will send daily reports at market close")



if __name__ == "__main__":
    main()