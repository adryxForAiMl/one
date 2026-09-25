from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(Integer)
    updated_at = Column(Integer)

    scans = relationship("Scan", back_populates="owner")

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_url = Column(String)
    scan_type = Column(String)
    created_at = Column(Integer)
    updated_at = Column(Integer)

    owner = relationship("User", back_populates="scans")
    findings = relationship("Finding", back_populates="scan")

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    title = Column(String)
    severity = Column(String)
    description = Column(Text)
    created_at = Column(Integer)

    scan = relationship("Scan", back_populates="findings")