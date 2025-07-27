from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base

class Book(Base):
    __tablename__ = "book"
    
    book_id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String(200))
    book_detail_url = Column(String)
    book_image = Column(String(300))
    author = Column(String(100))
    publisher = Column(String(100))
    summary = Column(Text)
    isbn = Column(String(20), unique=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())