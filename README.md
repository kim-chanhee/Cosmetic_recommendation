# KoBERT–SVD Hybrid Cosmetic Recommendation

### 사용자 감성과 피부 특성을 반영한 개인화 화장품 추천

화장품은 같은 제품이라도 사용자의 피부 타입과 고민에 따라 만족도가 달라집니다. 이 프로젝트는 평점뿐 아니라 **리뷰에 담긴 감정**, **리뷰 문맥**, **사용자의 피부 정보**를 함께 활용하는 하이브리드 추천 시스템을 구현합니다.

KoBERT는 한국어 리뷰의 의미를 표현하고, SVD 기반 협업 필터링은 사용자와 상품 사이의 선호 패턴을 학습합니다. 두 모델의 점수를 결합해 사용자에게 맞는 상품의 순위를 제공합니다.

[구현 과정 살펴보기](code/README.md) · [실행 방법](docs/RUNNING.md) · [추천 노트북](code/04_추천시스템/recommend_products.ipynb) · [연구 발표 PDF](docs/KoBERT-SVD_발표자료.pdf)

## Research Background

기존의 평점·구매 이력 중심 추천만으로는 리뷰에 드러나는 감성이나 피부 타입·톤·고민을 충분히 반영하기 어렵습니다. 본 연구는 감성 분석과 피부 프로필을 결합해 기능성 화장품의 개인화 추천을 지원하는 것을 목표로 합니다.

## Research Framework

![화장품 리뷰 수집부터 최종 추천까지의 연구 프레임워크](docs/assets/research-overview.png)

| 단계 | 내용 |
|---|---|
| Data Preprocessing | 리뷰 중복 제거, 피부 정보 추출, Komoran 형태소 분석 |
| Sentiment Analysis | 감성 사전과 TF-IDF·로지스틱 회귀를 통한 감성 점수 생성 |
| Skin Profile Filtering | 피부 타입·톤·고민을 바탕으로 추천 후보 선정 |
| SVD Collaborative Filtering | 감성 정보를 반영한 평점으로 사용자·상품 선호 패턴 학습 |
| KoBERT Content Filtering | 리뷰 임베딩과 코사인 유사도로 문맥 기반 선호도 계산 |
| Hybrid Integration | 두 점수를 가중 결합해 Top N 상품 추천 |

올리브영에서 수집한 리뷰 12,347개 중 최종 11,795개를 분석에 활용합니다. 구현의 입력·출력과 단계별 이미지는 [code 폴더](code/README.md)에 정리했습니다.

## Recommendation Example

![연구에서 제시한 화장품 Top 10 추천 예시](docs/assets/recommendation-example.png)

연구에서 제시한 추천 예시입니다. `item_id`는 상품, `final_score`는 두 모델의 점수를 결합한 추천 순위 점수입니다. 점수는 예측 정확도나 피부 적합 확률을 뜻하지 않습니다.

현재 코드는 입력과 실행 설정에 따라 결과를 다시 계산하므로 위 예시와 순위가 다를 수 있습니다. [현재 개인 추천 결과](outputs/data/recommendation/recommendations.csv)와 [피부 타입별 추천 결과](outputs/data/recommendation/recommendations_by_skin_type.csv)를 함께 제공합니다.

## Explore the Implementation

| 단계 | 설명과 코드 |
|---|---|
| 01 | [크롤링](code/01_크롤링/README.md) |
| 02 | [데이터 전처리](<code/02_데이터 전처리/README.md>) |
| 03 | [감성분석](code/03_감성분석/README.md) |
| 04 | [추천시스템](code/04_추천시스템/README.md) |
| 05 | [시각화](code/05_시각화/README.md) |

## Future Research

성분 정보·피부 시험 결과·실시간 피드백을 결합하는 멀티모달 확장, 실제 사용자 연구와 A/B 테스트, 다양한 피부 타입·연령·문화권으로의 적용 범위 확대를 향후 연구 방향으로 삼습니다.

**Keywords** · Sentiment Analysis · Hybrid Recommendation · SVD · KoBERT

## 논문과 발표자료

- 논문: [PDF](docs/논문/SCI2025-016_Original_Layout_Corrected.pdf) · [Word](docs/논문/SCI2025-016_Original_Layout_Corrected.docx)
- 발표자료: [PDF](docs/KoBERT-SVD_발표자료.pdf)
