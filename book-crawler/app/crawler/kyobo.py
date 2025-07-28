from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
import json
from app.utils.logger import logger

BASE_URL = "https://store.kyobobook.co.kr/bestseller/online/weekly"
DETAIL_BASE = "https://product.kyobobook.co.kr"

def crawl_book_detail(driver: webdriver.Chrome, url: str) -> dict | None:
    """개별 책의 상세 정보를 크롤링"""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # 페이지 로딩을 위한 추가 대기
        time.sleep(2)
        
        # JavaScript로 직접 데이터 추출
        book_image = driver.execute_script("""
            let img = document.querySelector('.portrait_img_box img') || 
                      document.querySelector('[class*="img_box"] img');
            return img ? img.src : '';
        """)
        
        author = driver.execute_script("""
            let authorElem = document.querySelector('.author a.detail_author') ||
                            document.querySelector('.author a');
            return authorElem ? authorElem.innerText.trim() : '';
        """)
        
        publisher = driver.execute_script("""
            // 방법 1: btn_publish_link 클래스
            let pubLink = document.querySelector('.btn_publish_link');
            if (pubLink) return pubLink.innerText.trim();
            
            // 방법 2: publish 클래스를 가진 요소 내의 링크
            let pubElem = document.querySelector('.publish a') ||
                         document.querySelector('[class*="publish"] a');
            if (pubElem) return pubElem.innerText.trim();
            
            // 방법 3: href에 publish 포함된 링크
            let links = document.querySelectorAll('a[href*="publish"], a[href*="publ"]');
            for (let link of links) {
                if (link.innerText && !link.innerText.includes('더보기')) {
                    return link.innerText.trim();
                }
            }
            
            return '';
        """)
        
        isbn = driver.execute_script("""
            let tables = document.querySelectorAll('table');
            for(let table of tables) {
                let rows = table.querySelectorAll('tr');
                for(let row of rows) {
                    let th = row.querySelector('th');
                    let td = row.querySelector('td');
                    if(th && td && th.innerText.includes('ISBN')) {
                        return td.innerText.trim();
                    }
                }
            }
            return '';
        """)
        
        summary = driver.execute_script("""
            let introElem = document.querySelector('.intro_bottom') ||
                           document.querySelector('[class*="intro"]');
            return introElem ? introElem.innerText : '';
        """)
        
        # 키워드 수집
        keywords = driver.execute_script("""
            let keywordList = [];
            
            // product_keyword_pick 영역에서만 tab_text 수집
            let keywordPickArea = document.querySelector('.product_keyword_pick');
            if (keywordPickArea) {
                let tabTexts = keywordPickArea.querySelectorAll('.tab_text');
                tabTexts.forEach(elem => {
                    let text = elem.innerText || elem.textContent || '';
                    text = text.trim();
                    if (text && text.length > 0) {
                        keywordList.push(text);
                    }
                });
            }
            
            // 중복 제거
            keywordList = [...new Set(keywordList)];
            
            // 쉼표로 구분된 문자열로 반환
            return keywordList.join(', ');
        """)
        
        # 리뷰 수집 (여러 페이지)
        all_reviews = []
        max_review_pages = int(os.getenv("MAX_REVIEW_PAGES", "5"))
        
        # 리뷰 탭 클릭 (필요한 경우)
        try:
            review_tab = driver.find_element(By.XPATH, "//a[contains(@class, 'tab_link') and contains(., '리뷰')]")
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)
        except:
            logger.debug("리뷰 탭을 찾을 수 없거나 이미 활성화됨")
        
        # 각 리뷰 페이지 순회
        for review_page in range(1, max_review_pages + 1):
            logger.debug(f"리뷰 페이지 {review_page}/{max_review_pages} 수집 중...")
            
            # 현재 페이지의 리뷰 수집
            page_reviews = driver.execute_script("""
                let reviewList = [];
                let commentItems = document.querySelectorAll('.comment_list .comment_item, .comment_list li');
                
                commentItems.forEach(item => {
                    let reviewText = '';
                    
                    // comment_text 클래스로 리뷰 텍스트 찾기
                    let textElem = item.querySelector('.comment_text');
                    if (textElem) {
                        reviewText = textElem.innerText.trim();
                    }
                    
                    // 평점 찾기 - input.form_rating의 value 속성에서 추출
                    let rating = '';
                    let ratingInput = item.querySelector('input.form_rating');
                    if (ratingInput && ratingInput.value) {
                        rating = ratingInput.value;
                    }
                    
                    if (reviewText) {
                        reviewList.push({
                            text: reviewText,
                            rating: rating
                        });
                    }
                });
                
                return reviewList;
            """)
            
            all_reviews.extend(page_reviews)
            
            # 다음 페이지로 이동
            if review_page < max_review_pages:
                try:
                    # 페이지네이션 버튼 찾기
                    next_button = driver.find_element(By.XPATH, f"//div[@class='pagination']//a[text()='{review_page + 1}']")
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2)
                except:
                    try:
                        # 다른 방식의 다음 버튼 찾기
                        next_button = driver.find_element(By.XPATH, "//a[contains(@class, 'btn_page_next')]")
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)
                    except:
                        logger.debug(f"리뷰 페이지 {review_page + 1}로 이동할 수 없음")
                        break
        
        reviews = all_reviews[:50]  # 최대 50개 리뷰만 저장
        
        # 리뷰 데이터를 객체로 구성 (review_count 포함)
        review_data = {
            "review_count": len(all_reviews),  # 전체 리뷰 개수
            "reviews": reviews  # 리뷰 리스트 (최대 50개)
        }
        
        # JSON 문자열로 변환 (DB 저장을 위해)
        review_json = json.dumps(review_data, ensure_ascii=False) if reviews else None
        
        logger.info(f"수집된 리뷰 수: {len(all_reviews)} (저장: {len(reviews)})")
        
        return {
            "book_image": book_image,
            "author": author,
            "publisher": publisher,
            "summary": summary,  # 전체 내용 저장
            "isbn": isbn,
            "keyword": keywords,  # 키워드 저장
            "review": review_json,  # 리뷰 객체를 JSON으로 저장
            "source_field": "crawling"
        }
        
    except Exception as e:
        logger.error(f"상세 페이지 크롤링 실패: {url}, {str(e)}")
        return None

def crawl_kyobo_books(limit: int | None = None, max_pages: int = 50, progress_callback=None) -> list[dict]:
    options = Options()
    
    # 환경변수에서 설정 읽기
    if os.getenv("CHROME_HEADLESS", "true").lower() == "true":
        options.add_argument("--headless")  # 브라우저 창을 띄우지 않고 백그라운드 실행
    
    options.add_argument("--no-sandbox") # 샌드박스 모드 비활성화
    options.add_argument("--disable-dev-shm-usage") # 메모리 사용량 최적화
    
    # User-Agent 설정
    user_agent = os.getenv("CHROME_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument(f"user-agent={user_agent}")
    
    options.add_argument("--window-size=1920x1080") # 브라우저 창 크기 설정

    driver = webdriver.Chrome(options=options)
    
    books = []
    book_links = []
    seen_isbns = set()  # 중복 제거를 위한 ISBN 추적
    
    # 환경변수에서 최대 페이지 수 읽기
    max_pages = int(os.getenv("MAX_BESTSELLER_PAGES", str(max_pages)))
    
    # 각 페이지 순회
    for page in range(1, max_pages + 1):
        if limit and len(book_links) >= limit:
            break
            
        logger.info(f"베스트셀러 페이지 {page}/{max_pages} 크롤링 중...")
        
        # 페이지 URL 구성
        page_url = f"{BASE_URL}?page={page}"
        driver.get(page_url)
        
        # 책 링크가 로딩될 때까지 대기
        try: 
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.prod_link"))
            )
        except Exception as e:
            logger.error(f"페이지 {page} 로딩 실패: {str(e)}")
            continue
        
        # 페이지 로딩 추가 대기
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 현재 페이지의 책 링크 수집
        page_book_count = 0
        for a_tag in soup.select("a.prod_link"):
            if limit and len(book_links) >= limit:
                break
                
            title = a_tag.text.strip()
            href = a_tag.get("href", "")
            if not href.startswith("http"):
                href = DETAIL_BASE + href

            # 불필요한 텍스트 필터링
            if title != '' and title != '새창보기 아이콘새창보기':
                book_links.append({
                    "book_name": title,
                    "book_detail_url": href
                })
                page_book_count += 1
        
        logger.info(f"페이지 {page}에서 {page_book_count}권의 책 발견")
        
        # 책이 없으면 더 이상 페이지가 없는 것으로 판단
        if page_book_count == 0:
            logger.info(f"페이지 {page}에 책이 없어 크롤링 종료")
            break

    logger.info(f"수집된 책 링크 수: {len(book_links)}")
    
    # 진행상황 콜백 호출
    if progress_callback:
        progress_callback(total_books=len(book_links))

    # 각 책의 상세 정보 수집
    for idx, book_info in enumerate(book_links):
        logger.info(f"상세 정보 수집 중... ({idx + 1}/{len(book_links)})")
        
        detail_info = crawl_book_detail(driver, book_info["book_detail_url"])
        
        if detail_info:
            # ISBN 중복 체크
            isbn = detail_info.get('isbn')
            if isbn and isbn not in seen_isbns:
                seen_isbns.add(isbn)
                # 기본 정보와 상세 정보 병합 (book_detail_url은 제외)
                complete_book_info = {
                    "book_name": book_info["book_name"],
                    **detail_info
                }
                books.append(complete_book_info)
            else:
                logger.debug(f"중복된 ISBN 발견, 건너뜀: {isbn}")
        else:
            # 상세 정보 크롤링 실패 시 기본 정보만 저장
            books.append({
                "book_name": book_info["book_name"],
                "book_image": None,
                "author": None,
                "publisher": None,
                "summary": None,
                "isbn": None,
                "keyword": None,
                "review": None,
                "source_field": "crawling"
            })
        
        # 요청 간격 조절 (봇 탐지 방지)
        crawl_delay = float(os.getenv("CRAWL_DELAY", "1"))
        time.sleep(crawl_delay)
        
        # 진행상황 콜백 호출 (10권마다)
        if progress_callback and ((idx + 1) % 10 == 0 or idx == len(book_links) - 1):
            progress_callback(current_book=idx + 1)

    driver.quit()
    
    logger.info(f"크롤링 완료. 총 {len(books)}권의 책 정보 수집")
    for book in books:
        logger.debug(f"제목: {book.get('book_name')}")
        logger.debug(f"저자: {book.get('author', 'N/A')}")
        logger.debug(f"출판사: {book.get('publisher', 'N/A')}")
        logger.debug(f"ISBN: {book.get('isbn', 'N/A')}")
        if book.get('review'):
            review_data = json.loads(book['review'])
            if isinstance(review_data, dict):
                logger.debug(f"전체 리뷰 수: {review_data.get('review_count', 0)}")
                logger.debug(f"저장된 리뷰 수: {len(review_data.get('reviews', []))}")
            else:
                logger.debug(f"리뷰 수: {len(review_data)}")
        logger.debug("-" * 50)

    return books