#!/usr/bin/env python3
"""
Database administration endpoints for fixing schema issues
"""
import logging
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
import models  # Import models to ensure metadata is populated
from models import KBTopic, Message, Sender  # Explicit imports to ensure all models are registered

from .deps import get_db_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin/database/status")
async def database_status(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> Dict[str, Any]:
    """Check database schema status."""
    try:
        # Check what tables exist
        result = await session.exec(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        # Check table contents
        table_counts = {}
        for table in ['kbtopic', 'message', 'sender']:
            if table in tables:
                result = await session.exec(text(f"SELECT COUNT(*) FROM {table}"))
                table_counts[table] = result.scalar()
            else:
                table_counts[table] = "table_missing"
                
        return {
            "status": "success",
            "tables": tables,
            "table_counts": table_counts,
            "expected_tables": ["kbtopic", "message", "sender"]
        }
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/admin/database/fix-schema")
async def fix_database_schema(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> Dict[str, Any]:
    """Fix database schema by dropping old tables and creating new ones."""
    try:
        # Drop old conflicting tables
        old_tables = ['group', 'alembic_version']
        dropped_tables = []
        
        for table in old_tables:
            try:
                await session.exec(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                dropped_tables.append(table)
                logger.info(f"Dropped table: {table}")
            except Exception as e:
                logger.warning(f"Could not drop {table}: {e}")
        
        await session.commit()
        
        # Create new tables using SQLModel
        from sqlalchemy import create_engine
        from config import Settings
        
        # Get a new engine for schema creation (synchronous)
        settings = Settings()
        sync_db_uri = settings.db_uri.replace('+asyncpg', '').replace('postgresql+asyncpg://', 'postgresql://')
        temp_engine = create_engine(sync_db_uri)
        
        # Create tables synchronously
        SQLModel.metadata.create_all(temp_engine)
        temp_engine.dispose()
            
        logger.info("Database schema fixed successfully")
        
        return {
            "status": "success",
            "message": "Database schema fixed",
            "dropped_tables": dropped_tables,
            "action": "Tables recreated with new schema"
        }
        
    except Exception as e:
        logger.error(f"Database schema fix failed: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Schema fix failed: {str(e)}")

@router.post("/admin/database/clear-data")
async def clear_database_data(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> Dict[str, Any]:
    """Clear all data from database tables."""
    try:
        tables_cleared = []
        
        # Clear data from tables in correct order (respecting foreign keys)
        for table in ['kbtopic', 'message', 'sender']:
            try:
                await session.exec(text(f"TRUNCATE TABLE {table} CASCADE"))
                tables_cleared.append(table)
                logger.info(f"Cleared table: {table}")
            except Exception as e:
                logger.warning(f"Could not clear {table}: {e}")
        
        await session.commit()
        
        return {
            "status": "success", 
            "message": "Database data cleared",
            "tables_cleared": tables_cleared
        }
        
    except Exception as e:
        logger.error(f"Database clear failed: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")