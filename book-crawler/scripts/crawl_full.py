#!/usr/bin/env python3
"""
교보문고 전체 크롤링 스크립트
베스트셀러 50페이지, 각 책마다 리뷰 5페이지씩 크롤링하여 DB에 저장
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.kyobo import crawl_kyobo_books
from app.db.database import SessionLocal
from app.db.crud import add_or_update_book
from app.utils.logger import logger
import time

def crawl_full_data():
    """50페이지 전체 데이터 크롤링 및 DB 저장"""
    print("=" * 60)
    print("교보문고 전체 크롤링 시작")
    print("베스트셀러: 최대 50페이지")
    print("리뷰: 각 책당 최대 5페이지")
    print("=" * 60)
    
    start_time = time.time()
    
    # 환경변수 설정 확인
    os.environ["MAX_BESTSELLER_PAGES"] = "50"
    os.environ["MAX_REVIEW_PAGES"] = "5"
    
    # 크롤링 실행
    try:
        books = crawl_kyobo_books(limit=None, max_pages=50)
        
        print(f"\n총 {len(books)}권의 책 정보를 크롤링했습니다.")
        
        # DB 세션 생성
        db = SessionLocal()
        
        new_count = 0
        updated_count = 0
        error_count = 0
        
        print("\nDB 저장 시작...")
        
        for idx, book in enumerate(books):
            try:
                saved_book, is_new = add_or_update_book(db, book)
                
                if is_new:
                    new_count += 1
                    logger.info(f"[{idx + 1}/{len(books)}] 새 책 저장: {book.get('book_name')}")
                else:
                    updated_count += 1
                    logger.info(f"[{idx + 1}/{len(books)}] 기존 책 업데이트: {book.get('book_name')}")
                    
                # 진행상황 출력 (10권마다)
                if (idx + 1) % 10 == 0:
                    print(f"진행상황: {idx + 1}/{len(books)}권 처리 완료")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"처리 실패: {book.get('book_name')} - {str(e)}")
                db.rollback()
                continue
        
        db.close()
        
        # 실행 시간 계산
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        print("\n" + "=" * 60)
        print("크롤링 완료!")
        print(f"총 실행 시간: {hours}시간 {minutes}분 {seconds}초")
        print(f"크롤링된 책: {len(books)}권")
        print(f"신규 저장: {new_count}권")
        print(f"업데이트: {updated_count}권")
        print(f"에러: {error_count}건")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 크롤링 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    crawl_full_data()