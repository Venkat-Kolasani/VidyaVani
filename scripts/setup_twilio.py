#!/usr/bin/env python3
"""
Twilio Setup and Validation Script for VidyaVani
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_twilio_credentials():
    """Check if Twilio credentials are configured"""
    print("🔍 Checking Twilio Configuration...")
    print("-" * 50)
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    base_url = os.getenv('BASE_URL')
    
    issues = []
    
    if not account_sid or account_sid == 'your_twilio_account_sid_here':
        issues.append("❌ TWILIO_ACCOUNT_SID not configured")
    else:
        print(f"✅ TWILIO_ACCOUNT_SID: {account_sid[:10]}...")
    
    if not auth_token or auth_token == 'your_twilio_auth_token_here':
        issues.append("❌ TWILIO_AUTH_TOKEN not configured")
    else:
        print(f"✅ TWILIO_AUTH_TOKEN: {auth_token[:10]}...")
    
    if not phone_number or phone_number == 'your_us_phone_number_here':
        issues.append("❌ TWILIO_PHONE_NUMBER not configured")
    else:
        print(f"✅ TWILIO_PHONE_NUMBER: {phone_number}")
    
    if not base_url:
        issues.append("❌ BASE_URL not configured")
    else:
        print(f"✅ BASE_URL: {base_url}")
    
    print("-" * 50)
    
    if issues:
        print("\n⚠️  Configuration Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        print("\n📝 Please update your .env file with Twilio credentials")
        return False
    
    print("\n✅ All Twilio credentials configured!")
    return True

def test_twilio_connection():
    """Test Twilio API connection"""
    print("\n🧪 Testing Twilio Connection...")
    print("-" * 50)
    
    try:
        from src.ivr.twilio_client import twilio_client
        
        if twilio_client.validate_connection():
            print("✅ Twilio connection successful!")
            
            # Get account details
            details = twilio_client.get_account_details()
            print(f"\n📊 Account Details:")
            print(f"  Account SID: {details['account_sid']}")
            print(f"  Friendly Name: {details['friendly_name']}")
            print(f"  Status: {details['status']}")
            print(f"  Balance: {details['balance']} {details['currency']}")
            
            return True
        else:
            print("❌ Twilio connection failed")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import twilio_client: {e}")
        print("\n💡 Install Twilio SDK: pip install twilio")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def display_webhook_urls():
    """Display webhook URLs for Twilio configuration"""
    base_url = os.getenv('BASE_URL', 'https://vidyavani.onrender.com')
    
    print("\n🔗 Webhook URLs for Twilio Configuration:")
    print("-" * 50)
    print(f"Incoming Call: {base_url}/webhook/incoming-call")
    print(f"Process Input: {base_url}/webhook/process-input")
    print(f"Process Recording: {base_url}/webhook/process-recording")
    print(f"SMS: {base_url}/webhook/sms")
    print("-" * 50)
    
    print("\n📋 Twilio Console Configuration:")
    print("1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/active")
    print("2. Select your phone number")
    print("3. Under 'Voice Configuration':")
    print(f"   - A CALL COMES IN: Webhook")
    print(f"   - URL: {base_url}/webhook/incoming-call")
    print(f"   - HTTP Method: POST")
    print("4. Click 'Save'")

def main():
    """Main setup function"""
    print("\n" + "=" * 50)
    print("  VidyaVani - Twilio Setup & Validation")
    print("=" * 50 + "\n")
    
    # Step 1: Check credentials
    if not check_twilio_credentials():
        print("\n❌ Setup incomplete. Please configure Twilio credentials first.")
        print("\n📖 See docs/TWILIO_MIGRATION_GUIDE.md for detailed instructions")
        sys.exit(1)
    
    # Step 2: Test connection
    if not test_twilio_connection():
        print("\n❌ Connection test failed. Please check your credentials.")
        sys.exit(1)
    
    # Step 3: Display webhook URLs
    display_webhook_urls()
    
    print("\n" + "=" * 50)
    print("  ✅ Twilio Setup Complete!")
    print("=" * 50)
    print("\n📖 Next steps:")
    print("  1. Configure webhooks in Twilio Console (URLs shown above)")
    print("  2. Test by calling your Twilio number")
    print("  3. Monitor logs: https://console.twilio.com/us1/monitor/logs/calls")
    print("\n")

if __name__ == "__main__":
    main()
