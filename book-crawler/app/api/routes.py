from fastapi import APIRouter, BackgroundTasks
from app.db.database import SessionLocal
from app.db.crud import add_or_update_book
from app.crawler.kyobo import crawl_kyobo_books
from app.utils.logger import logger
import uuid
from typing import Dict
from datetime import datetime

router = APIRouter()

# 작업 상태를 저장할 딕셔너리 (실제로는 Redis 사용 권장)
job_status: Dict[str, dict] = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def background_crawl_task(job_id: str, max_pages: int = 50):
    """백그라운드에서 실행될 크롤링 작업"""
    db = SessionLocal()
    
    try:
        # 작업 시작
        job_status[job_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": 0,
            "current_book": 0,
            "total_books": 0
        }
        
        logger.info(f"백그라운드 크롤링 시작: job_id={job_id}, max_pages={max_pages}")
        
        # 진행상황 업데이트 콜백
        def update_progress(**kwargs):
            if 'total_books' in kwargs:
                job_status[job_id]["total_books"] = kwargs['total_books']
            if 'current_book' in kwargs:
                job_status[job_id]["current_book"] = kwargs['current_book']
                job_status[job_id]["progress"] = (kwargs['current_book'] / job_status[job_id]["total_books"]) * 100
        
        # 크롤링 실행
        books = crawl_kyobo_books(limit=None, max_pages=max_pages, progress_callback=update_progress)
        
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for idx, book in enumerate(books):
            try:
                _, is_new = add_or_update_book(db, book)
                
                if is_new:
                    new_count += 1
                else:
                    updated_count += 1
                    
                # 진행상황 업데이트 (10권마다)
                if (idx + 1) % 10 == 0 or idx == len(books) - 1:
                    job_status[job_id].update({
                        "progress": ((idx + 1) / len(books)) * 100,
                        "current_book": idx + 1,
                        "books_processed": {
                            "new": new_count,
                            "updated": updated_count,
                            "errors": error_count
                        }
                    })
                    
            except Exception as e:
                error_count += 1
                logger.error(f"처리 실패: {book.get('book_name')} - {str(e)}")
                db.rollback()
                
        # 작업 완료
        job_status[job_id] = {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "started_at": job_status[job_id]["started_at"],
            "progress": 100,
            "result": {
                "crawled": len(books),
                "new": new_count,
                "updated": updated_count,
                "errors": error_count
            }
        }
        
        logger.info(f"백그라운드 크롤링 완료: job_id={job_id}")
        
    except Exception as e:
        logger.error(f"백그라운드 크롤링 실패: job_id={job_id}, error={str(e)}")
        job_status[job_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }
    finally:
        db.close()

@router.post("/crawl/kyobo/async")
async def crawl_books_async(
    background_tasks: BackgroundTasks,
    max_pages: int = 50
) -> dict:
    """비동기 크롤링 시작"""
    job_id = str(uuid.uuid4())
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        background_crawl_task,
        job_id,
        max_pages
    )
    
    logger.info(f"크롤링 작업 생성: job_id={job_id}")
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"크롤링 작업이 시작되었습니다. (최대 {max_pages}페이지)",
        "check_status_url": f"/crawl/status/{job_id}"
    }

@router.get("/crawl/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """크롤링 작업 상태 확인"""
    if job_id not in job_status:
        return {
            "error": "작업을 찾을 수 없습니다.",
            "job_id": job_id
        }
    
    return {
        "job_id": job_id,
        **job_status[job_id]
    }

@router.get("/crawl/jobs")
async def list_jobs() -> dict:
    """모든 크롤링 작업 목록"""
    return {
        "total": len(job_status),
        "jobs": [
            {
                "job_id": job_id,
                "status": status.get("status"),
                "started_at": status.get("started_at"),
                "progress": status.get("progress", 0)
            }
            for job_id, status in job_status.items()
        ]
    }

