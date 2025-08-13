#!/usr/bin/env python3
"""
Fix database schema by dropping old tables and creating new ones
"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def fix_database():
    """Fix database schema issues."""
    try:
        from config import Settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlmodel import text, SQLModel
        import models
        
        settings = Settings()
        print("Fixing database schema...")
        
        engine = create_async_engine(settings.db_uri, echo=True)
        
        async with AsyncSession(engine) as session:
            # Drop old tables that might conflict
            old_tables = ['group', 'alembic_version']
            
            for table in old_tables:
                try:
                    await session.exec(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    print(f"Dropped table: {table}")
                except Exception as e:
                    print(f"Could not drop {table}: {e}")
            
            await session.commit()
            
        # Create new tables with SQLModel
        print("Creating new tables...")
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            
        print("Database schema fixed!")
        
        # Test the new schema
        async with AsyncSession(engine) as session:
            # Check tables exist
            result = await session.exec(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables after fix: {tables}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

if __name__ == "__main__":
    print("Database Schema Fix")
    print("=" * 30)
    success = asyncio.run(fix_database())
    if success:
        print("Database fixed! You can now upload documentation.")
    else:
        print("Database fix failed. Check the error messages above.")