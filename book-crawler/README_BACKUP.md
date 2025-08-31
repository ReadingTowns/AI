# 데이터베이스 백업 및 복구 가이드

## 🔒 DB 안정성 개선 사항

### 1. 자동 백업 시스템
- 크롤링 시작 전 자동 백업
- 100권마다 중간 백업
- 크롤링 완료 후 최종 백업

### 2. 중간 저장 (배치 커밋)
- 10권씩 트랜잭션 처리
- 실패 시 해당 배치만 롤백
- 메모리 효율적 처리

### 3. 진행 상태 추적
- `crawl_progress.json` 파일에 진행 상황 저장
- 중단 시 `--resume` 옵션으로 재개 가능

## 📋 백업 관리 명령어

### 백업 생성
```bash
# 수동 백업 생성
python scripts/backup_db.py backup

# 특정 타입으로 백업
python scripts/backup_db.py backup --type manual
```

### 백업 목록 확인
```bash
python scripts/backup_db.py list
```

### 백업 복구
```bash
# 백업 목록 확인 후 파일명으로 복구
python scripts/backup_db.py restore --file backup_book_db_test_20240829_120000.sql.gz
```

## 🔄 크롤링 명령어

### 새로 시작
```bash
python scripts/crawl_full.py
```

### 중단된 작업 재개
```bash
python scripts/crawl_full.py --resume
```

## 📊 데이터베이스 모니터링

### 전체 상태 보고서
```bash
python scripts/monitor_db.py
```

### 통계만 확인
```bash
python scripts/monitor_db.py --stats
```

### 데이터 무결성 검증
```bash
python scripts/monitor_db.py --validate
```

### 최근 활동 확인
```bash
# 최근 24시간
python scripts/monitor_db.py --recent 24

# 최근 1시간
python scripts/monitor_db.py --recent 1
```

## 🚨 비상 복구 절차

### DB가 완전히 날아간 경우
1. 백업 목록 확인
   ```bash
   python scripts/backup_db.py list
   ```

2. 가장 최근 백업으로 복구
   ```bash
   python scripts/backup_db.py restore --file [백업파일명]
   ```

3. 복구 확인
   ```bash
   python scripts/monitor_db.py --stats
   ```

### 직접 MySQL 명령어로 복구
```bash
# 압축 해제 및 복구
gunzip -c backups/backup_book_db_test_20240829_180000.sql.gz | mysql -u root -p book_db_test
```

## 📁 백업 파일 구조

```
backups/
├── backup_book_db_test_before_crawl_*.sql.gz  # 크롤링 시작 전
├── backup_book_db_test_auto_*.sql.gz          # 100권마다 자동
├── backup_book_db_test_final_*.sql.gz         # 크롤링 완료 후
├── backup_book_db_test_manual_*.sql.gz        # 수동 백업
└── backup_metadata.json                       # 백업 메타데이터
```

## ⚡ 성능 비교

| 데이터량 | 크롤링 시간 | 백업 복구 시간 |
|---------|------------|---------------|
| 100권   | 15-20분    | 1-2초         |
| 1000권  | 2-3시간    | 10-30초       |
| 5000권  | 10-15시간  | 1-2분         |

## 🔧 환경 변수 설정 (.env)

```env
# 데이터베이스 설정
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/book_db_test
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=book_db_test
DB_PORT=3306

# 크롤링 설정
MAX_BESTSELLER_PAGES=50
MAX_REVIEW_PAGES=5
```

## 💡 추가 보안 팁

1. **정기 백업 설정 (crontab)**
   ```bash
   # 매일 새벽 3시 자동 백업
   0 3 * * * /usr/bin/python3 /path/to/scripts/backup_db.py backup --type scheduled
   ```

2. **백업 파일 외부 저장**
   ```bash
   # 외장 드라이브로 복사
   cp backups/*.sql.gz /mnt/backup/

   # 클라우드 동기화 (예: rclone)
   rclone copy backups/ gdrive:book-backups/
   ```

3. **백업 파일 암호화**
   ```bash
   # 백업 파일 암호화
   openssl enc -aes-256-cbc -salt -in backup.sql.gz -out backup.sql.gz.enc

   # 복호화
   openssl enc -aes-256-cbc -d -in backup.sql.gz.enc -out backup.sql.gz
   ```