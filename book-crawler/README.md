# Book Crawler API

교보문고에서 책 정보를 크롤링하는 FastAPI 기반 웹 서비스입니다.

## 기능

- 교보문고 주간 베스트셀러 크롤링
- MySQL 데이터베이스에 책 정보 저장
- ISBN 기반 중복 체크 및 업데이트

## 설치 방법

### 1. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 데이터베이스 설정을 변경하세요
```

### 4. 데이터베이스 설정
MySQL에서 데이터베이스를 생성합니다:
```sql
CREATE DATABASE book_db_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

테이블을 생성합니다:
```bash
python scripts/create_tables.py
```

### 5. ChromeDriver 설치
Selenium이 동작하려면 ChromeDriver가 필요합니다. 시스템에 Chrome이 설치되어 있어야 합니다.

## 실행 방법

### API 서버 실행
```bash
python run.py
```

서버가 실행되면 http://localhost:8000 에서 접속할 수 있습니다.

### API 문서
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 사용법

### 책 크롤링
```bash
curl -X POST http://localhost:8000/crawl/kyobo
```

응답 예시:
```json
{
  "crawled": 20,
  "new": 15,
  "updated": 5,
  "errors": 0
}
```

## 테스트

크롤러 테스트 실행:
```bash
# 3권만 테스트 (기본값)
python tests/test_crawler.py

# 10권 테스트
python tests/test_crawler.py 10

# 전체 테스트
python tests/test_crawler.py all
```

## 환경 변수

- `DATABASE_URL`: MySQL 데이터베이스 연결 URL
- `CRAWL_DELAY`: 크롤링 요청 간격 (초, 기본값: 1.0)
- `CHROME_HEADLESS`: 브라우저 헤드리스 모드 (true/false, 기본값: true)
- `CHROME_USER_AGENT`: 브라우저 User-Agent 설정

## 프로젝트 구조

```
book-crawler/
├── app/
│   ├── api/          # API 라우트
│   ├── crawler/      # 크롤링 로직
│   ├── db/           # 데이터베이스 모델 및 CRUD
│   └── utils/        # 유틸리티 (로거 등)
├── scripts/          # 유틸리티 스크립트
├── tests/            # 테스트 코드
├── logs/             # 로그 파일 (자동 생성)
└── run.py            # 진입점
```