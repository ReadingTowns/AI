from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

BASE_URL = "https://store.kyobobook.co.kr/bestseller/online/weekly"
DETAIL_BASE = "https://product.kyobobook.co.kr"

def crawl_kyobo_books():#limit=10
    options = Options()
    options.add_argument("--headless")  # 창 안 띄우고 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(options=options)
    driver.get(BASE_URL)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.prod_link"))
        )
    except Exception as e:
        print("[ERROR] 페이지 로딩 실패")
        driver.quit()
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    books = []

    for i, a_tag in enumerate(soup.select("a.prod_link")):
        #if i >= limit:
        #    break
        title = a_tag.text.strip()
        href = a_tag.get("href", "")
        if not href.startswith("http"):
            href = DETAIL_BASE + href

        # 불필요한 텍스트 필터링
        if title != '' and title != '새창보기 아이콘새창보기':
            books.append({
                "book_name": title,
                "book_detail_url": href
             })

    print(f"[INFO] 크롤링된 책 수: {len(books)}")
    for b in books:
        print(b)

    return books