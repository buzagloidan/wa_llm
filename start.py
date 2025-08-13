#!/usr/bin/env python3
"""
Startup script for Railway deployment
Handles environment validation and graceful startup
"""
import os
import sys
import time
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_environment():
    """Check if all required environment variables are present."""
    required_vars = [
        'DB_URI',
        'WHATSAPP_HOST',
        'GOOGLE_API_KEY', 
        'VOYAGE_API_KEY',
        'LOGFIRE_TOKEN'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("🔧 Please set these in Railway environment variables")
        return False
    
    print("✅ All required environment variables found")
    return True

async def test_imports():
    """Test if we can import the main modules."""
    try:
        print("🔍 Testing imports...")
        
        from config import Settings
        print("✅ Config import successful")
        
        settings = Settings()
        print("✅ Settings initialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main startup function."""
    print("🚀 Starting Jeen.ai Company Representative Bot...")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    imports_ok = asyncio.run(test_imports()) if env_ok else False
    
    # Get port from environment (Railway sets this)
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting server on 0.0.0.0:{port}")
    
    # Try to start the application
    import uvicorn
    
    # If environment/imports failed, start minimal version
    if not env_ok or not imports_ok:
        print("⚠️ Starting in minimal mode due to configuration issues...")
        try:
            uvicorn.run(
                "app.main_minimal:app",
                host="0.0.0.0", 
                port=port,
                log_level="info",
                access_log=True
            )
        except Exception as e:
            print(f"💥 Failed to start minimal app: {e}")
            sys.exit(1)
    else:
        print("✅ All checks passed! Starting full application...")
        try:
            uvicorn.run(
                "app.main:app",
                host="0.0.0.0", 
                port=port,
                log_level="info",
                access_log=True
            )
        except Exception as e:
            print(f"💥 Failed to start full app: {e}")
            print("🔄 Falling back to minimal mode...")
            try:
                uvicorn.run(
                    "app.main_minimal:app",
                    host="0.0.0.0", 
                    port=port,
                    log_level="info"
                )
            except Exception as e2:
                print(f"💥 Failed to start minimal app: {e2}")
                sys.exit(1)

if __name__ == "__main__":
    main()