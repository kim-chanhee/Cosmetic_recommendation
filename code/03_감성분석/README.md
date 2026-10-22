# Sentiment Analysis

텍스트 리뷰의 긍정·부정 감정을 분석하고, 원래 평점에 감성 정보를 반영합니다.

![감성 분석과 평점 보정 과정](../assets/sentiment-analysis.png)

## 분석 흐름

리뷰 본문과 원래 평점을 준비한 뒤 감성 사전을 이용한 규칙 기반 분석을 수행합니다. TF-IDF 벡터화와 로지스틱 회귀 모델로 리뷰의 긍정 확률을 추정하고, 감성 점수를 평점 보정에 활용합니다.

현재 구현에서는 `sentiment_score = 2 × positive_probability - 1`을 사용합니다. 긍정 라벨은 1, 부정 라벨은 0입니다. 작성자 단위 교차 검증의 OOF 결과를 저장하며, 학습 정답은 평점 4점 이상 여부를 사용한 대리 라벨입니다.

## 구현

[analyze_sentiment.ipynb](analyze_sentiment.ipynb)에서 분석합니다.

- 입력: [전처리 리뷰](../../outputs/data/processed/Ntoken_review.csv)
- 출력: [감성 결과](../../outputs/data/sentiment/senti_labeled_df.csv)
- 평가: [감성 평가 리포트](../../outputs/reports/sentiment/metrics.json)

[전체 구현 안내](../README.md) · [다음 단계 추천시스템](../04_추천시스템/README.md)
