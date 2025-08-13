#!/usr/bin/env python3
"""
Database administration endpoints for fixing schema issues
"""
import logging
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
import models  # Import models to ensure metadata is populated
from models import KBTopic, Message, Sender  # Explicit imports to ensure all models are registered

from .deps import get_db_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin/test")
async def test_endpoint() -> Dict[str, Any]:
    """Simple test endpoint to verify connectivity."""
    return {"status": "success", "message": "Database admin endpoints are working"}

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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
) -> Dict[str, Any]:
    """Fix database schema by dropping old tables and creating new ones."""
    logger.info("=== DATABASE SCHEMA FIX STARTED ===")
    try:
        # Drop old conflicting tables AND recreate kbtopic with new schema
        old_tables = ['group', 'alembic_version', 'kbtopic']  # Include kbtopic to force recreation
        dropped_tables = []
        
        for table in old_tables:
            try:
                # Start a new transaction for each table
                await session.begin()
                
                # Check if table exists first
                check_result = await session.exec(text(
                    "SELECT table_name FROM information_schema.tables "
                    f"WHERE table_schema = 'public' AND table_name = '{table}'"
                ))
                existing = check_result.fetchall()
                
                if existing:
                    logger.info(f"Table {table} exists, attempting to drop...")
                    
                    # Try to drop the table (quote name for reserved keywords)
                    try:
                        await session.exec(text(f'DROP TABLE "{table}" CASCADE'))
                        await session.commit()
                        
                        # Verify the table was actually dropped
                        verify_result = await session.exec(text(
                            "SELECT table_name FROM information_schema.tables "
                            f"WHERE table_schema = 'public' AND table_name = '{table}'"
                        ))
                        still_remaining = verify_result.fetchall()
                        
                        if not still_remaining:
                            dropped_tables.append(table)
                            logger.info(f"✅ Successfully dropped table: {table}")
                        else:
                            logger.error(f"❌ Table {table} still exists after DROP")
                            
                    except Exception as drop_error:
                        logger.warning(f"Failed to drop {table}: {drop_error}")
                        await session.rollback()
                else:
                    logger.info(f"Table {table} does not exist (already dropped)")
                    await session.commit()
                    
            except Exception as e:
                logger.error(f"Error processing table {table}: {e}")
                try:
                    await session.rollback()
                except:
                    pass
        
        logger.info(f"Drop phase complete. Successfully dropped: {dropped_tables}")
        
        # Create new tables using the app's existing database engine
        logger.info("Using app's existing database engine for schema creation")
        
        # Get the app's database engine
        async_engine = request.app.state.db_engine
        
        # Create tables using the async engine
        try:
            logger.info("Creating schema using async engine...")
            async with async_engine.begin() as conn:
                # Use run_sync to execute the synchronous create_all method
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Schema creation completed successfully")
            
            # Verify the kbtopic table has the correct schema
            verify_result = await session.exec(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'kbtopic' AND table_schema = 'public'
                ORDER BY column_name
            """))
            columns = verify_result.fetchall()
            logger.info(f"kbtopic table columns: {columns}")
            
            # Check if source column exists
            has_source = any(col[0] == 'source' for col in columns)
            if has_source:
                logger.info("✅ kbtopic table has 'source' column - schema is correct")
            else:
                logger.error("❌ kbtopic table missing 'source' column - schema fix failed")
                raise HTTPException(status_code=500, detail="kbtopic table schema is incorrect")
                
        except Exception as schema_error:
            logger.error(f"Schema creation failed: {schema_error}")
            raise HTTPException(status_code=500, detail=f"Schema creation failed: {str(schema_error)}")
            
        logger.info("Database schema fixed successfully")
        
        return {
            "status": "success",
            "message": "Database schema fixed",
            "dropped_tables": dropped_tables,
            "action": "Tables recreated with new schema"
        }
        
    except Exception as e:
        logger.error(f"=== DATABASE SCHEMA FIX FAILED === Error: {e}")
        logger.exception("Full traceback:")
        try:
            await session.rollback()
        except:
            pass
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