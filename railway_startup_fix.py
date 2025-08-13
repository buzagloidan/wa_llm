#!/usr/bin/env python3
"""
Railway startup fix - handles missing environment variables gracefully
This helps with Railway deployment issues where env vars might not be ready
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_required_env_vars():
    """Check if all required environment variables are set."""
    required_vars = [
        'DB_URI',
        'WHATSAPP_HOST', 
        'GOOGLE_API_KEY',
        'VOYAGE_API_KEY',
        'LOGFIRE_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("🔧 Make sure these are set in Railway environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def test_basic_imports():
    """Test if basic imports work."""
    try:
        from config import Settings
        print("✅ Config import successful")
        
        settings = Settings()
        print("✅ Settings initialization successful")
        print(f"📍 DB URI: {settings.db_uri[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Import/Settings error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Railway Startup Diagnostics")
    print("=" * 40)
    
    env_ok = check_required_env_vars()
    if env_ok:
        import_ok = test_basic_imports()
        
        if import_ok:
            print("\n✅ All checks passed! App should start normally.")
        else:
            print("\n❌ Import issues detected.")
    else:
        print("\n❌ Environment variable issues detected.")
        
    print("\n📝 If issues persist, check Railway logs for more details.")