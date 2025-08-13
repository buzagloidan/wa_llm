from datetime import datetime, timezone
from typing import List, Optional, Any

from pgvector.sqlalchemy import Vector
from sqlmodel import Field, SQLModel, Index, Column, DateTime


class KBTopicBase(SQLModel):
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    # Company documentation topic/source
    source: str
    subject: str
    content: str


class KBTopicCreate(KBTopicBase):
    id: str
    embedding: List[float]


class KBTopic(KBTopicBase, table=True):
    id: str = Field(primary_key=True)
    embedding: Any = Field(sa_type=Vector(1024))

    # Add pgvector index
    __table_args__ = (
        Index(
            "kb_topic_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
