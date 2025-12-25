from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import uuid

Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(Text)
    priority = Column(Integer)
    status = Column(String)
    reminder_time = Column(TIMESTAMP)

    # Timestamps for production readiness
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
