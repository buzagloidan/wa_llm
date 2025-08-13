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
    if not check_environment():
        print("💥 Environment check failed")
        sys.exit(1)
    
    # Test imports
    if not asyncio.run(test_imports()):
        print("💥 Import test failed") 
        sys.exit(1)
    
    print("✅ All checks passed! Starting main application...")
    print("=" * 50)
    
    # Import and run the main app
    try:
        import uvicorn
        
        # Run the FastAPI app
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0", 
            port=int(os.getenv("PORT", 8080)),
            log_level="info"
        )
        
    except Exception as e:
        print(f"💥 Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()