from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Finding(Base):
    __tablename__ = 'findings'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(String)
    severity = Column(String)
    confidence = Column(Integer)
    confidence_label = Column(String)
    category = Column(String)
    cwe = Column(String)
    cwe_title = Column(String)
    owasp = Column(String)
    endpoint = Column(String)
    method = Column(String)
    attacker = Column(String)
    resource_owner = Column(String)
    object_id = Column(String)
    status_code = Column(Integer)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    impact = Column(Text)
    remediation = Column(Text)
    description = Column(Text)
    security_reasoning = Column(Text)  # Consider using a JSON type if supported

    def __repr__(self):
        return f"<Finding(id={self.id}, title={self.title}, severity={self.severity})>"