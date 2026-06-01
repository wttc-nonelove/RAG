from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.database import Base


class ModelPreset(Base):
    __tablename__ = "model_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    model_config_id = Column(Integer, ForeignKey("model_configs.id", ondelete="CASCADE"), nullable=False)
    scope = Column(Enum("global", "personal"), nullable=False, default="personal")
    description = Column(String(255))
    system_prompt = Column(Text)
    temperature = Column(Numeric(3, 2), default=0.70)
    top_p = Column(Numeric(3, 2), default=0.90)
    max_tokens = Column(Integer, default=2048)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, server_default=func.now())
