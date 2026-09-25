from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Scan(Base):
    __tablename__ = 'scans'

    id = Column(Integer, primary_key=True, index=True)
    api_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    findings = Column(JSON, nullable=True)
    status = Column(String, default='pending')  # e.g., 'pending', 'completed', 'failed'

    def __repr__(self):
        return f"<Scan(id={self.id}, api_url={self.api_url}, status={self.status}, created_at={self.created_at})>"