#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화장품 리뷰 데이터 전처리 스크립트
전처리(1).ipynb를 파이썬 스크립트로 변환

주요 기능:
1. CSV 파일 통합 및 데이터 정제
2. 피부타입 자동 추출
3. 형태소 분석 및 토큰화
4. N-gram 생성 및 불용어 제거
5. 최종 데이터 저장
"""

import os
import glob
import re
import pandas as pd
import numpy as np
from collections import Counter
from konlpy.tag import Komoran
import warnings
warnings.filterwarnings('ignore')

def setup_paths():
    """경로 설정"""
    # 현재 스크립트의 디렉토리를 기준으로 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_directory = os.path.join(current_dir, '피부 질환 화장품 데이터', '크림')
    
    return csv_directory

def load_and_merge_csv_files(csv_directory):
    """CSV 파일들을 로드하고 통합"""
    print("=== CSV 파일 로드 및 통합 ===")
    
    # CSV 파일 경로 수집
    csv_files = glob.glob(os.path.join(csv_directory, '*.csv'))
    print(f"총 {len(csv_files)}개의 CSV 파일을 찾았습니다.")
    
    # 각 CSV 파일에 product_name 열 추가
    for file_path in csv_files:
        product_name = os.path.basename(file_path).replace('.csv', '')
        df_temp = pd.read_csv(file_path)
        
        # 이미 product_name 열이 있으면 값을 갱신, 없으면 추가
        if 'product_name' in df_temp.columns:
            df_temp['product_name'] = product_name
        else:
            df_temp.insert(0, 'product_name', product_name)
        
        df_temp.to_csv(file_path, index=False)
        print(f"처리 완료: {product_name}")
    
    print("모든 파일에 product_name 열이 정상적으로 추가(또는 갱신)되었습니다.")
    
    # 모든 파일을 읽어서 하나의 데이터프레임으로 합치기
    df_list = []
    for file_path in csv_files:
        df_temp = pd.read_csv(file_path)
        df_list.append(df_temp)
    
    df = pd.concat(df_list, ignore_index=True)
    
    # 원하는 열만 남기고 나머지는 삭제
    columns_to_keep = ['product_name', 'id', 'tag', 'tag 2', 'tag 3', 'tag 4', 'point_flag', 'point', 'date', 'txt_inner']
    df = df[columns_to_keep]
    
    return df

def clean_data(df):
    """데이터 정제"""
    print("\n=== 데이터 정제 ===")
    
    # 평점 형식 변경 (5점 만점에 5점 -> 5)
    df['point'] = df['point'].str.extract(r'(\d+)점$')[0]
    
    # 컬럼명 변경
    df = df.rename(columns={
        'id': 'reviewer_id',
        'tag': 'skin_type',
        'tag 2': 'skin_tone',
        'tag 3': 'skin_concern_1',
        'tag 4': 'skin_concern_2',
        'point_flag': 'usage_period_flag',
        'more_msg': 'review_note',
        'point': 'rating',
        'date': 'review_date',
        'txt_inner': 'review',
    })
    
    print(f"데이터 크기: {df.shape}")
    print("컬럼 정보:")
    print(df.info())
    
    # 중복 제거
    df = df.drop_duplicates(['review'])
    df = df.reset_index(drop=True)
    
    # 불필요한 컬럼 삭제
    cols_to_drop = ['usage_period_flag']
    df = df.drop(cols_to_drop, axis=1)
    
    # review NaN인 행 제거
    df = df.dropna(subset=['review'])
    
    # 한글만 추출하는 함수
    def extract_word(text):
        hangul = re.compile('[^ ㄱ-ㅣ가-힣]+')
        result = hangul.sub(' ', text)
        return result
    
    # 한글만 남기고 review 컬럼에 적용
    df['review'] = df['review'].apply(extract_word)
    
    # 공백을 모두 제거한 토큰 컬럼 생성
    df['tokens'] = df['review'].str.replace(' ', '', regex=False)
    
    # tokens가 빈 문자열인 행 제거
    df = df[df['tokens'].str.len() > 0].reset_index(drop=True)
    
    # NaN -> None
    df['skin_type'] = df['skin_type'].fillna('None')
    
    print(f"정제 후 데이터 크기: {df.shape}")
    print("피부타입 분포:")
    print(df['skin_type'].value_counts())
    
    return df

def advanced_skin_type_extraction(df):
    """피부타입 자동 추출"""
    print("\n=== 피부타입 자동 추출 ===")
    
    if "skin_type" not in df.columns:
        df["skin_type"] = "None"
    
    TYPE_GROUP = r"(건성|지성|복합성|민감성|수부지|약건성|중성|트러블성)"
    patterns = [
        re.compile(rf"저는\s*{TYPE_GROUP}"),
        re.compile(rf"전\s*{TYPE_GROUP}"),
        re.compile(rf"피부가\s*{TYPE_GROUP}"),
        re.compile(rf"{TYPE_GROUP}\s*피부"),
        re.compile(rf"{TYPE_GROUP}"),
    ]
    
    def _to_text(x):
        if isinstance(x, (list, tuple)):
            parts = []
            for item in x:
                if isinstance(item, (list, tuple)) and len(item) > 0:
                    parts.append(str(item[0]))  # (token, pos) → token
                else:
                    parts.append(str(item))
            return " ".join(parts)
        return "" if pd.isna(x) else str(x)
    
    def extract_from_text(text):
        s = "" if pd.isna(text) else str(text)
        for p in patterns:
            m = p.search(s)
            if m:
                val = m.group(m.lastindex or 1)
                return "지성" if val == "수부지" else val
        return "None"
    
    # 대상: None 값인 행만
    mask = df["skin_type"].astype(str).str.strip().eq("None")
    
    # 1) review에서 추출
    if "review" in df.columns:
        df.loc[mask, "skin_type"] = df.loc[mask, "review"].apply(extract_from_text)
    
    # 2) 여전히 None이면 tokens에서 추출
    mask = df["skin_type"].astype(str).str.strip().eq("None")
    if "tokens" in df.columns:
        df.loc[mask, "skin_type"] = df.loc[mask, "tokens"].apply(lambda x: extract_from_text(_to_text(x)))
    
    print("피부타입 자동 추출 후 분포:")
    print(df['skin_type'].value_counts())
    
    return df

def tokenize_and_analyze(df):
    """형태소 분석 및 토큰화"""
    print("\n=== 형태소 분석 및 토큰화 ===")
    
    # Komoran 초기화 (사용자 사전이 있으면 사용)
    user_dict_path = os.path.join(os.path.dirname(__file__), 'user_dict.txt')
    if os.path.exists(user_dict_path):
        komoran = Komoran(userdic=user_dict_path)
    else:
        komoran = Komoran()
    
    # 형태소 분석
    df['tokens'] = df['review'].apply(lambda x: komoran.pos(x))
    
    # 명사 토큰 추출
    Ntag_list = ['NNP', 'NNG']
    Ntoken_list = [[token[0] for token in tokens if token[1] in Ntag_list] for tokens in df['tokens']]
    
    # N-gram 생성
    print("N-gram 생성 중...")
    
    # 2-gram
    bigram = []
    for i in range(len(Ntoken_list)):
        for j in range(len(Ntoken_list[i])-1):
            bigram.append((Ntoken_list[i][j], Ntoken_list[i][j+1]))
    
    bigram_counts = Counter(bigram).most_common()
    bigram_df = pd.DataFrame(bigram_counts, columns=['bigram', 'count'])
    
    # 3-gram
    ngram = []
    for i in range(len(Ntoken_list)):
        for j in range(len(Ntoken_list[i])-2):
            ngram.append((Ntoken_list[i][j], Ntoken_list[i][j+1], Ntoken_list[i][j+2]))
    
    ngram_counts = Counter(ngram).most_common()
    ngram_df = pd.DataFrame(ngram_counts, columns=['ngram', 'count'])
    
    print(f"2-gram 개수: {len(bigram_counts)}")
    print(f"3-gram 개수: {len(ngram_counts)}")
    
    return Ntoken_list, bigram_df, ngram_df

def compound_words(Ntoken_list):
    """단어 합성 (3-gram, 2-gram)"""
    print("\n=== 단어 합성 ===")
    
    # 3-gram 단어 합성
    for i in range(len(Ntoken_list)):
        j = 0
        while j < len(Ntoken_list[i])-2:
            # 3-gram 패턴 매칭
            patterns_3gram = [
                (['아', '벤', '느'], '아벤느'),
                (['리얼', '베리', '어'], '리얼베리어'),
                (['리', '뉴', '얼'], '리뉴얼'),
                (['바이오', '힐', '보'], '바이오힐보'),
                (['톤', '업', '크림'], '톤업크림'),
                (['쿠', '링', '감'], '쿨링감'),
                (['라', '로슈', '포'], '라로슈포'),
                (['아토', '베리', '어'], '아토베리어'),
                (['수분', '부족', '지성'], '수부지'),
                (['라마', '이', '딘'], '세라마이딘'),
                (['피부', '진정', '효과'], '진정'),
                (['바이오', '더', '마'], '바이오더마'),
                (['보', '타', '닉'], '보타닉'),
                (['민', '감성', '피부'], '민감성'),
                (['닥터', '자르', '카'], '닥터자르카'),
                (['악', '건성', '피부'], '악건성피부'),
                (['지', '복합성', '피부'], '지복합성피부'),
                (['베리', '어', '익스트림'], '베리어익스트림'),
                (['자작나무', '수분', '크림'], '자작나무수분크림'),
                (['닥터', '디', '런'], '닥터디런'),
                (['화', '농성', '여드름'], '화농성여드름'),
                (['자르', '카', '페어'], '자르카페어')
            ]
            
            for pattern, replacement in patterns_3gram:
                if (j < len(Ntoken_list[i])-2 and 
                    Ntoken_list[i][j] == pattern[0] and 
                    Ntoken_list[i][j+1] == pattern[1] and 
                    Ntoken_list[i][j+2] == pattern[2]):
                    Ntoken_list[i][j] = replacement
                    del Ntoken_list[i][j+1:j+3]
                    break
            j += 1
    
    # 2-gram 단어 합성
    for i in range(len(Ntoken_list)):
        j = 0
        while j < len(Ntoken_list[i])-1:
            # 2-gram 패턴 매칭
            patterns_2gram = [
                (['수분', '크림'], '수분크림'),
                (['수분', '감'], '수분감'),
                (['유', '분기'], '유분기'),
                (['올리브', '영'], '올리브영'),
                (['진정', '효과'], '진정효과'),
                (['속', '건조'], '속건조'),
                (['보습', '감'], '보습감'),
                (['구매', '의사'], '구매의사'),
                (['발림', '성도'], '발림성'),
                (['사용', '감'], '사용감'),
                (['젤', '크림'], '젤크림'),
                (['악', '건성'], '악건성'),
                (['톤', '업'], '톤업'),
                (['체험', '단'], '체험단'),
                (['재생', '크림'], '재생크림'),
                (['멀티', '밤'], '멀티밤'),
                (['쿠', '링'], '쿨링'),
                (['강', '추'], '강추'),
                (['좁쌀', '여드름'], '좁쌀여드름'),
                (['배', '송'], '배송'),
                (['속', '당김'], '속당김'),
                (['극', '건성'], '극건성'),
                (['젤', '타입'], '젤타입')
            ]
            
            for pattern, replacement in patterns_2gram:
                if (j < len(Ntoken_list[i])-1 and 
                    Ntoken_list[i][j] == pattern[0] and 
                    Ntoken_list[i][j+1] == pattern[1]):
                    Ntoken_list[i][j] = replacement
                    del Ntoken_list[i][j+1]
                    break
            j += 1
    
    print("단어 합성 완료")
    return Ntoken_list

def remove_stopwords(Ntoken_list):
    """불용어 제거"""
    print("\n=== 불용어 제거 ===")
    
    # 기본 불용어 리스트 로드
    stopwords_file = os.path.join(os.path.dirname(__file__), 'stopwords.txt')
    if os.path.exists(stopwords_file):
        stop_words = pd.read_csv(stopwords_file, header=None)
        stopwords_list = stop_words[0].tolist()
    else:
        stopwords_list = []
        print("stopwords.txt 파일이 없습니다. 기본 불용어만 제거합니다.")
    
    # 1. 기본 불용어 제거
    for i in range(len(Ntoken_list)):
        Ntoken_list[i] = [j for j in Ntoken_list[i] if j not in stopwords_list and len(j) > 1]
    
    # 2. 브랜드명 등 추가 불용어 제거
    additional_stopwords = [
        '아벤느', '리얼베리어', '바이오힐보', '라로슈포', '아토베리어', 
        '바이오더마', '보타닉', '닥터자르카', '베리어익스트림',
        '자작나무수분크림', '닥터디런', '자르카페어', '올리브영', '멀티밤'
    ]
    
    for i in range(len(Ntoken_list)):
        Ntoken_list[i] = [j for j in Ntoken_list[i] if j not in additional_stopwords]
    
    print("불용어 제거 완료")
    return Ntoken_list


def main():
    """메인 실행 함수"""
    print("=== 화장품 리뷰 데이터 전처리 시작 ===")
    
    # 1. 경로 설정
    csv_directory = setup_paths()
    
    # 2. CSV 파일 로드 및 통합
    df = load_and_merge_csv_files(csv_directory)
    
    # 3. 데이터 정제
    df = clean_data(df)
    
    # 4. 피부타입 자동 추출
    df = advanced_skin_type_extraction(df)
    
    # 5. 형태소 분석 및 토큰화
    Ntoken_list, bigram_df, ngram_df = tokenize_and_analyze(df)
    
    # 6. 단어 합성
    Ntoken_list = compound_words(Ntoken_list)
    
    # 7. 불용어 제거
    Ntoken_list = remove_stopwords(Ntoken_list)
    
    # 8. 데이터프레임에 토큰 추가
    df['Ntoken_review'] = Ntoken_list
    
    # 9. 최종 저장
    output_file = os.path.join(os.path.dirname(__file__), 'Ntoken_review.csv')
    df.to_csv(output_file, index=False)
    print(f"\n✅ 최종 결과가 {output_file}에 저장되었습니다!")
    print(f"최종 데이터 크기: {df.shape}")
    
    return df

if __name__ == "__main__":
    df = main()
