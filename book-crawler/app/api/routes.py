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
            "total_books": 0,
            "new_count": 0,
            "updated_count": 0,
            "error_count": 0
        }
        
        logger.info(f"백그라운드 크롤링 시작: job_id={job_id}, max_pages={max_pages}")
        
        # 먼저 책 링크만 수집
        from app.crawler.kyobo import collect_book_links, crawl_book_detail, create_chrome_driver
        book_links = collect_book_links(limit=None, max_pages=max_pages)
        
        job_status[job_id]["total_books"] = len(book_links)
        logger.info(f"수집된 책 링크: {len(book_links)}권")
        
        new_count = 0
        updated_count = 0
        error_count = 0
        driver = None
        RESTART_INTERVAL = 50
        
        try:
            # 각 책을 크롤링하고 즉시 DB에 저장
            for idx, book_info in enumerate(book_links):
                # 브라우저 생성 또는 재시작
                if driver is None or (idx > 0 and idx % RESTART_INTERVAL == 0):
                    if driver:
                        logger.info(f"브라우저 재시작 중... (메모리 관리)")
                        driver.quit()
                    driver = create_chrome_driver()
                
                # 책 상세 정보 크롤링
                logger.info(f"상세 정보 수집 중... ({idx + 1}/{len(book_links)})")
                book_detail = crawl_book_detail(driver, book_info["book_detail_url"])
                
                if book_detail:
                    # 즉시 DB에 저장
                    try:
                        book_data = {
                            "book_name": book_info["book_name"],
                            **book_detail,
                            "source_field": "CRAWLING"
                        }
                        
                        _, is_new = add_or_update_book(db, book_data)
                        
                        if is_new:
                            new_count += 1
                        else:
                            updated_count += 1
                            
                        # 10권마다 중간 저장
                        if (idx + 1) % 10 == 0:
                            db.commit()
                            logger.info(f"중간 저장 완료: {idx + 1}권 처리됨 (신규: {new_count}, 업데이트: {updated_count})")
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"DB 저장 실패: {book_info.get('book_name')} - {str(e)}")
                        db.rollback()
                
                # 진행상황 업데이트 (매 책마다)
                job_status[job_id].update({
                    "progress": ((idx + 1) / len(book_links)) * 100,
                    "current_book": idx + 1,
                    "new_count": new_count,
                    "updated_count": updated_count,
                    "error_count": error_count
                })
                
            # 브라우저 정리
            if driver:
                driver.quit()
                
        except Exception as e:
            logger.error(f"크롤링 중 오류: {str(e)}")
            if driver:
                driver.quit()
            raise
        
        # 마지막 남은 데이터 commit
        db.commit()
        logger.info(f"최종 저장 완료: 총 {len(book_links)}권 처리")
                
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


"""비동기 크롤링 시작"""
@router.post("/crawl/kyobo/async")
async def crawl_books_async(
    background_tasks: BackgroundTasks,
    max_pages: int = 50
) -> dict:
    job_id = str(uuid.uuid4())
    
    background_tasks.add_task( # 백그라운드 작업 추가
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


"""크롤링 작업 상태 확인"""
@router.get("/crawl/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    if job_id not in job_status:
        return {
            "error": "작업을 찾을 수 없습니다.",
            "job_id": job_id
        }
    
    return {
        "job_id": job_id,
        **job_status[job_id]
    }


"""모든 크롤링 작업 목록"""
@router.get("/crawl/jobs")
async def list_jobs() -> dict:
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

