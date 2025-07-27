from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.crud import add_or_update_book
from app.crawler.kyobo import crawl_kyobo_books
from app.utils.logger import logger

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/crawl/kyobo")
def crawl_books(db: Session = Depends(get_db)) -> dict:
    logger.info("API 호출됨")
    books = crawl_kyobo_books()
    logger.info(f"크롤링된 책 수: {len(books)}")
    
    new_count = 0
    updated_count = 0
    error_count = 0
    
    for book in books:
        try:
            saved_book, is_new = add_or_update_book(db, book)
            
            if is_new:
                new_count += 1
                logger.info(f"새 책 저장: {book.get('book_name')}")
            else:
                updated_count += 1
                logger.info(f"기존 책 업데이트: {book.get('book_name')}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"처리 실패: {book.get('book_name')} - {str(e)}")
            db.rollback()  # 에러 발생 시 롤백
            continue
            
    return {
        "crawled": len(books),
        "new": new_count,
        "updated": updated_count,
        "errors": error_count
    }