#!/usr/bin/env python3
"""
교보문고 크롤링 + 실시간 DB 저장 스크립트
크롤링과 동시에 DB에 저장하여 중단되어도 진행사항 보존
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.kyobo import create_chrome_driver, get_book_isbn, crawl_book_detail
from app.db.database import SessionLocal
from app.db.crud import add_or_update_book
from app.db.models import Book
from app.utils.logger import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

BASE_URL = "https://store.kyobobook.co.kr/bestseller/online/weekly"
DETAIL_BASE = "https://product.kyobobook.co.kr"

def crawl_and_save():
    """크롤링과 동시에 DB 저장"""
    print("=" * 60)
    print("교보문고 크롤링 + 실시간 저장 시작")
    print("=" * 60)
    
    start_time = time.time()
    
    # 환경변수 설정
    os.environ.setdefault("MAX_BESTSELLER_PAGES", "50")
    os.environ.setdefault("MAX_REVIEW_PAGES", "5")
    max_pages = int(os.getenv("MAX_BESTSELLER_PAGES", "50"))
    
    # DB 세션 생성
    db = SessionLocal()
    
    # 기존 ISBN 목록 가져오기
    existing_isbns = set()
    try:
        existing_books = db.query(Book.isbn).all()
        existing_isbns = {book.isbn for book in existing_books if book.isbn}
        print(f"DB에 이미 {len(existing_isbns)}권의 책이 존재합니다.")
    except Exception as e:
        logger.error(f"DB 조회 실패: {str(e)}")
    
    driver = create_chrome_driver()
    
    new_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    total_processed = 0
    
    try:
        # 1단계: 페이지별로 책 수집 및 즉시 처리
        for page in range(1, max_pages + 1):
            print(f"\n베스트셀러 페이지 {page}/{max_pages} 처리 중...")
            
            # 페이지 로드
            page_url = f"{BASE_URL}?page={page}"
            driver.get(page_url)
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.prod_link"))
                )
            except Exception as e:
                logger.error(f"페이지 {page} 로딩 실패: {str(e)}")
                continue
            
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # 현재 페이지의 책들 처리
            page_books = []
            for a_tag in soup.select("a.prod_link"):
                title = a_tag.text.strip()
                href = a_tag.get("href", "")
                if not href.startswith("http"):
                    href = DETAIL_BASE + href
                
                if title and title != '새창보기 아이콘새창보기':
                    page_books.append({
                        "book_name": title,
                        "book_detail_url": href
                    })
            
            print(f"페이지 {page}에서 {len(page_books)}권 발견")
            
            # 각 책 즉시 처리
            for book_info in page_books:
                total_processed += 1
                
                # 50개마다 브라우저 재시작
                if total_processed > 0 and total_processed % 50 == 0:
                    logger.info("브라우저 재시작 중... (메모리 관리)")
                    driver.quit()
                    time.sleep(2)
                    driver = create_chrome_driver()
                
                # ISBN 체크
                isbn = get_book_isbn(driver, book_info["book_detail_url"])
                
                # ISBN이 없으면 건너뜀
                if not isbn:
                    skipped_count += 1
                    logger.info(f"[{total_processed}] ISBN 없음, 건너뜀: {book_info['book_name']}")
                    continue
                
                # 이미 있는 책인지 확인
                if isbn in existing_isbns:
                    skipped_count += 1
                    logger.info(f"[{total_processed}] DB에 이미 존재, 건너뜀: {book_info['book_name']} (ISBN: {isbn})")
                    continue
                
                # 상세 정보 크롤링
                detail_info = crawl_book_detail(driver, book_info["book_detail_url"])
                
                if detail_info:
                    # 크롤링 성공 시 즉시 DB 저장
                    try:
                        complete_book_info = {
                            "book_name": book_info["book_name"],
                            **detail_info
                        }
                        
                        saved_book, is_new = add_or_update_book(db, complete_book_info)
                        
                        if is_new:
                            new_count += 1
                            if detail_info.get('isbn'):
                                existing_isbns.add(detail_info.get('isbn'))  # 중복 방지를 위해 추가
                            logger.info(f"[{total_processed}] 새 책 저장: {book_info['book_name']}")
                        else:
                            updated_count += 1
                            logger.info(f"[{total_processed}] 기존 책 업데이트: {book_info['book_name']}")
                        
                        # 10권마다 commit
                        if (new_count + updated_count) % 10 == 0:
                            db.commit()
                            print(f"중간 저장 완료 (신규: {new_count}, 업데이트: {updated_count}, 건너뜀: {skipped_count})")
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"DB 저장 실패: {book_info['book_name']} - {str(e)}")
                        db.rollback()
                        
                else:
                    error_count += 1
                    logger.error(f"크롤링 실패: {book_info['book_name']}")
                
                # 진행상황 출력 (20권마다)
                if total_processed % 20 == 0:
                    elapsed = time.time() - start_time
                    print(f"\n진행상황: {total_processed}권 처리")
                    print(f"  - 신규: {new_count}, 업데이트: {updated_count}, 건너뜀: {skipped_count}, 에러: {error_count}")
                    print(f"  - 경과 시간: {int(elapsed//60)}분 {int(elapsed%60)}초")
                
                time.sleep(1)  # 봇 탐지 방지
        
        # 마지막 커밋
        db.commit()
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
        db.commit()  # 중단 시에도 저장
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        db.rollback()
        
    finally:
        driver.quit()
        db.close()
        
        # 최종 결과
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        print("\n" + "=" * 60)
        print("크롤링 완료!")
        print(f"총 실행 시간: {hours}시간 {minutes}분 {seconds}초")
        print(f"처리된 책: {total_processed}권")
        print(f"신규 저장: {new_count}권")
        print(f"업데이트: {updated_count}권")
        print(f"건너뜀: {skipped_count}권")
        print(f"에러: {error_count}건")
        print("=" * 60)

if __name__ == "__main__":
    crawl_and_save()