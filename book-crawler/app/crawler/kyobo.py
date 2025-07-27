from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

BASE_URL = "https://store.kyobobook.co.kr/bestseller/online/weekly"
DETAIL_BASE = "https://product.kyobobook.co.kr"

def crawl_book_detail(driver, url):
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
        
        return {
            "book_image": book_image,
            "author": author,
            "publisher": publisher,
            "summary": summary[:500] if summary else "",  # 요약은 500자로 제한
            "isbn": isbn
        }
        
    except Exception as e:
        print(f"[ERROR] 상세 페이지 크롤링 실패: {url}, {str(e)}")
        return None

def crawl_kyobo_books(limit=None):
    options = Options()
    options.add_argument("--headless")  # 브라우저 창을 띄우지 않고 백그라운드 실행
    options.add_argument("--no-sandbox") # 샌드박스 모드 비활성화
    options.add_argument("--disable-dev-shm-usage") # 메모리 사용량 최적화
    options.add_argument("user-agent=Mozilla/5.0") # User-Agent 설정으로 봇 차단 우회
    options.add_argument("--window-size=1920x1080") # 브라우저 창 크기 설정

    driver = webdriver.Chrome(options=options)
    driver.get(BASE_URL)

    # 책 링크가 로딩될 때까지 최대 10초 대기
    try: 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.prod_link"))
        )
    except Exception as e:
        print("[ERROR] 페이지 로딩 실패")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")

    books = []
    book_links = []

    # 먼저 모든 책 링크 수집
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

    print(f"[INFO] 수집된 책 링크 수: {len(book_links)}")

    # 각 책의 상세 정보 수집
    for idx, book_info in enumerate(book_links):
        print(f"[INFO] 상세 정보 수집 중... ({idx + 1}/{len(book_links)})")
        
        detail_info = crawl_book_detail(driver, book_info["book_detail_url"])
        
        if detail_info:
            # 기본 정보와 상세 정보 병합
            complete_book_info = {**book_info, **detail_info}
            books.append(complete_book_info)
        else:
            # 상세 정보 크롤링 실패 시 기본 정보만 저장
            books.append(book_info)
        
        # 요청 간격 조절 (봇 탐지 방지)
        time.sleep(1)

    driver.quit()
    
    print(f"[INFO] 크롤링 완료. 총 {len(books)}권의 책 정보 수집")
    for book in books:
        print(f"제목: {book.get('book_name')}")
        print(f"저자: {book.get('author', 'N/A')}")
        print(f"출판사: {book.get('publisher', 'N/A')}")
        print(f"ISBN: {book.get('isbn', 'N/A')}")
        print("-" * 50)

    return books