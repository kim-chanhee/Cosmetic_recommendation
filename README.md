# Cosmetic_recommendation

📝 화장품 추천 시스템: 데이터 전처리 파이프라인
개인별 피부 특성(타입, 톤, 고민)에 최적화된 화장품을 추천하기 위한 데이터 전처리 프로젝트입니다. 올리브영 웹사이트의 리뷰 데이터를 수집하고 자연어 처리 기술을 적용하여 추천 모델이 사용할 수 있는 정제된 데이터셋을 구축합니다.

✨ 주요 기능 (Features)
- 웹 크롤링: Selenium을 활용하여 동적 웹사이트의 리뷰 데이터를 안정적으로 수집합니다.
- 텍스트 정제: 정규식을 사용하여 한글, 영어, 숫자 외 불필요한 문자를 제거하고 텍스트를 표준화합니다.
- 한국어 형태소 분석: Konlpy를 이용해 리뷰 텍스트를 토큰화하고, 명사, 동사, 형용사 등 핵심 품사만 추출합니다.
- 감성 분석: KNU 한국어 감성 사전을 기반으로 각 리뷰의 긍정/부정 레이블을 생성하여 데이터의 활용도를 높입니다.

🛠️ 기술 스택 (Tech Stack)
- Language: Python 3.x
- Crawling: Selenium, BeautifulSoup
- Data Handling: Pandas, Numpy
- NLP: Konlpy, Scikit-learn
- Visualization: Matplotlib, WordCloud

📂 프로젝트 파일 구조
.
├── 여드름_크림_crawling.py       # 1. 올리브영 리뷰 데이터 수집 스크립트
├── 전처리.ipynb                      # 2. 데이터 정제 및 토큰화 노트북
├── 감성사전구축3_KNU.ipynb         # 3. 감성 분석 및 레이블링 노트북
├── 3.추천.ipynb                      # 4. 데이터 병합 및 추천 모델링 노트북
├── combined_pos_words.txt          # KNU 긍정 감성 사전
├── combined_neg_words.txt          # KNU 부정 감성 사전
├── senti_labeled_df.csv            # [결과물] 감성 분석 완료 데이터
└── merged_output.csv               # [최종 결과물] 모든 전처리 완료 데이터

🚀 실행 방법 (How to Run)
1. 사전 준비
프로젝트 실행에 필요한 라이브러리를 설치합니다.

pip install pandas selenium konlpy scikit-learn wordcloud matplotlib

2. 데이터 처리 파이프라인
아래 순서에 따라 각 스크립트와 노트북을 실행합니다.

1️⃣ 단계: 데이터 수집

여드름_크림_crawling.py를 실행하여 올리브영에서 원시 리뷰 데이터를 수집합니다.

결과: 상품별 리뷰가 담긴 다수의 .csv 파일이 생성됩니다.

2️⃣ 단계: 데이터 정제 및 토큰화

전처리.ipynb 노트북을 실행합니다.

프로세스:

1단계에서 생성된 .csv 파일들을 하나로 통합합니다.

결측치 처리, 텍스트 정제, 형태소 분석 및 불용어 제거를 수행합니다.

결과: 토큰화된 키워드가 포함된 중간 결과 파일이 생성됩니다.

3️⃣ 단계: 감성 분석

감성사전구축3_KNU.ipynb 노트북을 실행합니다.

프로세스:

combined_pos_words.txt와 combined_neg_words.txt 사전을 사용합니다.

토큰화된 리뷰를 기반으로 감성 점수를 계산하고 긍정(1)/부정(0) 레이블을 부여합니다.

결과: senti_labeled_df.csv 파일이 생성됩니다.

4️⃣ 단계: 최종 데이터 병합

3.추천.ipynb 노트북의 초반부 셀을 실행하여 최종 데이터를 생성합니다.

프로세스: 2단계의 정제된 데이터와 3단계의 감성 분석 결과를 병합합니다.

결과: 모델링에 사용할 최종 데이터셋인 merged_output.csv가 생성됩니다.

📊 최종 데이터셋 구조 (merged_output.csv)

