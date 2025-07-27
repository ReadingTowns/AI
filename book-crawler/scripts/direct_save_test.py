#!/usr/bin/env python3
"""
직접 크롤링 및 저장 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.db.database import SessionLocal
from app.db.crud import add_or_update_book
from app.crawler.kyobo import crawl_kyobo_books

def test_direct_save():
    # 세션 생성
    db = SessionLocal()
    
    try:
        # 5권만 크롤링
        print("크롤링 시작...")
        books = crawl_kyobo_books(limit=7)  # 2권 더 크롤링
        print(f"크롤링 완료: {len(books)}권\n")
        
        # 각 책 저장/업데이트
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for book in books:
            try:
                saved_book, is_new = add_or_update_book(db, book)
                
                if is_new:
                    new_count += 1
                    print(f"새 책 저장: {book.get('book_name')} (ID: {saved_book.book_id})")
                else:
                    updated_count += 1
                    print(f"기존 책 업데이트: {book.get('book_name')} (ID: {saved_book.book_id})")
                    
            except Exception as e:
                error_count += 1
                print(f"처리 실패: {book.get('book_name')} - {str(e)}")
                db.rollback()
                
        print(f"\n처리 결과:")
        print(f"- 새로 저장: {new_count}권")
        print(f"- 업데이트: {updated_count}권")
        print(f"- 실패: {error_count}권")
        print(f"- 총 처리: {new_count + updated_count}/{len(books)}권")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_save()