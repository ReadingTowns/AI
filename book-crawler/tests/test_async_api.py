#!/usr/bin/env python3
"""
비동기 API 테스트 스크립트
"""

import requests
import time
import json

API_URL = "http://localhost:8000"

def test_async_crawl():
    print("=" * 60)
    print("비동기 크롤링 API 테스트")
    print("=" * 60)
    
    # 1. 크롤링 시작
    print("\n1. 크롤링 작업 시작...")
    response = requests.post(f"{API_URL}/crawl/kyobo/async", params={"max_pages": 1})
    
    if response.status_code != 200:
        print(f"❌ 에러: {response.status_code} - {response.text}")
        return
        
    data = response.json()
    job_id = data["job_id"]
    
    print(f"✅ 작업 시작됨!")
    print(f"   Job ID: {job_id}")
    print(f"   메시지: {data['message']}")
    
    # 2. 진행상황 확인 (최대 2분간)
    print("\n2. 진행상황 확인 중...")
    
    start_time = time.time()
    timeout = 120  # 2분
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{API_URL}/crawl/status/{job_id}")
        status_data = response.json()
        
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        
        if status == "completed":
            print(f"\n✅ 작업 완료!")
            print(f"   소요 시간: {time.time() - start_time:.1f}초")
            print(f"   결과:")
            result = status_data.get("result", {})
            print(f"   - 크롤링된 책: {result.get('crawled', 0)}권")
            print(f"   - 신규: {result.get('new', 0)}권")
            print(f"   - 업데이트: {result.get('updated', 0)}권")
            print(f"   - 에러: {result.get('errors', 0)}건")
            break
            
        elif status == "failed":
            print(f"\n❌ 작업 실패!")
            print(f"   에러: {status_data.get('error', '알 수 없는 에러')}")
            break
            
        elif status == "running":
            current = status_data.get("current_book", 0)
            total = status_data.get("total_books", 0)
            
            print(f"\r⏳ 진행 중... {progress:.1f}% ({current}/{total}권)", end="", flush=True)
            
        time.sleep(2)
    else:
        print(f"\n⏱️  타임아웃! ({timeout}초 경과)")
        
    # 3. 모든 작업 목록 확인
    print("\n\n3. 전체 작업 목록:")
    response = requests.get(f"{API_URL}/crawl/jobs")
    jobs_data = response.json()
    
    print(f"총 작업 수: {jobs_data['total']}")
    for job in jobs_data['jobs']:
        print(f"   - Job ID: {job['job_id'][:8]}... | 상태: {job['status']} | 진행률: {job['progress']:.1f}%")

if __name__ == "__main__":
    test_async_crawl()