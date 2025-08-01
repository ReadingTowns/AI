from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class SourceFieldEnum(enum.Enum):
    crawling = "crawling"
    manual = "manual"

class Book(Base):
    __tablename__ = "book"
    
    book_id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String(200))
    book_image = Column(String(300))
    author = Column(String(100))
    publisher = Column(String(100))
    summary = Column(Text)
    isbn = Column(String(20), unique=True, index=True)
    keyword = Column(Text, nullable=True)
    review = Column(Text, nullable=True)
    source_field = Column(Enum(SourceFieldEnum), nullable=False, default=SourceFieldEnum.crawling)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())