from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.crud import add_book
from app.crawler.kyobo import crawl_kyobo_books

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/crawl/kyobo")
def crawl_books(db: Session = Depends(get_db)):
    print("[DEBUG] API 호출됨")
    books = crawl_kyobo_books()#limit=
    print(f"[DEBUG] 크롤링된 책 수: {len(books)}")
    for book in books:
        #add_book(db, book)
        print(book)
    return {"inserted": len(books)}