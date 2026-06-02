from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(20), nullable=False)  # 'chat' or 'embedding'
    tokens_used = Column(Integer, nullable=False, default=0)
    source_type = Column(String(20), nullable=False)  # 'qa' or 'document'
    source_id = Column(Integer)  # conversation_id or document_id
    source_name = Column(String(255))  # question or filename
    created_at = Column(DateTime, server_default=func.now())
