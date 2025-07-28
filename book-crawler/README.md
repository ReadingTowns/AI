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
  }
}
```

## 🧪 테스트

```bash
python tests/test_crawler.py          # 3권 테스트
python tests/test_crawler.py 10 2     # 10권, 2페이지
python tests/test_async_api.py        # API 테스트
```

## ⚙️ 환경변수 (.env)

```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/book_db_test
MAX_BESTSELLER_PAGES=50
MAX_REVIEW_PAGES=5
CRAWL_DELAY=1.0
```