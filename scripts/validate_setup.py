#!/usr/bin/env python3
"""
Validation script for VidyaVani IVR Learning System setup
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

def check_environment():
    """Check if environment variables are properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded successfully")
    except ImportError:
        print("⚠️  python-dotenv not installed, checking system environment variables")
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False
    
    # Check required variables
    required_vars = [
        'EXOTEL_ACCOUNT_SID',
        'EXOTEL_API_KEY',
        'EXOTEL_API_TOKEN',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'openai',
        'requests',
        'google.cloud.speech',
        'google.cloud.texttospeech',
        'faiss',
        'PyPDF2'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_directories():
    """Check if required directories exist"""
    print("📁 Checking directory structure...")
    
    required_dirs = [
        'src',
        'src/ivr',
        'src/audio', 
        'src/rag',
        'src/content',
        'src/session',
        'src/cache',
        'src/utils',
        'tests',
        'data/ncert',
        'logs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ All required directories exist")
    return True

def test_flask_app():
    """Test if Flask app can start"""
    print("🌐 Testing Flask application...")
    
    try:
        from config import Config
        Config.validate_required_keys()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    try:
        # Import app without running it
        import app
        print("✅ Flask application imports successfully")
        return True
    except Exception as e:
        print(f"❌ Flask application error: {e}")
        return False

def test_exotel_connection():
    """Test Exotel API connection (optional)"""
    print("📞 Testing Exotel connection...")
    
    try:
        # Only test if all Exotel credentials are provided
        import os
        required_exotel_vars = ['EXOTEL_ACCOUNT_SID', 'EXOTEL_API_KEY', 'EXOTEL_API_TOKEN']
        
        if not all(os.getenv(var) for var in required_exotel_vars):
            print("⚠️  Exotel credentials not fully configured - skipping connection test")
            return True
        
        from src.ivr.exotel_client import exotel_client
        if exotel_client.validate_connection():
            print("✅ Exotel connection successful")
            return True
        else:
            print("⚠️  Exotel connection failed - please verify your API credentials")
            print("   You can continue with development and fix credentials later")
            return True  # Make this non-blocking
            
    except Exception as e:
        print(f"⚠️  Exotel connection test failed: {e}")
        print("   This is optional - you can configure Exotel credentials later")
        return True

def main():
    """Run all validation checks"""
    print("🚀 VidyaVani IVR Learning System - Setup Validation")
    print("=" * 50)
    
    checks = [
        check_directories,
        check_dependencies,
        check_environment,
        test_flask_app,
        test_exotel_connection
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All validation checks passed! System is ready to run.")
        print("Start the application with: python app.py")
    else:
        print("❌ Some validation checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()