# Book Crawler API

교보문고 베스트셀러 크롤러 (FastAPI + Selenium)

## 🚀 빠른 시작

```bash
# 1. 설치
pip install -r requirements.txt

# 2. DB 설정
mysql -u root -e "CREATE DATABASE book_db_test"
python scripts/create_tables.py

# 3. 서버 실행  
python run.py

# 4. 크롤링 시작 (백그라운드)
curl -X POST http://localhost:8000/crawl/kyobo/async?max_pages=50
```

## 🔧 크롤링 실행 방법

### 1. API 서버 방식 (권장)
FastAPI 서버를 통해 크롤링을 백그라운드로 실행합니다.

```bash
# 서버 시작
python run.py

# 크롤링 요청 (다른 터미널에서)
curl -X POST http://localhost:8000/crawl/kyobo/async?max_pages=50

# 진행상황 확인
curl http://localhost:8000/crawl/status/{job_id}
```

**특징:**
- 백그라운드 실행 (요청 즉시 job_id 반환)
- 실시간 진행률 조회 가능
- 타임아웃 없음 (장시간 크롤링 가능)
- 원격 접근 가능
- FastAPI 서버 실행 필요

### 2. 직접 스크립트 방식
서버 없이 Python 스크립트를 직접 실행합니다.

```bash
# 테스트용 (소량)
python tests/test_crawler.py          # 3권 테스트
python tests/test_crawler.py 10 2     # 10권, 2페이지

# 전체 크롤링
python scripts/crawl_full.py          # 전체 페이지
python scripts/crawl_with_save.py     # 중간 저장 포함
```

**특징:**
- 서버 없이 바로 실행
- 콘솔에서 즉시 결과 확인
- 간단한 테스트에 적합
- 실행 중 중단 시 데이터 손실 가능
- 로컬에서만 실행 가능

### 언제 어떤 방식을 사용할까?

| 상황 | 권장 방식 |
|------|----------|
| 웹 서비스 통합 | API 서버 |
| 장시간 대량 크롤링 | API 서버 |
| 여러 작업 동시 관리 | API 서버 |
| 빠른 테스트 | 직접 스크립트 |
| 일회성 크롤링 | 직접 스크립트 |
| 개발/디버깅 | 직접 스크립트 |

## 📡 API 문서

http://localhost:8000/docs

### 주요 엔드포인트

- `POST /crawl/kyobo/async` - 크롤링 시작 (최대 50페이지)
- `GET /crawl/status/{job_id}` - 진행상황 확인
- `GET /crawl/jobs` - 전체 작업 목록

## 🗂️ 데이터 구조

```json
{
  "book_name": "책 제목",
  "author": "저자",
  "publisher": "출판사", 
  "isbn": "ISBN",
  "keyword": "키워드1, 키워드2",
  "review": {
    "review_count": 150,
    "reviews": [
      {"text": "리뷰 내용", "rating": "5"}
    ]
  },
  "created_at": "2024-01-01 12:00:00",
  "updated_at": "2024-01-01 12:00:00"
}
```


## ⚙️ 환경변수 (.env)

```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/book_db_test
MAX_BESTSELLER_PAGES=50
MAX_REVIEW_PAGES=5
```

## 🔄 최근 개선사항

### 크롤링 효율성 개선
- **ISBN 중복 체크**: 이미 크롤링된 책은 자동으로 건너뛰어 속도 향상
- **중간 저장 기능**: 10권마다 자동 commit으로 데이터 손실 방지
- **타임스탬프 자동 관리**: `created_at`, `updated_at` 필드 자동 설정

### 안정성 개선
- **DB 스키마 개선**: ENUM 타입을 대문자로 통일 (CRAWLING, MANUAL), 테이블명 변경 (book → books)
- **환경변수 우선순위**: 시스템 환경변수 > .env 파일 순으로 설정 적용
- **에러 핸들링**: ZeroDivisionError 방지 및 크롤링 실패 시 안전한 처리