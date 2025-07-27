#!/usr/bin/env python3
"""
교보문고 크롤러 빠른 테스트 스크립트
소량의 책(기본 3권)으로 빠르게 기능 검증

사용법:
    python test_crawler_small.py        # 3권 테스트
    python test_crawler_small.py 5      # 5권 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.kyobo import crawl_kyobo_books

def test_crawler_small(limit=3):
    """소량의 책으로 크롤링 기능 테스트"""
    print("=" * 60)
    print(f"교보문고 크롤러 테스트 시작 ({limit}권 제한)")
    print("=" * 60)
    
    try:
        # 지정된 수만큼 크롤링
        books = crawl_kyobo_books(limit=limit)
        
        print(f"\n총 {len(books)}권의 책 정보를 성공적으로 크롤링했습니다.\n")
        
        # 상세 정보 확인
        for idx, book in enumerate(books):
            print(f"\n[책 {idx + 1}] 상세 정보")
            print("=" * 40)
            print(f"제목: {book.get('book_name', 'N/A')}")
            print(f"상세 URL: {book.get('book_detail_url', 'N/A')}")
            print(f"이미지 URL: {book.get('book_image', 'N/A')}")
            print(f"저자: {book.get('author', 'N/A')}")
            print(f"출판사: {book.get('publisher', 'N/A')}")
            print(f"ISBN: {book.get('isbn', 'N/A')}")
            print(f"요약: {book.get('summary', 'N/A')[:100]}...")  # 요약은 100자까지만
            
        # 데이터 검증
        print("\n\n[데이터 검증 결과]")
        print("=" * 40)
        
        complete_books = 0
        missing_info = {
            'book_name': 0,
            'book_detail_url': 0,
            'book_image': 0,
            'author': 0,
            'publisher': 0,
            'isbn': 0,
            'summary': 0
        }
        
        for book in books:
            if all([
                book.get('book_name'),
                book.get('book_detail_url'),
                book.get('author'),
                book.get('publisher'),
                book.get('isbn')
            ]):
                complete_books += 1
            
            # 누락된 정보 카운트
            for field in missing_info:
                if not book.get(field):
                    missing_info[field] += 1
                
        print(f"완전한 정보를 가진 책: {complete_books}/{len(books)}")
        print(f"성공률: {complete_books/len(books)*100:.1f}%")
        
        print("\n[필드별 누락 현황]")
        for field, count in missing_info.items():
            if count > 0:
                print(f"- {field}: {count}권 누락")
        
    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 명령줄 인자로 테스트할 책 수 지정 가능
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            test_crawler_small(limit)
        except ValueError:
            print("올바른 숫자를 입력해주세요.")
            sys.exit(1)
    else:
        test_crawler_small()