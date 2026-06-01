from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum("user", "bot"), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON)
    kg_references = Column(JSON)
    model_name = Column(String(100))
    tokens_used = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
