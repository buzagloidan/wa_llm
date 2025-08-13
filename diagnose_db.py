#!/usr/bin/env python3
"""
Diagnose database issues by testing basic queries
"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_database():
    """Test database connection and schema."""
    try:
        from config import Settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlmodel import text
        
        settings = Settings()
        print(f"Connecting to database...")
        
        engine = create_async_engine(settings.db_uri, echo=False)
        
        async with AsyncSession(engine) as session:
            # Check what tables exist
            result = await session.exec(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"Tables in database: {tables}")
            
            # Check if our expected tables exist
            expected_tables = ['kbtopic', 'message', 'sender']
            missing_tables = [t for t in expected_tables if t not in tables]
            extra_tables = [t for t in tables if t not in expected_tables and not t.startswith('alembic')]
            
            if missing_tables:
                print(f"Missing tables: {missing_tables}")
            
            if extra_tables:
                print(f"Extra tables (old schema): {extra_tables}")
                
            # Check table contents
            for table in ['kbtopic', 'message', 'sender']:
                if table in tables:
                    result = await session.exec(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"Table {table}: {count} records")
                    
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    print("Database Diagnostics")
    print("=" * 30)
    asyncio.run(test_database())