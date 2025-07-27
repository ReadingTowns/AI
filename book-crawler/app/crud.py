from app.models import Book
from sqlalchemy.orm import Session

def add_book(db: Session, book_data: dict):
    book = Book(**book_data)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book