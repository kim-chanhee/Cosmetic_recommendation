# 실행 가이드

## 1. 환경 준비

프로젝트 루트에서 실행합니다. Python 3.11 이상과 Java가 필요합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --prefix .venv --name cosmetics --display-name "Python (cosmetics)"
JUPYTER_PATH="$PWD/.venv/share/jupyter" python -m jupyter lab
```

노트북 커널은 `Python (cosmetics)`를 선택하세요. 이번 검증용 `.venv`는 기존 시스템 패키지를 공유하여 만들었지만 새 환경은 위와 같이 독립적으로 설치할 수 있습니다. macOS에서 Java를 찾지 못하면 `JAVA_HOME`을 설치된 JDK로 설정하세요.

코드 셀에서 패키지를 자동 설치하지 않습니다. 최초 KoBERT 실행 시 캐시가 없으면 인터넷 다운로드가 필요합니다. 이후 리뷰 벡터는 `outputs/cache/kobert/`에서 재사용합니다.

## 2. 실행 순서

| 순서 | 파일 | 역할 |
|---|---|---|
| 선택 | `code/01_크롤링/crawl_reviews.py` | 새 리뷰 수집. 실행 시 원본 리뷰 CSV를 초기화하므로 기존 데이터를 사용할 때는 생략 |
| 1 | `code/02_데이터 전처리/preprocess_reviews.ipynb` | 정제, 피부 타입 보완, Komoran 명사 추출, `review_id` 생성 |
| 2 | `code/03_감성분석/analyze_sentiment.ipynb` | 사전 분석, 사용자 단위 교차 검증, OOF 감성 점수 저장 |
| 3 | `code/04_추천시스템/recommend_products.ipynb` | ID 병합, KoBERT, SVD, 피부 필터, 실제 추천·그림·평가 |

각 노트북의 설명을 읽고 위에서 아래로 실행하세요. 코드는 프로젝트 내부에서 현재 폴더의 상위 경로를 탐색해 루트를 찾습니다. 결과 파일은 단계별로 덮어씁니다.

## 3. 추천 설정

추천 노트북의 첫 설정 셀에서 다음 항목을 수정합니다.

- `USER_ID`: 추천할 사용자명. 기본값 `vwaaang`; 미등록 사용자는 인기순 추천.
- `TOP_K`: 추천 개수. 기본 10. 후보가 적으면 그보다 적게 반환.
- `CONTENT_WEIGHT`: 콘텐츠 점수 비중. 기본 0.5. 콘텐츠 이력이 없으면 협업 점수만 사용.
- `SKIN_THRESHOLD`: 알려진 피부 정보가 있는 리뷰 중 해당 특성의 최소 비율. 기본 0.1.
- `EMBEDDING_BATCH_SIZE`: GPU 메모리가 부족하면 낮춥니다.

KoBERT는 긴 리뷰를 조각으로 나누어 전부 처리합니다. 최초 임베딩 생성은 시간이 걸릴 수 있습니다. 캐시 키에는 전체 입력과 모델 버전·임베딩 정책이 포함됩니다.

Surprise가 있으면 SVD를 사용하고, 없으면 관측 평점만 학습하는 PyTorch 잠재요인 모델을 사용합니다. 사용한 구현은 `run_info.json`에 기록됩니다.

## 4. 결과물

| 경로 | 내용 |
|---|---|
| `outputs/data/processed/Ntoken_review.csv` | 정제 리뷰·피부 추정 여부·고유 ID |
| `outputs/data/sentiment/senti_labeled_df.csv` | ID별 사전 점수·OOF 확률·감성 점수·폴드 |
| `outputs/data/recommendation/merged_output.csv` | 검증된 추천 입력 |
| `outputs/data/recommendation/recommendations.csv` | 실제 사용자별 추천 표, 점수 내역·필터 상태 |
| `outputs/data/recommendation/recommendations_by_skin_type.csv` | 피부 타입별 Top 10 집단 추천, 점수 내역·피부 리뷰 비율 |
| `outputs/reports/recommendation/skin_type_summary.csv` | 타입별 사용자 수·콘텐츠 프로필 수·후보 수·실제 추천 수 |
| `outputs/reports/preprocessing/summary.json` | 제거·정제·피부 보완 통계 |
| `outputs/reports/sentiment/metrics.json` | 사전 coverage, 감성 교차 검증 성능 |
| `outputs/reports/recommendation/run_info.json` | 추천 설정·사용 모델·피부 프로필 |
| `outputs/reports/recommendation/ranking_metrics.csv` | 인기순·평균 평점·콘텐츠·협업·하이브리드 비교 |
| `outputs/reports/recommendation/evaluation_info.json` | 평가 분할·사용자 수·후보 정답 포함률 |
| `outputs/figures/` | 실제 실행 데이터로 만든 단계별 그래프 |

`outputs/figures/recommendation/variants/`는 수정 전 디자인 변형본입니다. 현재 추천 결과를 표시하지 않습니다. 원본 10개 제품 그래프 파일명은 기존 참조와의 호환을 위해 유지하지만 실제 제품과 개수는 추천 CSV에서 가져옵니다.

그래프만 다시 생성하려면:

셀 단위로 데이터·비율·그래프를 확인하려면
`code/05_시각화/plot_skin_ratio.ipynb`를 위에서 아래로 실행하세요.
기본 실행은 타입별 누적 리뷰 비율 이미지를 만들며, 7단계에서 미리 볼 타입을
선택합니다. 8·9단계의 옵션으로 추천 점수 그림과 개인 추천 그림도 생성할 수 있습니다.

스크립트 실행:

```bash
python code/05_시각화/plot_skin_ratio.py
```

추천 노트북의 8단계는 피부 타입별 추천 CSV도 생성합니다. 새 Figure 3은
`outputs/figures/recommendation/figure3_skin_type_top10_recommendations.png`이며,
타입별 300dpi 이미지는 같은 폴더의 `by_skin_type/`에 저장됩니다.
원본 Figure 3처럼 각 추천 상품의 피부 타입별 리뷰 비율을 쌓아 표시한
300dpi 이미지는 `by_skin_type_review_ratio/figure3_review_ratio_*.png`입니다.
각 파일의 추천 대상 타입은 제목에 표시하며, 색상은 그 상품에 달린 전체 리뷰의
피부 타입 구성비입니다. 미상 리뷰도 분모에 포함하므로 각 막대의 합은 1입니다.
기존 `figure3_skin_ratio_top10_products.png`는 개인 추천 상품들의 리뷰 구성비입니다.

피부 타입별 추천은 사용자의 최신 유효 타입으로 집단을 만들고, 구성원들의
콘텐츠 유사도와 협업 예측을 각각 동일 비중으로 평균한 뒤 `CONTENT_WEIGHT`로
결합합니다. 콘텐츠 프로필이 없는 구성원은 콘텐츠 평균에서 제외합니다.
타입에 알려진 리뷰 비율이 `SKIN_THRESHOLD` 이상인 상품만 후보가 되며,
피부 톤·고민으로 후보를 늘리거나 후보 부족 시 필터를 완화하지 않습니다.
미상 타입은 제외하고, 집단 추천에는 구성원이 이미 리뷰한 상품도 포함합니다.
타입별 후보 안에서 정규화하므로 타입 간 점수 크기를 직접 비교하지 마세요.

## 5. 검증과 해석

```bash
python -m unittest discover -s tests -v
```

감성 라벨은 **1=긍정, 0=부정**, `sentiment_score`는 `2 * positive_probability - 1`입니다. 평점 4점 이상을 긍정 정답으로 사용하는 대리 평가입니다.

추천 평가는 사용자별 마지막 제품의 모든 리뷰를 보류하고 학습 데이터만으로 모델·제품 벡터·피부 비율을 재구성합니다. 전체 평점으로 만든 감성 OOF 값이 평가 정답을 간접 전달하지 않도록 **평가에서는 감성 보정을 끕니다**. 따라서 평가 수치는 감성 보정까지 포함한 최종 운영 모델의 성능이 아닙니다. 전역 시간순 미래 예측 검증도 아닙니다.

## 6. 변경 전 자료

- `.backups/before_organization.zip`: 폴더 정리 이전 전체 파일.
- `.backups/before_pipeline_fixes.zip`: 이번 로직 수정 직전 코드·데이터·이미지.
- `docs/file_moves.csv`: 최초 파일 이동 기록(해시는 당시 원본 기준).
- `docs/stages/`, `docs/archive/`: 수정 전 설명 문서. 현재 실행 안내는 이 문서를 따릅니다.
