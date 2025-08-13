#!/usr/bin/env python3
"""
Create a new Alembic migration for the Jeen.ai transformation.
This will handle the database schema changes automatically.
"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def create_migration():
    """Create a new migration for the schema changes."""
    print("Creating Alembic migration for Jeen.ai transformation...")
    
    # Use alembic to create a new migration
    os.system('alembic revision --autogenerate -m "transform_to_jeen_ai_representative"')
    
    print("Migration created! You can apply it with: alembic upgrade head")

if __name__ == "__main__":
    create_migration()