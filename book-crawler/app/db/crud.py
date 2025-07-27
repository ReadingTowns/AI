from app.db.models import Book
from sqlalchemy.orm import Session
from app.utils.logger import logger

def get_book_by_isbn(db: Session, isbn: str) -> Book | None:
    """ISBN으로 책 조회"""
    return db.query(Book).filter(Book.isbn == isbn).first()

def add_book(db: Session, book_data: dict) -> Book:
    """새 책 추가"""
    book = Book(**book_data)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def update_book(db: Session, book: Book, book_data: dict) -> Book:
    """기존 책 정보 업데이트"""
    # 업데이트할 필드만 수정 (book_id, created_at은 제외)
    update_fields = ['book_name', 'book_image', 'author', 'publisher', 
                    'summary', 'keyword', 'review', 'source_field']
    
    for field in update_fields:
        if field in book_data:
            setattr(book, field, book_data[field])
    
    db.commit()
    db.refresh(book)
    return book

def add_or_update_book(db: Session, book_data: dict) -> tuple[Book, bool]:
    """책 추가 또는 업데이트 (ISBN 기준)"""
    isbn = book_data.get('isbn')
    if not isbn:
        raise ValueError("ISBN is required")
    
    existing_book = get_book_by_isbn(db, isbn)
    
    if existing_book:
        # 기존 책 업데이트
        logger.info(f"기존 책 업데이트: {book_data.get('book_name')} (ISBN: {isbn})")
        return update_book(db, existing_book, book_data), False  # (책, 신규여부)
    else:
        # 새 책 추가
        logger.info(f"새 책 추가: {book_data.get('book_name')} (ISBN: {isbn})")
        return add_book(db, book_data), True  # (책, 신규여부)