#!/usr/bin/env python3
"""
데이터베이스 테이블 생성 스크립트
- 테이블이 존재하지 않을 때만 생성
- 기존 데이터 보존
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from app.db.database import engine, Base
from app.db.models import Book

def check_and_create_tables():
    """테이블 확인 및 생성"""
    
    # 인스펙터를 사용하여 기존 테이블 확인
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print("=== 데이터베이스 테이블 관리 ===")
    print(f"현재 데이터베이스: {engine.url.database}")
    
    if existing_tables:
        print("\n기존 테이블 목록:")
        for table in existing_tables:
            print(f"  - {table}")
    else:
        print("\n기존 테이블이 없습니다.")
    
    # 테이블이 없을 때만 생성 (checkfirst=True)
    print("\n테이블 생성 중...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    # 생성 후 테이블 확인
    inspector = inspect(engine)
    final_tables = inspector.get_table_names()
    
    # 새로 생성된 테이블 확인
    new_tables = set(final_tables) - set(existing_tables)
    if new_tables:
        print("\n새로 생성된 테이블:")
        for table in new_tables:
            print(f"  - {table}")
    else:
        print("\n모든 테이블이 이미 존재합니다.")
    
    # Book 테이블 정보 표시
    if Book.__tablename__ in final_tables:
        columns = inspector.get_columns(Book.__tablename__)
        print(f"\n'{Book.__tablename__}' 테이블 구조:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}")

if __name__ == "__main__":
    check_and_create_tables()