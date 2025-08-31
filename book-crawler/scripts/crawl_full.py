#!/usr/bin/env python3
"""
교보문고 전체 크롤링 스크립트
베스트셀러 50페이지, 각 책마다 리뷰 5페이지씩 크롤링하여 DB에 저장
안정성 개선: 자동 백업, 중간 저장, 트랜잭션 관리
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.kyobo import crawl_kyobo_books
from app.db.database import SessionLocal
from app.db.crud import add_or_update_book
from app.utils.logger import logger
from scripts.backup_db import DatabaseBackup
import time
import json
from pathlib import Path

def crawl_full_data(resume=False):
    """50페이지 전체 데이터 크롤링 및 DB 저장
    
    Args:
        resume: 중단된 작업 재개 여부
    """
    print("=" * 60)
    print("교보문고 전체 크롤링 시작")
    print("베스트셀러: 최대 50페이지")
    print("리뷰: 각 책당 최대 5페이지")
    print("=" * 60)
    
    start_time = time.time()
    
    # 크롤링 시작 전 백업 생성
    backup_manager = DatabaseBackup()
    print("\n크롤링 시작 전 DB 백업 중...")
    backup_path = backup_manager.create_backup(backup_type="before_crawl")
    if backup_path:
        print(f"백업 완료: {backup_path}\n")
    
    # 진행 상태 파일
    progress_file = Path("crawl_progress.json")
    progress_data = {
        'last_page': 0,
        'processed_books': [],
        'start_time': start_time
    }
    
    # 재개 모드인 경우 이전 진행 상태 로드
    if resume and progress_file.exists():
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        print(f"\n이전 작업 재개: {progress_data['last_page']}페이지부터 시작")
        print(f"이미 처리된 책: {len(progress_data['processed_books'])}권\n")
    
    # 환경변수 설정 확인
    os.environ.setdefault("MAX_BESTSELLER_PAGES", "50")
    os.environ.setdefault("MAX_REVIEW_PAGES", "5")
    
    # 크롤링 실행
    try:
        books = crawl_kyobo_books(limit=None, max_pages=50)
        
        # 재개 모드인 경우 이미 처리된 책 제외
        if resume and progress_data['processed_books']:
            processed_isbns = set(progress_data['processed_books'])
            books = [book for book in books if book.get('isbn_13') not in processed_isbns]
        
        print(f"\n총 {len(books)}권의 책 정보를 크롤링했습니다.")
        
        # DB 세션 생성
        db = SessionLocal()
        
        new_count = 0
        updated_count = 0
        error_count = 0
        batch_size = 10  # 배치 크기
        
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
                
                # ISBN 저장 (진행 상태 추적용)
                if book.get('isbn_13'):
                    progress_data['processed_books'].append(book.get('isbn_13'))
                    
                # 배치 처리 및 중간 저장 (10권마다)
                if (idx + 1) % batch_size == 0:
                    print(f"\n진행상황: {idx + 1}/{len(books)}권 처리 완료")
                    print("중간 저장 중...")
                    
                    try:
                        # 트랜잭션 커밋
                        db.commit()
                        logger.info(f"배치 {(idx + 1) // batch_size} 커밋 완료")
                        
                        # 진행 상태 저장
                        with open(progress_file, 'w') as f:
                            json.dump(progress_data, f, indent=2, ensure_ascii=False)
                        
                        # 100권마다 자동 백업
                        if (idx + 1) % 100 == 0:
                            print(f"\n자동 백업 생성 중... ({idx + 1}권 처리 시점)")
                            backup_path = backup_manager.create_backup(backup_type="auto")
                            if backup_path:
                                print(f"백업 완료: {backup_path}\n")
                        
                    except Exception as commit_error:
                        logger.error(f"커밋 실패: {str(commit_error)}")
                        db.rollback()
                        # 실패한 배치의 책들을 진행 상태에서 제거
                        for _ in range(min(batch_size, len(progress_data['processed_books']))):
                            if progress_data['processed_books']:
                                progress_data['processed_books'].pop()
                    
            except Exception as e:
                error_count += 1
                logger.error(f"처리 실패: {book.get('book_name')} - {str(e)}")
                db.rollback()
                continue
        
        # 마지막 배치 커밋
        try:
            db.commit()
            logger.info("최종 커밋 완료")
        except Exception as e:
            logger.error(f"최종 커밋 실패: {str(e)}")
            db.rollback()
        
        db.close()
        
        # 진행 상태 파일 삭제 (성공적으로 완료된 경우)
        if progress_file.exists():
            os.remove(progress_file)
        
        # 크롤링 완료 후 최종 백업
        print("\n크롤링 완료 후 최종 백업 생성 중...")
        final_backup = backup_manager.create_backup(backup_type="final")
        if final_backup:
            print(f"최종 백업 완료: {final_backup}")
        
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
    import argparse
    
    parser = argparse.ArgumentParser(description='교보문고 전체 크롤링')
    parser.add_argument('--resume', action='store_true', 
                       help='중단된 작업 재개')
    
    args = parser.parse_args()
    crawl_full_data(resume=args.resume)