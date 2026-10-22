# 리뷰 수집

올리브영 상품 리뷰에서 추천에 사용할 리뷰 본문, 별점, 작성자와 피부 정보를 수집합니다.

[전체 코드 안내](../README.md) · 다음 단계 [데이터 전처리](<../02_데이터 전처리/README.md>)

## 수집하는 정보

![리뷰 데이터의 주요 항목](../assets/review-data-columns.png)

상품·사용자 식별 정보와 피부 타입·피부 톤·피부 고민, 리뷰, 평점을 수집합니다. 이 정보는 이후 피부 필터링, 리뷰 의미 분석, 협업 모델의 입력이 됩니다. 이미지의 `item_id`와 `user_id`는 추천 단계의 명칭이며, 수집 CSV에서는 `product_name`과 `customer_name`으로 저장합니다.

| 입력 | 출력 |
|---|---|
| 올리브영 상품 리뷰 페이지 | [`outputs/data/raw/acne_cream_reviews.csv`](../../outputs/data/raw/acne_cream_reviews.csv) |

## 실행 파일

[crawl_reviews.py](crawl_reviews.py)를 사용합니다. 수집 대상과 실행 환경을 확인한 뒤 프로젝트 루트에서 실행하세요.

```bash
.venv/bin/python code/01_크롤링/crawl_reviews.py
```

스크립트 실행 시 원본 리뷰 CSV가 초기화됩니다. 이미 저장된 데이터를 분석할 때는 이 단계를 생략하고 전처리 노트북부터 실행하세요.
