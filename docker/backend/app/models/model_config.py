from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"
    __table_args__ = (UniqueConstraint("provider_id", "model_name", name="uk_provider_model"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_type = Column(Enum("chat", "embedding"), nullable=False)
    system_prompt = Column(Text)
    embedding_dimension = Column(Integer)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    provider = relationship("ModelProvider", lazy="joined")
