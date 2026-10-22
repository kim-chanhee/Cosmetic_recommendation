# 화장품 리뷰 기반 추천 프로젝트

올리브영 리뷰를 수집·정제하고 감성 분석, KoBERT 콘텐츠 유사도, SVD 협업 필터링, 피부 정보 필터를 결합해 추천합니다.

## 코드 순서

1. `code/01_크롤링/crawl_reviews.py` — 원본 리뷰 수집(기존 CSV 사용 시 생략).
2. `code/02_데이터 전처리/preprocess_reviews.ipynb` — 정제·명사 추출·리뷰 ID 생성.
3. `code/03_감성분석/analyze_sentiment.ipynb` — 사전 분석·TF-IDF/Logistic Regression 교차 검증.
4. `code/04_추천시스템/recommend_products.ipynb` — 안전한 감성 병합·하이브리드 추천·실제 결과·성능 비교.
5. `code/05_시각화/plot_skin_ratio.ipynb` — 셀별 리뷰 비율 계산·타입별 그래프 생성·미리보기. 스크립트 실행은 같은 폴더의 `plot_skin_ratio.py` 사용.

각 노트북은 단계 제목·입출력 설명·정책 주석을 포함합니다. 공통 ID·병합 검증 규칙은 `code/common/project_utils.py`에 있습니다.

## 폴더

원본 GitHub 저장소의 한글 단계명을 반영했습니다.

```text
code/
├── 01_크롤링/
├── 02_데이터 전처리/
├── 03_감성분석/
├── 04_추천시스템/
├── 05_시각화/
└── common/
```

- `code/`: 단계별 코드와 공통 검증 함수.
- `outputs/data/`: 원본, 전처리, 감성, 추천 입력·결과 CSV.
- `outputs/figures/`: 실제 데이터 그래프. `recommendation/variants/`는 이전 디자인 자료.
- `outputs/reports/`: 실행 설정, 통계, 감성·추천 평가 결과.
- `outputs/cache/`: KoBERT 리뷰 임베딩 캐시.
- `resources/`: 공식 KNU 감성 사전·출처와 선택적 전처리 사전.
- `tests/`: 핵심 오류 회귀 테스트.
- `docs/`: 실행 방법·수정 내역·이전 단계 설명·파일 이동 기록.
- `.backups/`: 정리 전 및 로직 수정 전 전체 백업.

## 실행과 결과 확인

[실행 가이드](docs/RUNNING.md)를 따라 전처리 → 감성 → 추천 노트북을 순서대로 실행합니다. 설치 패키지는 `requirements.txt`에 있고 Java가 별도로 필요합니다. 사용자와 추천 가중치는 추천 노트북 첫 설정 셀에서 지정합니다.

추천 표는 `outputs/data/recommendation/recommendations.csv`, 그래프는 `outputs/figures/recommendation/`에 저장됩니다. 고정된 상품·점수를 출력하지 않습니다. 감성 라벨은 1=긍정, 0=부정으로 통일했고 결측 피부 정보는 필터 조건에서 제외합니다.

감성 정답은 평점 기반 대리 라벨입니다. 추천 평가는 감성 보정을 끈 사용자별 보류 실험이며 운영 모델 전체 성능으로 해석하지 않습니다. 검증 결과와 한계는 [수정 내역](docs/CHANGES.md)에 기록합니다.

## 연구 발표자료

[KoBERT SVD 발표자료와 이미지 설명](docs/발표자료/KoBERT-SVD/README.md)에서 원본 PDF, 추출 이미지, 슬라이드별 설명을 확인할 수 있습니다.
