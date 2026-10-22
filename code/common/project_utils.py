"""노트북 공통 규약: 경로, 리뷰 ID, 라벨 병합 검증.

모델 코드는 각 단계 노트북에 두고, 세 단계가 반드시 공유해야 하는
파일 식별 규칙만 이 모듈에 둡니다.
"""
from pathlib import Path
import hashlib
import json
import re
import unicodedata

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "2.0"
ID_COLUMNS = ["product_name", "customer_name", "review", "date"]


def review_id(row):
    """정제된 리뷰의 내용을 식별합니다. 행 순서와 CSV 인덱스에 의존하지 않습니다."""
    values = [unicodedata.normalize("NFC", str(row[c])).strip() for c in ID_COLUMNS]
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def add_review_ids(frame):
    frame = frame.copy()
    frame["review_id"] = frame.apply(review_id, axis=1)
    if frame["review_id"].duplicated().any():
        raise ValueError("리뷰 ID 중복: 전처리 단계에서 중복 리뷰를 제거하세요.")
    return frame


def merge_sentiment(reviews, sentiment):
    """리뷰 ID가 정확히 일치할 때만 1:1 병합합니다. 인덱스 병합은 금지합니다."""
    required = {"review_id", "pred", "positive_probability", "sentiment_score", "schema_version"}
    if not required.issubset(sentiment.columns):
        raise ValueError("구형 감성 파일입니다. 감성 분석 노트북부터 재실행하세요.")
    if reviews.review_id.duplicated().any() or sentiment.review_id.duplicated().any():
        raise ValueError("review_id 중복으로 병합할 수 없습니다.")
    if set(reviews.review_id) != set(sentiment.review_id):
        raise ValueError("전처리 리뷰와 감성 결과의 review_id 집합이 다릅니다.")
    if not sentiment.schema_version.astype(str).eq(SCHEMA_VERSION).all():
        raise ValueError("감성 스키마 버전이 다릅니다.")
    prob = pd.to_numeric(sentiment.positive_probability, errors="coerce")
    score = pd.to_numeric(sentiment.sentiment_score, errors="coerce")
    if not prob.between(0, 1).all() or not score.between(-1, 1).all():
        raise ValueError("감성 확률/점수 범위를 확인하세요.")
    if not ((score - (2 * prob - 1)).abs() < 1e-8).all():
        raise ValueError("sentiment_score는 2 * positive_probability - 1이어야 합니다.")
    if not sentiment.pred.eq((prob >= .5).astype(int)).all():
        raise ValueError("pred는 1=긍정, 0=부정이어야 합니다.")
    cols = ["review_id", "pred", "positive_probability", "sentiment_score", "schema_version"]
    return reviews.merge(sentiment[cols], on="review_id", how="left", validate="one_to_one", sort=False)


def known_value(value):
    """빈 피부 정보는 필터 조건으로 사용하지 않습니다."""
    return pd.notna(value) and str(value).strip().lower() not in {"", "unknown", "none", "nan"}


def split_concerns(value):
    if not known_value(value):
        return set()
    return {s.strip() for s in re.split(r"\s*[/,|]\s*", str(value)) if known_value(s)}
