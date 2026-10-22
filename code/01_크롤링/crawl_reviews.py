# -*- coding: utf-8 -*-
"""
OliveYoung '여드름' 크림 다건 + 리뷰 전량(끝까지) 크롤링
- 상품 목록: startCount → 부족시 페이지네이터 fallback
- 리뷰: 성별(여성→남성) 필터 각각 끝까지 수집
- 스킨 태그 3분할: skin_type / skin_tone / skin_concerns
- 평점(원문/숫자) 포함, 드라이버 예외 시 재생성 후 1회 재시도
- CSV 컬럼:
  product_name, product_brand, product_link, customer_name,
  skin_type, skin_tone, skin_concerns, review, date,
  rating_text, rating, gender
"""

import os, re, csv, time, random
from urllib.parse import quote
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException,
    StaleElementReferenceException, InvalidSessionIdException
)

# =========================
# 0) 드라이버/환경 설정
# =========================
def make_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 필요 시 활성화
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=ko-KR")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36"
    )
    d = webdriver.Chrome(options=options)
    w = WebDriverWait(d, 12)
    return d, w

driver, wait = make_driver()

# =========================
# 1) 파라미터/경로
# =========================
keyword = "여드름"
items_per_page = 48
MAX_STARTCOUNT_PAGES = 1  # startCount 방식 최대 페이지수
PAGINATOR_MAX_CLICKS  = 60

START_AT = 0
MAX_PRODUCTS = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = PROJECT_ROOT / "outputs/data/raw"
CSV_PATH = os.path.join(BASE_DIR, "acne_cream_reviews.csv")
PRODUCT_LIST_CSV = os.path.join(BASE_DIR, "acne_cream_products.csv")
os.makedirs(BASE_DIR, exist_ok=True)

# =========================
# 2) 유틸
# =========================
def sleep_smart(a=1.0, b=2.0):
    time.sleep(random.uniform(a, b))

def parse_rating_to_float(text: str):
    if not text:
        return None
    nums = re.findall(r'(\d+(?:\.\d+)?)', text)
    if not nums:
        return None
    try:
        return float(nums[-1])
    except:
        return None

def safe_click(el):
    try:
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        try:
            el.click()
            return True
        except Exception:
            return False

def recreate_driver():
    global driver, wait
    try:
        driver.quit()
    except Exception:
        pass
    driver, wait = make_driver()

# =========================
# 3) 스킨 태그 분리(피부타입/피부톤/피부고민)
# =========================
SKIN_TYPE_SET = {"지성","건성","복합성","민감성","약건성","트러블성","중성"}
SKIN_TONE_SET = {"쿨톤","웜톤","봄웜톤","여름쿨톤","가을웜톤","겨울쿨톤","봄원톤"}
SKIN_CONCERN_SET = {
    "잡티","미백","주름","각질","트러블","블랙헤드","피지과다","민감성",
    "모공","탄력","홍조","아토피","다크서클"
}
ALIAS = {
    "봄원톤":"봄웜톤",
    "여드름":"트러블",
    "여드름성":"트러블성",
    "트러블성피부":"트러블성",
    "민감성피부":"민감성",
}

def _norm_token(s: str) -> str:
    t = (s or "").strip().replace(" ", "")
    return ALIAS.get(t, t)

def split_skin_tags(span_texts):
    skin_type = ""
    skin_tone = ""
    concerns = []
    seen = set()
    for raw in span_texts:
        tok = _norm_token(raw)
        if not tok or tok in seen:
            continue
        seen.add(tok)
        if not skin_type and tok in SKIN_TYPE_SET:
            skin_type = tok
            continue
        if not skin_tone and tok in SKIN_TONE_SET:
            skin_tone = "봄웜톤" if tok == "봄원톤" else tok
            continue
        if tok in SKIN_CONCERN_SET:
            concerns.append(tok)
    if skin_type == "민감성":
        concerns = [c for c in concerns if c != "민감성"]
    return skin_type, skin_tone, (" / ".join(concerns) if concerns else "")

# =========================
# 4) CSV 초기화 / Append  (gender 및 3컬럼 포함)
# =========================
def init_reviews_csv(path=CSV_PATH):
    with open(path, "w", newline="", encoding="utf-8-sig") as fw:
        writer = csv.DictWriter(
            fw,
            fieldnames=[
                "product_name","product_brand","product_link",
                "customer_name",
                "skin_type","skin_tone","skin_concerns",
                "review","date","rating_text","rating","gender"
            ]
        )
        writer.writeheader()

def append_reviews_to_csv(product, reviews, path=CSV_PATH):
    if not reviews:
        return
    with open(path, "a", newline="", encoding="utf-8-sig") as fa:
        writer = csv.DictWriter(
            fa,
            fieldnames=[
                "product_name","product_brand","product_link",
                "customer_name",
                "skin_type","skin_tone","skin_concerns",
                "review","date","rating_text","rating","gender"
            ]
        )
        for r in reviews:
            writer.writerow({
                "product_name":  product.get("product_name",""),
                "product_brand": product.get("product_brand",""),
                "product_link":  product.get("product_link",""),
                "customer_name": r.get("customer_name",""),
                "skin_type":     r.get("skin_type",""),
                "skin_tone":     r.get("skin_tone",""),
                "skin_concerns": r.get("skin_concerns",""),
                "review":        r.get("review",""),
                "date":          r.get("date",""),
                "rating_text":   r.get("rating_text",""),
                "rating":        r.get("rating",""),
                "gender":        r.get("gender",""),
            })

def write_product_list_csv(products, path=PRODUCT_LIST_CSV):
    with open(path, "w", newline="", encoding="utf-8-sig") as fw:
        writer = csv.DictWriter(fw, fieldnames=["product_name","product_brand","product_link"])
        writer.writeheader()
        for p in products:
            writer.writerow(p)

# =========================
# 5) 상품 목록 (startCount → paginator fallback)
# =========================
def wait_cards_loaded(timeout=12):
    end = time.time() + timeout
    sels = [
        "ul#w_cate_prd_list li.flag.li_result",
        "ul.cate_prd_list li",
        "div.prd_info .tx_name",
    ]
    while time.time() < end:
        for sel in sels:
            if driver.find_elements(By.CSS_SELECTOR, sel):
                return True
        driver.execute_script("window.scrollBy(0, 900);")
        sleep_smart(0.2, 0.4)
    return False

def parse_product_cards():
    cards = driver.find_elements(By.CSS_SELECTOR, "ul#w_cate_prd_list li.flag.li_result")
    if not cards:
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.cate_prd_list li")
    out = []
    for c in cards:
        try:
            try:
                name = c.find_element(By.CSS_SELECTOR, "div.prd_info .tx_name").text.strip()
            except NoSuchElementException:
                name = "N/A"
            try:
                brand = c.find_element(By.CSS_SELECTOR, "div.prd_info .tx_brand").text.strip()
            except NoSuchElementException:
                brand = "N/A"
            try:
                link = c.find_element(By.CSS_SELECTOR, "a").get_attribute("href") or ""
            except NoSuchElementException:
                link = ""
            if link:
                out.append({"product_name": name, "product_brand": brand, "product_link": link})
        except Exception:
            continue
    return out

def build_search_url(start_count=0):
    q = quote(keyword)
    return (
        "https://www.oliveyoung.co.kr/store/search/getSearchMain.do?"
        f"startCount={start_count}"
        "&sort=RANK%2FDESC&goods_sort=WEIGHT%2FDESC%2CRANK%2FDESC"
        "&collection=ALL&reQuery="
        "&viewtype=image&category=&catename=LCTG_ID&catedepth=1&rt="
        f"&listnum={items_per_page}&tmp_requery=&tmp_requery2="
        "&categoryDepthValue=2&cateId=10000010001&cateId2=100000100010015"
        "&BenefitAll_CHECK="
        f"&query={q}&realQuery={q}"
        "&selectCateNm=%ED%81%AC%EB%A6%BC+%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EC%97%90"
        "&typeChk=thum"
    )

def crawl_product_list_startcount():
    products, seen = [], set()
    for i in range(MAX_STARTCOUNT_PAGES):
        start_count = i * items_per_page
        try:
            driver.get(build_search_url(start_count))
        except WebDriverException as e:
            print(f"❌ 이동 실패(startCount={start_count}): {e}")
            continue
        if not wait_cards_loaded(10):
            print(f"❌ 리스트 로딩 타임아웃 (startCount={start_count})")
            continue
        cards = parse_product_cards()
        added = 0
        for p in cards:
            key = (p["product_name"], p["product_link"])
            if key not in seen:
                seen.add(key); products.append(p); added += 1
        print(f"✅ startCount={start_count} 수집: {len(cards)}개 (신규 {added})")
        if added == 0 and i > 0:
            break
    return products

def crawl_product_list_paginator():
    products, seen = [], set()
    try:
        driver.get(build_search_url(0))
    except WebDriverException as e:
        print(f"❌ 첫 페이지 이동 실패: {e}")
        return products
    if not wait_cards_loaded(10):
        print("❌ 첫 페이지 카드 로딩 실패"); return products
    for p in parse_product_cards():
        key = (p["product_name"], p["product_link"])
        if key not in seen:
            seen.add(key); products.append(p)
    clicks = 0
    while clicks < PAGINATOR_MAX_CLICKS:
        pager_links = driver.find_elements(By.CSS_SELECTOR, "div.pageing a")
        if not pager_links: break
        next_clicked = False
        for a in pager_links:
            label = (a.get_attribute("aria-label") or a.text or "").strip()
            if "다음" in label or "next" in label.lower():
                if safe_click(a):
                    clicks += 1; sleep_smart(1.0, 1.6)
                    if wait_cards_loaded(10):
                        added_here = 0
                        for p in parse_product_cards():
                            key = (p["product_name"], p["product_link"])
                            if key not in seen:
                                seen.add(key); products.append(p); added_here += 1
                        next_clicked = True
                break
        if not next_clicked:
            num_links = []
            for a in driver.find_elements(By.CSS_SELECTOR, "div.pageing a"):
                t = (a.text or "").strip()
                if t.isdigit(): num_links.append((int(t), a))
            num_links.sort(key=lambda x: x[0])
            clicked_numeric = False
            for _, a in reversed(num_links):
                if safe_click(a):
                    clicks += 1; sleep_smart(1.0, 1.6)
                    if wait_cards_loaded(10):
                        added_here = 0
                        for p in parse_product_cards():
                            key = (p["product_name"], p["product_link"])
                            if key not in seen:
                                seen.add(key); products.append(p); added_here += 1
                        clicked_numeric = added_here > 0
                    break
            if not clicked_numeric: break
    print(f"✅ 페이지네이터 방식 수집 완료: {len(products)}개")
    return products

def crawl_product_list():
    products = crawl_product_list_startcount()
    if len(products) <= items_per_page:
        print("ℹ️ startCount 결과가 적어 페이지네이터로 재시도")
        products = crawl_product_list_paginator()
    unique, seen = [], set()
    for p in products:
        key = (p["product_name"], p["product_link"])
        if key not in seen:
            seen.add(key); unique.append(p)
    print(f"✅ 최종 상품 수집: {len(unique)}개")
    return unique

# =========================
# 6) 리뷰 필터(성별) 적용 (nth-child 금지, 속성 기반 + 적용버튼 다각도 시도)
# =========================
def open_filter_panel():
    btn = None
    try:
        btn = wait.until(EC.element_to_be_clickable((By.ID, "filterBtn")))
    except TimeoutException:
        pass
    if not btn:
        cand = driver.find_elements(By.XPATH, "//button[contains(., '리뷰 검색 필터')]")
        if cand: btn = cand[0]
    if btn:
        driver.execute_script("arguments[0].click();", btn)
        sleep_smart(0.4, 0.8)

def ensure_first_review_page():
    """필터 적용 후 1페이지로 강제 이동(있으면)."""
    try:
        pager = driver.find_element(By.CSS_SELECTOR, "#gdasContentsArea div.pageing")
        links = pager.find_elements(By.CSS_SELECTOR, "a")
        for a in links:
            t = (a.text or "").strip()
            if t == "1":
                safe_click(a)
                sleep_smart(0.4, 0.8)
                break
    except NoSuchElementException:
        pass

def apply_gender_filter(gcode: str):  # 'F' or 'M'
    """
    성별 필터 적용 + 리뷰 리스트 재로딩 대기.
    - label[for='sati_type5_1/2'] 또는 input[name='sati_type5'][value='F/M']
    - 클릭 실패 시 JS 강제 체크 + change 이벤트
    - 적용/검색 버튼을 다양한 셀렉터·텍스트로 시도
    """
    open_filter_panel()

    target_for = "sati_type5_1" if gcode == "F" else "sati_type5_2"
    val = "F" if gcode == "F" else "M"

    # 1) 라벨/인풋 찾기
    label = driver.find_elements(By.CSS_SELECTOR, f"#filterDiv label[for='{target_for}']")
    inp = driver.find_elements(By.CSS_SELECTOR, f"#filterDiv input[name='sati_type5'][value='{val}']")
    if not (label or inp):
        # 백업: 텍스트 기반
        txt = "여성" if gcode == "F" else "남성"
        label = driver.find_elements(By.XPATH, f"//*[@id='filterDiv']//label[contains(., '{txt}')]")

    el = (label[0] if label else (inp[0] if inp else None))
    if not el:
        print(f"⚠️ 성별 라벨/인풋을 못 찾음: {gcode}")
        return

    # 2) 보이게 스크롤
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
    except Exception:
        pass

    # 3) 선택(라벨 → 인풋 → JS 강제)
    try:
        driver.execute_script("arguments[0].click();", el)
        time.sleep(0.2)
    except Exception:
        pass

    if inp:
        radio = inp[0]
        try:
            if not radio.is_selected():
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(0.2)
            if not radio.is_selected():
                driver.execute_script("""
                    const r=arguments[0];
                    r.checked=true;
                    r.dispatchEvent(new Event('change',{bubbles:true}));
                """, radio)
                time.sleep(0.2)
        except Exception:
            pass

    # 4) 적용/검색 버튼 여러 후보 시도
    apply_clicked = False
    apply_candidates = [
        "#filterDiv .btnArea .btnGreen",
        "#filterDiv .btn_area .btnGreen",
        "#filterDiv button.btnGreen",
        "#filterDiv .btn_confirm",
        "#filterDiv button[type='button'].btn_confirm",
        "#filterDiv .btn_srch",
        "#filterDiv .btn_search",
    ]
    for css in apply_candidates:
        try:
            b = driver.find_element(By.CSS_SELECTOR, css)
            if b and b.is_enabled():
                driver.execute_script("arguments[0].click();", b)
                apply_clicked = True
                break
        except Exception:
            continue
    if not apply_clicked:
        try:
            btns = driver.find_elements(By.XPATH, "//*[@id='filterDiv']//button[contains(., '적용') or contains(., '검색')]")
            if btns:
                driver.execute_script("arguments[0].click();", btns[0])
                apply_clicked = True
        except Exception:
            pass

    # 5) 리스트 갱신 대기 + 1페이지 보정
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasList")))
        sleep_smart(0.6, 1.0)
    except TimeoutException:
        pass
    ensure_first_review_page()

# =========================
# 7) 리뷰 크롤링(성별별, 끝까지)
# =========================
def crawl_reviews_for_product(product):
    all_reviews = []
    url = product["product_link"]

    driver.get(url)
    sleep_smart(1.2, 1.8)

    tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#reviewInfo > a")))
    safe_click(tab)
    sleep_smart(0.8, 1.2)

    for gcode, glabel in [("F","여성"), ("M","남성")]:
        try:
            apply_gender_filter(gcode)
        except Exception as e:
            print(f"⚠️ 성별 필터 적용 실패({glabel}): {e}")
            continue

        page_no = 1
        SEEN = set()

        while True:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasList")))
            except TimeoutException:
                print(f"❌ 리뷰 목록 로딩 실패 ({product['product_name']} / {glabel} / p.{page_no})")
                break

            items = driver.find_elements(By.CSS_SELECTOR, "#gdasList > li")

            for it in items:
                try:
                    if it.find_elements(By.CSS_SELECTOR, "div.info > div > p.info_user > a.id"):
                        customer_name = it.find_element(By.CSS_SELECTOR, "div.info > div > p.info_user > a.id").text.strip()
                    else:
                        customer_name = "Anonymous"

                    spans = it.find_elements(By.CSS_SELECTOR, "div.info > div > p.tag > span")
                    span_texts = [s.text.strip() for s in spans if s.text.strip()]
                    skin_type_val, skin_tone_val, skin_concerns_val = split_skin_tags(span_texts)

                    review_text = ""
                    if it.find_elements(By.CSS_SELECTOR, "div.review_cont > div.txt_inner"):
                        review_text = it.find_element(By.CSS_SELECTOR, "div.review_cont > div.txt_inner").text.strip()

                    date = "N/A"
                    if it.find_elements(By.CSS_SELECTOR, "div.review_cont > div.score_area > span.date"):
                        date = it.find_element(By.CSS_SELECTOR, "div.review_cont > div.score_area > span.date").text.strip()

                    rating_text, rating_val = "", ""
                    rt = it.find_elements(By.CSS_SELECTOR, "div.review_cont > div.score_area > span.review_point > span")
                    if rt:
                        rating_text = (rt[0].get_attribute("title") or rt[0].text or "").strip()
                        parsed = parse_rating_to_float(rating_text)
                        rating_val = parsed if parsed is not None else ""

                    sig = (customer_name, date, review_text, glabel)
                    if sig in SEEN:
                        continue
                    SEEN.add(sig)

                    all_reviews.append({
                        "customer_name": customer_name,
                        "skin_type": skin_type_val,
                        "skin_tone": skin_tone_val,
                        "skin_concerns": skin_concerns_val,
                        "review": review_text,
                        "date": date,
                        "rating_text": rating_text,
                        "rating": rating_val,
                        "gender": glabel,
                    })
                except (StaleElementReferenceException, Exception):
                    continue

            # 다음 페이지
            try:
                pager = driver.find_element(By.CSS_SELECTOR, "#gdasContentsArea div.pageing")
                links = pager.find_elements(By.CSS_SELECTOR, "a")
            except NoSuchElementException:
                break

            next_clicked = False
            for a in links:
                t = (a.text or "").strip()
                if t.isdigit():
                    try:
                        if int(t) == page_no + 1:
                            if safe_click(a):
                                sleep_smart(0.7, 1.1)
                                page_no += 1
                                next_clicked = True
                            break
                    except:
                        pass
            if not next_clicked:
                for a in links:
                    label = (a.get_attribute("aria-label") or a.text or "").strip()
                    if "다음" in label or "next" in label.lower():
                        if safe_click(a):
                            sleep_smart(0.7, 1.1)
                            page_no += 1
                            next_clicked = True
                        break
            if not next_clicked:
                break

    return all_reviews

# =========================
# 8) 메인
# =========================
try:
    print("▶ 상품 목록 수집 시작")
    products = crawl_product_list()

    if MAX_PRODUCTS is not None:
        products = products[START_AT: START_AT + MAX_PRODUCTS]
    elif START_AT:
        products = products[START_AT:]

    print(f"총 수집 대상 상품 수: {len(products)}")
    write_product_list_csv(products, PRODUCT_LIST_CSV)
    print(f"상품 리스트 저장: {PRODUCT_LIST_CSV}")

    init_reviews_csv(CSV_PATH)

    for idx, product in enumerate(products, 1):
        print(f"\n🔍 ({idx}/{len(products)}) 리뷰 크롤링: {product['product_name']}")
        try:
            rs = crawl_reviews_for_product(product)
        except (InvalidSessionIdException, WebDriverException) as e:
            print(f"⚠️ 드라이버 오류 → 재생성 후 재시도: {e}")
            recreate_driver()
            try:
                rs = crawl_reviews_for_product(product)
            except Exception as e2:
                print(f"❌ 재시도 실패: {e2}")
                continue
        append_reviews_to_csv(product, rs, CSV_PATH)
        print(f"  ↳ 수집 리뷰 수: {len(rs)}")
        sleep_smart(2.0, 3.5)

    print(f"\n✅ 완료! 리뷰 CSV 저장: {CSV_PATH}")

finally:
    try:
        driver.quit()
    except:
        pass
    print("브라우저 종료")
