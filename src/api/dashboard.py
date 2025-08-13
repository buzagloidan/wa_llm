#!/usr/bin/env python3
"""
Dashboard API for visualizing company documentation and topics
"""
import logging
from typing import Annotated, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc, func

from models import KBTopic
from .deps import get_db_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard/topics")
async def get_topics(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    source: str = Query(default=None, description="Filter by document source")
) -> Dict[str, Any]:
    """Get all topics/documents for dashboard visualization."""
    try:
        # Build query
        query = select(KBTopic).order_by(desc(KBTopic.start_time))
        
        # Apply source filter if provided
        if source:
            query = query.where(KBTopic.source == source)
            
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await session.exec(query)
        topics = result.all()
        
        # Get total count
        count_query = select(func.count(KBTopic.id))
        if source:
            count_query = count_query.where(KBTopic.source == source)
        total_count = await session.scalar(count_query)
        
        # Get unique sources for filtering
        sources_query = select(KBTopic.source).distinct()
        sources_result = await session.exec(sources_query)
        available_sources = [s for s in sources_result.all() if s]
        
        return {
            "topics": [
                {
                    "id": topic.id,
                    "subject": topic.subject,
                    "content": topic.content[:300] + "..." if len(topic.content) > 300 else topic.content,
                    "source": topic.source,
                    "start_time": topic.start_time.isoformat(),
                    "content_length": len(topic.content)
                }
                for topic in topics
            ],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(topics) < total_count
            },
            "filters": {
                "available_sources": available_sources,
                "current_source": source
            }
        }
        
    except Exception as e:
        logger.error(f"Dashboard topics query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.get("/dashboard/topic/{topic_id}")
async def get_topic_detail(
    topic_id: str,
    session: Annotated[AsyncSession, Depends(get_db_async_session)]
) -> Dict[str, Any]:
    """Get detailed view of a specific topic/document."""
    try:
        topic = await session.get(KBTopic, topic_id)
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
            
        return {
            "id": topic.id,
            "subject": topic.subject,
            "content": topic.content,
            "source": topic.source,
            "start_time": topic.start_time.isoformat(),
            "content_length": len(topic.content),
            "word_count": len(topic.content.split()),
            "has_embedding": topic.embedding is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topic detail query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    session: Annotated[AsyncSession, Depends(get_db_async_session)]
) -> Dict[str, Any]:
    """Get statistics for the dashboard."""
    try:
        # Total topics count
        total_query = select(func.count(KBTopic.id))
        total_topics = await session.scalar(total_query)
        
        # Topics by source
        source_query = select(KBTopic.source, func.count(KBTopic.id)).group_by(KBTopic.source)
        source_result = await session.exec(source_query)
        topics_by_source = {source: count for source, count in source_result.all() if source}
        
        # Average content length
        avg_length_query = select(func.avg(func.length(KBTopic.content)))
        avg_content_length = await session.scalar(avg_length_query) or 0
        
        return {
            "total_topics": total_topics,
            "topics_by_source": topics_by_source,
            "average_content_length": round(avg_content_length, 2),
            "has_embeddings": total_topics > 0,
            "ready_for_queries": total_topics > 0
        }
        
    except Exception as e:
        logger.error(f"Dashboard stats query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")

@router.get("/dashboard/search")
async def search_topics(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=10, le=50)
) -> Dict[str, Any]:
    """Search through topics/documents for dashboard."""
    try:
        # Simple text search (can be enhanced with full-text search later)
        query = select(KBTopic).where(
            (KBTopic.subject.ilike(f"%{q}%")) | 
            (KBTopic.content.ilike(f"%{q}%"))
        ).order_by(desc(KBTopic.start_time)).limit(limit)
        
        result = await session.exec(query)
        topics = result.all()
        
        return {
            "query": q,
            "results": [
                {
                    "id": topic.id,
                    "subject": topic.subject,
                    "content": topic.content[:200] + "..." if len(topic.content) > 200 else topic.content,
                    "source": topic.source,
                    "relevance": "text_match"  # Could be enhanced with similarity scores
                }
                for topic in topics
            ],
            "total_results": len(topics),
            "has_more": len(topics) == limit
        }
        
    except Exception as e:
        logger.error(f"Topic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")