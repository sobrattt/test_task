from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    name = Column(String, nullable=True)
    source = Column(String, nullable=True)
    company = Column(String, nullable=True)
    status = Column(String, default='pending')



class LeadEvent(Base):
    __tablename__ = 'lead_event'
    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
