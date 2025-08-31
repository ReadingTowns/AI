#!/usr/bin/env python3
"""
데이터베이스 모니터링 및 검증 스크립트
데이터 무결성 확인 및 통계 제공
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Book, Review
from app.utils.logger import logger
from sqlalchemy import func, text
from datetime import datetime, timedelta
import json

class DatabaseMonitor:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_statistics(self):
        """데이터베이스 통계 조회"""
        try:
            # 책 통계
            total_books = self.db.query(func.count(Book.id)).scalar()
            books_with_reviews = self.db.query(func.count(func.distinct(Review.book_id))).scalar()
            total_reviews = self.db.query(func.count(Review.id)).scalar()
            
            # 최근 업데이트
            latest_book = self.db.query(Book).order_by(Book.updated_at.desc()).first()
            
            # 카테고리별 통계
            category_stats = self.db.query(
                Book.category,
                func.count(Book.id).label('count')
            ).group_by(Book.category).all()
            
            # 평점 통계
            avg_rating = self.db.query(func.avg(Book.rating)).scalar()
            
            stats = {
                'total_books': total_books,
                'books_with_reviews': books_with_reviews,
                'total_reviews': total_reviews,
                'average_rating': float(avg_rating) if avg_rating else 0,
                'latest_update': latest_book.updated_at.isoformat() if latest_book else None,
                'categories': {cat: count for cat, count in category_stats}
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return None
    
    def validate_data(self):
        """데이터 무결성 검증"""
        issues = []
        
        try:
            # 1. ISBN 중복 체크
            duplicates = self.db.query(
                Book.isbn_13,
                func.count(Book.id).label('count')
            ).group_by(Book.isbn_13).having(func.count(Book.id) > 1).all()
            
            if duplicates:
                for isbn, count in duplicates:
                    issues.append(f"ISBN 중복: {isbn} ({count}개)")
            
            # 2. 필수 필드 누락 체크
            missing_title = self.db.query(func.count(Book.id)).filter(
                (Book.book_name == None) | (Book.book_name == '')
            ).scalar()
            
            if missing_title:
                issues.append(f"제목 없는 책: {missing_title}권")
            
            # 3. 비정상 가격 체크
            abnormal_price = self.db.query(func.count(Book.id)).filter(
                (Book.price < 0) | (Book.price > 1000000)
            ).scalar()
            
            if abnormal_price:
                issues.append(f"비정상 가격: {abnormal_price}권")
            
            # 4. 리뷰 연결 검증
            orphan_reviews = self.db.query(func.count(Review.id)).filter(
                ~Review.book_id.in_(
                    self.db.query(Book.id)
                )
            ).scalar()
            
            if orphan_reviews:
                issues.append(f"책 없는 리뷰: {orphan_reviews}개")
            
            return issues
            
        except Exception as e:
            logger.error(f"데이터 검증 실패: {str(e)}")
            return [f"검증 실패: {str(e)}"]
    
    def check_recent_activity(self, hours=24):
        """최근 활동 확인"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_books = self.db.query(func.count(Book.id)).filter(
                Book.created_at >= cutoff_time
            ).scalar()
            
            recent_updates = self.db.query(func.count(Book.id)).filter(
                Book.updated_at >= cutoff_time
            ).scalar()
            
            recent_reviews = self.db.query(func.count(Review.id)).filter(
                Review.created_at >= cutoff_time
            ).scalar()
            
            return {
                'period_hours': hours,
                'new_books': recent_books,
                'updated_books': recent_updates,
                'new_reviews': recent_reviews
            }
            
        except Exception as e:
            logger.error(f"최근 활동 확인 실패: {str(e)}")
            return None
    
    def get_storage_info(self):
        """데이터베이스 용량 정보"""
        try:
            # MySQL 테이블 크기 조회
            query = text("""
                SELECT 
                    table_name,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.TABLES 
                WHERE table_schema = :db_name
                ORDER BY (data_length + index_length) DESC
            """)
            
            db_name = os.getenv('DB_NAME', 'book_db_test')
            result = self.db.execute(query, {'db_name': db_name}).fetchall()
            
            storage_info = {}
            total_size = 0
            
            for table_name, size_mb in result:
                storage_info[table_name] = float(size_mb) if size_mb else 0
                total_size += float(size_mb) if size_mb else 0
            
            storage_info['total_size_mb'] = total_size
            
            return storage_info
            
        except Exception as e:
            logger.error(f"용량 정보 조회 실패: {str(e)}")
            return None
    
    def generate_report(self):
        """종합 보고서 생성"""
        print("\n" + "=" * 60)
        print("데이터베이스 상태 보고서")
        print("=" * 60)
        
        # 통계
        stats = self.get_statistics()
        if stats:
            print("\n📊 데이터 통계:")
            print(f"  - 총 책 수: {stats['total_books']:,}권")
            print(f"  - 리뷰 있는 책: {stats['books_with_reviews']:,}권")
            print(f"  - 총 리뷰 수: {stats['total_reviews']:,}개")
            print(f"  - 평균 평점: {stats['average_rating']:.2f}")
            print(f"  - 최근 업데이트: {stats['latest_update']}")
        
        # 데이터 검증
        issues = self.validate_data()
        print("\n🔍 데이터 무결성 검사:")
        if issues:
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print("  ✅ 모든 데이터가 정상입니다")
        
        # 최근 활동
        recent = self.check_recent_activity(24)
        if recent:
            print(f"\n📈 최근 24시간 활동:")
            print(f"  - 신규 책: {recent['new_books']}권")
            print(f"  - 업데이트된 책: {recent['updated_books']}권")
            print(f"  - 신규 리뷰: {recent['new_reviews']}개")
        
        # 용량 정보
        storage = self.get_storage_info()
        if storage:
            print(f"\n💾 저장 용량:")
            print(f"  - 전체 크기: {storage['total_size_mb']:.2f} MB")
            for table, size in storage.items():
                if table != 'total_size_mb' and size > 0:
                    print(f"  - {table}: {size:.2f} MB")
        
        print("\n" + "=" * 60)
        
        # JSON 파일로 저장
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'validation_issues': issues,
            'recent_activity': recent,
            'storage_info': storage
        }
        
        report_file = f"db_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 상세 보고서 저장: {report_file}")
        print("=" * 60)
        
        return report_data
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터베이스 모니터링')
    parser.add_argument('--stats', action='store_true', help='통계만 출력')
    parser.add_argument('--validate', action='store_true', help='검증만 수행')
    parser.add_argument('--recent', type=int, help='최근 N시간 활동 확인')
    parser.add_argument('--full', action='store_true', help='전체 보고서 생성')
    
    args = parser.parse_args()
    
    monitor = DatabaseMonitor()
    
    if args.stats:
        stats = monitor.get_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    elif args.validate:
        issues = monitor.validate_data()
        if issues:
            print("데이터 무결성 문제:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ 데이터 무결성 검사 통과")
    elif args.recent:
        recent = monitor.check_recent_activity(args.recent)
        print(f"최근 {args.recent}시간 활동:")
        print(json.dumps(recent, indent=2))
    else:
        monitor.generate_report()

if __name__ == "__main__":
    main()