from sqlalchemy import Column, Integer, String, Enum, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(Enum("PDF", "DOCX", "TXT", "MD", "XLSX", "XLS", "CSV"), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_path = Column(String(500), nullable=False)
    tag = Column(String(100))
    parse_status = Column(Enum("pending", "parsing", "completed", "failed"), nullable=False, default="pending")
    version = Column(Integer, nullable=False, default=1)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    error_message = Column(Text)
    embedding_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
