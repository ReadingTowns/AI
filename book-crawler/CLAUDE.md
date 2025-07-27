# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

교보문고 웹사이트에서 책 정보를 크롤링하는 FastAPI 기반 Book Crawler API입니다. Selenium을 사용하여 웹 스크래핑을 수행하고 MySQL 데이터베이스에 책 정보를 저장합니다.

## 개발 명령어

### 애플리케이션 실행
```bash
python run.py
```
API 서버가 http://localhost:8000 에서 hot-reload 모드로 실행됩니다.

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 데이터베이스 설정
- MySQL이 로컬에서 실행 중이어야 함
- `book_db_test` 데이터베이스 생성 필요
- 데이터베이스 연결: `mysql+pymysql://root:@localhost:3306/book_db_test`

## 아키텍처 개요

### 애플리케이션 구조
- **FastAPI 애플리케이션**: `app/main.py`가 메인 진입점, `run.py`를 통해 실행
- **API 레이어**: `app/api/routes.py`에 라우트 정의
  - 주요 엔드포인트: `POST /crawl/kyobo` - 책 크롤링 트리거
- **크롤러 모듈**: `app/crawler/kyobo.py`에 Selenium 기반 웹 스크래핑 로직 구현
  - 교보문고 주간 베스트셀러 페이지 스크래핑
  - 탐지 방지를 위한 headless Chrome 사용
- **데이터 레이어**: 
  - `app/models.py`에 SQLAlchemy 모델 정의 (ISBN을 고유 식별자로 하는 Book 모델)
  - `app/database.py`에서 데이터베이스 세션 관리
  - `app/crud.py`에 CRUD 작업 구현

### 주요 기술 세부사항
- 크롤러는 특정 user-agent 설정과 함께 headless Chrome 실행
- 책 데이터: 이름, 상세 URL, 이미지, 저자, 출판사, 요약, ISBN 포함
- 현재 API 라우트에서 데이터베이스 작업은 주석 처리됨 (routes.py의 22번째 줄)
- 데이터베이스 세션에 의존성 주입 패턴 사용

### 중요 참고사항
- routes.py의 `add_book` 함수가 주석 처리되어 있어 현재는 책 정보를 출력만 하고 DB에 저장하지 않음
- ChromeDriver는 의존성으로 리스트되어 있지만 시스템에 별도 설치 필요할 수 있음
- 크롤러에는 결과 제한 기능이 있음 (주석 처리된 limit 매개변수)