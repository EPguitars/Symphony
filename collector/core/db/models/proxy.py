from sqlalchemy import Column, Integer, String, Boolean
from ..base import Base

class Proxy(Base):
    __tablename__ = 'proxies'
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True, index=True)
    proxy = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
