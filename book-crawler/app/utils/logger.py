import logging
import sys
from pathlib import Path

# 로그 디렉토리 생성
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 로거 생성
logger = logging.getLogger("book_crawler")
logger.setLevel(logging.DEBUG)

# 포맷터 생성
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 파일 핸들러
file_handler = logging.FileHandler(log_dir / "app.log", encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 핸들러 추가
logger.addHandler(console_handler)
logger.addHandler(file_handler)