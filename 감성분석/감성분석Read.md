<파일 설명>

1. 📘 감성사전구축3_KNU.ipynb – 감성사전 구축 과정이 담긴 주피터 노트북입니다.
- KNU 감성 사전을 기반으로 긍정/부정 어휘를 분류 및 확장한 프로젝트 코드로 보입니다.
- 형태소 분석, 감성 점수 부여, 사전 구축 및 시각화 등의 절차가 포함되어 있을 가능성이 높습니다.

2. 📄 combined_pos_words.txt / combined_neg_words.txt 
- 각각 긍정 단어, 부정 단어 목록으로, 감성사전구축3_KNU.ipynb의 최종 산출물(lexicon output)에 해당합니다.
- 긍정 단어(예: “훌륭하다”, “행복하다”, “감사하다”)와 부정 단어(예: “슬프다”, “불편하다”, “괴롭다”)로 이루어져 있습니다.
- KNU 사전 기반의 감성분석 모델에서 리뷰 텍스트의 감정 점수를 계산할 때 활용됩니다.

3. 📊 senti_labeled_df.csv 
- 감성 분석 결과가 포함된 데이터셋으로, 리뷰 텍스트별로 pred(감성 점수) 컬럼이 존재합니다.
- 이 파일은 combined_pos_words / combined_neg_words를 기반으로 문장별 긍·부정 단어 출현 비율 혹은 감성점수를 계산한 결과물입니다.


# 📄 감성사전 구축 및 리뷰 감성분석

### 1. 개요
이 코드는 한국어 리뷰 데이터(특히 화장품 리뷰)에 내재된 감정적 의미를 자동으로 분석하기 위해 **감성사전(KNU 기반)**을 구축하고, 각 문장의 감정 점수를 계산하는 전 과정을 자동화한 것이다.
핵심 목표는 다음과 같다:
- 한국어 감성 어휘를 긍정/부정으로 구분 및 정제
- 리뷰 문장에서 감정 단어를 탐색하여 감성 점수 산출
- 결과를 구조화된 형태(senti_labeled_df.csv)로 저장하여 후속 분석에 활용
---
### 2. 전체 흐름 요약 6단계

| 단계              | 주요 목적                | 주요 산출물                                             |
| --------------- | -------------------- | -------------------------------------------------- |
| ① 데이터 로드 및 환경설정 | KNU 감성사전 및 텍스트 파일 로드 | 원시 감성어 리스트                                         |
| ② 감정어 정제 및 분류   | 긍정·부정 어휘 필터링 및 중복 제거 | 정제된 감성어 리스트                                        |
| ③ 감정어 통합 및 확장   | 긍·부정 통합 사전 구축        | `combined_pos_words.txt`, `combined_neg_words.txt` |
| ④ 감성 점수 산출      | 리뷰 텍스트별 감성 스코어 계산    | 감정 점수(`pred`) 컬럼                                   |
| ⑤ 결과 저장 및 검증    | CSV 형태로 결과 저장        | `senti_labeled_df.csv`                             |
| ⑥ 통계적 분석 및 시각화  | 감성 분포, 주요 단어 빈도 분석   | 긍/부정 분포 시각 자료                                      |
---
### 3. 데이터 및 사전 구성 

사용된 리뷰 데이터의 레이블 분포와 감성 사전의 기본 구조를 제시한다.
감성 사전은 KNU 기반 긍·부정 어휘를 통합한 combined_pos_words.txt와 combined_neg_words.txt로 구성되어 있으며,
긍정(0)과 부정(1)의 비율을 시각화하면 다음과 같다.

<0 = pos, 1 = neg>

<img width="384" height="284" alt="image" src="https://github.com/user-attachments/assets/9e5e27ff-cea4-401c-94dc-6ef2609e3976" />

---


### 4. 감성 점수 산출
이 단계에서는 두 가지 방식으로 감성을 분류하였다.
첫째는 사전(Lexicon) 기반 규칙형 접근이고,
둘째는 머신러닝(ML) 기반 학습형 접근이다.
두 접근의 혼동행렬(confusion matrix)을 비교하여 각 방식의 강점과 한계를 분석하였다.

🧾 < 사전 기반 감성 분석의 실제 >

<img width="304" height="284" alt="image" src="https://github.com/user-attachments/assets/79e240ce-b535-493f-867b-9a6620d2f989" />

True Positive(긍정 정확도)는 높지만 False Negative(부정 누락)가 다수 발생한다.

🧠 < ML 모델 성능 비교 >

<img width="304" height="284" alt="image" src="https://github.com/user-attachments/assets/bae7909d-5414-4e0f-b72f-c9a8d8b0ba85" />

머신러닝 모델(Logistic Regression, TF-IDF 벡터 기반)은 부정 리뷰 검출률이 개선되었다.
Lexicon 대비 Recall 향상 효과가 크며, 실제 감정 분류의 분포가 현실적이다.
단, 긍정 데이터 과다로 인한 Precision 손실이 일부 존재한다.

---

### 5. 통계 분석 및 시각화 

모델 성능을 정량적으로 평가하기 위해 ROC 및 PR 곡선을 분석하였다.
두 지표 모두 분류기의 전체적 판별력과 불균형 데이터에서의 효율성을 평가하는 핵심 수단이다.

📈 < ROC (ML) >

<img width="384" height="284" alt="image" src="https://github.com/user-attachments/assets/733c46d5-149b-426d-a9ba-c28b0a5bc2bd" />

ROC 곡선은 True Positive Rate과 False Positive Rate의 관계를 나타내며,
AUC=0.848로 모델의 전반적 분류 성능이 우수함을 확인할 수 있다.
랜덤 분류선(주황색 점선) 대비 안정적인 판별 경향을 보인다.


📉 < Precision-Recall Curve >

<img width="384" height="284" alt="image" src="https://github.com/user-attachments/assets/b6d7213b-f8e3-4c9d-abc6-bfefacf70395" />

Precision-Recall 곡선은 불균형 데이터에서 더 유용한 지표로,
Average Precision(AP)은 0.345로 측정되었다.
이는 모델이 부정 리뷰를 탐지할 때 정밀도는 다소 낮지만,
재현율(Recall)을 유지하며 긍정 편향을 완화함을 의미한다.
