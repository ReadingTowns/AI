#!/usr/bin/env python3
"""
교보문고 크롤러 테스트 스크립트
기본적으로 3권만 테스트하며, 인자로 수량 조정 가능

사용법:
    python test_crawler.py          # 3권 테스트 (빠른 테스트)
    python test_crawler.py 10       # 10권 테스트
    python test_crawler.py all      # 전체 테스트 (제한 없음)
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler.kyobo import crawl_kyobo_books

def test_crawler_small(limit=3, test_pages=1):
    """크롤링 기능 테스트"""
    print("=" * 60)
    if limit:
        print(f"교보문고 크롤러 테스트 시작 ({limit}권 제한, {test_pages}페이지)")
    else:
        print(f"교보문고 크롤러 전체 테스트 시작 ({test_pages}페이지)")
    print("=" * 60)
    
    try:
        # 지정된 수만큼 크롤링
        books = crawl_kyobo_books(limit=limit, max_pages=test_pages)
        
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
            print(f"키워드: {book.get('keyword', 'N/A')}")
            print(f"요약: {book.get('summary', 'N/A')[:100]}...")  # 요약은 100자까지만
            
            # 리뷰 정보 출력
            if book.get('review'):
                review_data = json.loads(book['review'])
                if isinstance(review_data, dict):
                    # 새 형식 (review_count 포함)
                    print(f"\n전체 리뷰 수: {review_data.get('review_count', 0)}")
                    reviews = review_data.get('reviews', [])
                else:
                    # 이전 형식 (리스트)
                    reviews = review_data
                    print(f"\n리뷰 수: {len(reviews)}")
                
                # 처음 3개 리뷰 출력
                for i, review in enumerate(reviews[:3]):
                    print(f"\n리뷰 {i+1}:")
                    print(f"  평점: {review.get('rating', 'N/A')}")
                    print(f"  내용: {review.get('text', 'N/A')[:50]}...")
            
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
        if len(books) > 0:
            print(f"성공률: {complete_books/len(books)*100:.1f}%")
        else:
            print("성공률: 0.0%")
        
        print("\n[필드별 누락 현황]")
        for field, count in missing_info.items():
            if count > 0:
                print(f"- {field}: {count}권 누락")
        
    except Exception as e:
        print(f"\n[ERROR] 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 명령줄 인자로 테스트할 책 수와 페이지 수 지정 가능
    limit = 3
    pages = 1
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "all":
            limit = None
        else:
            try:
                limit = int(sys.argv[1])
            except ValueError:
                print("올바른 숫자를 입력하거나 'all'을 입력해주세요.")
                sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            pages = int(sys.argv[2])
        except ValueError:
            print("페이지 수는 숫자로 입력해주세요.")
            sys.exit(1)
    
    test_crawler_small(limit=limit, test_pages=pages)