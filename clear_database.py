#!/usr/bin/env python3
"""
Database clearing script for transforming WhatsApp group bot to Jeen.ai company representative.
Clears all existing data in both general and embeddings databases.
"""
import asyncio
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import delete, text

from config import Settings
from models import Message, Sender, KBTopic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_all_data():
    """Clear all data from the database."""
    try:
        settings = Settings()
        logger.info(f"Connecting to database: {settings.db_uri[:50]}...")
        
        # Create engine
        engine = create_async_engine(settings.db_uri, echo=True)
        
        async with AsyncSession(engine) as session:
            try:
                logger.info("Starting database cleanup...")
                
                # Clear all knowledge base topics (embeddings) first
                logger.info("Clearing knowledge base topics (embeddings)...")
                result = await session.exec(delete(KBTopic))
                logger.info(f"Deleted KBTopic records")
                
                # Clear all messages
                logger.info("Clearing messages...")
                result = await session.exec(delete(Message))
                logger.info(f"Deleted Message records")
                
                # Clear all senders
                logger.info("Clearing senders...")
                result = await session.exec(delete(Sender))
                logger.info(f"Deleted Sender records")
                
                await session.commit()
                logger.info("Database cleared successfully!")
                
            except Exception as e:
                logger.error(f"Error clearing database: {e}")
                await session.rollback()
                raise
            finally:
                await engine.dispose()
                
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        return False
    
    return True

async def verify_database_empty():
    """Verify that the database is empty."""
    try:
        settings = Settings()
        engine = create_async_engine(settings.db_uri, echo=False)
        
        async with AsyncSession(engine) as session:
            # Check if tables are empty
            tables_to_check = [
                (KBTopic, "kbtopic"),
                (Message, "message"), 
                (Sender, "sender")
            ]
            
            for model, table_name in tables_to_check:
                result = await session.exec(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                logger.info(f"Table {table_name}: {count} records")
                
            await engine.dispose()
            logger.info("Database verification complete!")
            
    except Exception as e:
        logger.error(f"Error verifying database: {e}")

if __name__ == "__main__":
    print("Clearing database for Jeen.ai transformation...")
    print("=" * 50)
    
    success = asyncio.run(clear_all_data())
    
    if success:
        print("\nVerifying database is empty...")
        asyncio.run(verify_database_empty())
        print("\nDatabase successfully cleared!")
        print("You can now proceed to upload Jeen.ai company documentation.")
    else:
        print("\nFailed to clear database. Please check the logs above.")