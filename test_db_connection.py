#!/usr/bin/env python3
"""Test database connection."""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import create_async_engine
from config import Settings

async def test_connection():
    try:
        settings = Settings()
        print(f"Testing connection to: {settings.db_uri[:50]}...")
        
        engine = create_async_engine(settings.db_uri, echo=False)
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("Database connection successful!")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())