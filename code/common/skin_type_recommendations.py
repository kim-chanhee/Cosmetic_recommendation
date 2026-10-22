"""사용자의 최신 피부 타입별 집단 선호를 사용한 상품 추천.

타입별 추천은 개인 추천과 달리 집단 구성원이 이미 본 상품도 포함합니다.
피부 톤과 고민으로 후보를 확장하지 않으며 미상 타입은 제외합니다.
"""
import numpy as np
import pandas as pd

from project_utils import known_value

SKIN_TYPES = ["건성", "지성", "복합성", "민감성", "약건성", "중성", "트러블성"]


def normalize(values):
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("피부 타입 추천 점수에 유효하지 않은 값이 있습니다.")
    span = np.ptp(values)
    return np.full_like(values, .5) if span < 1e-8 else (values-values.min())/span


def recommend_by_skin_type(state, k=10, content_weight=.5, threshold=.1):
    """최신 타입별 사용자 콘텐츠 프로필 및 협업 예측을 각각 평균합니다.

    사용자별 콘텐츠 프로필은 평점 >=4인 제품 벡터의 평점 가중 평균입니다.
    콘텐츠 프로필이 있는 사용자는 각각 단위 벡터로 만든 후 동일 비중으로
    집계합니다. 협업 예측도 사용자별 동일 비중입니다. 정규화는 타입별
    후보 안에서 수행하므로 서로 다른 타입의 점수를 직접 비교하지 않습니다.
    """
    if k < 1 or not 0 <= content_weight <= 1 or not 0 <= threshold <= 1:
        raise ValueError("k는 양수, 가중치와 비율 기준은 0~1이어야 합니다.")
    frame = state["frame"]
    latest = (frame.loc[frame.skin_type.map(known_value)]
              .sort_values(["date", "review_id"], na_position="first")
              .groupby("user_id", sort=True).tail(1))
    weights = (frame.loc[frame.rating >= 4]
               .groupby(["user_id", "item_id"]).rating.mean())
    profiles = {}
    for user, values in weights.groupby(level="user_id"):
        indices = [state["item_index"][item] for item in values.index.get_level_values("item_id")]
        vector = np.average(state["vectors"][indices], axis=0, weights=values.to_numpy())
        norm = np.linalg.norm(vector)
        if norm > 1e-12:
            profiles[user] = vector/norm
    rows, summaries = [], []
    ratios = state["ratios"]["skin_type"]
    for skin in SKIN_TYPES:
        users = sorted(latest.loc[latest.skin_type == skin, "user_id"].unique())
        items = sorted(ratios.index[ratios[skin] >= threshold]) if skin in ratios else []
        summary = dict(skin_type=skin, user_count=len(users), candidate_count=len(items),
                       recommended_count=0, content_user_count=0)
        if not users or not items:
            summaries.append(summary)
            continue
        vectors = [profiles[user] for user in users if user in profiles]
        summary["content_user_count"] = len(vectors)
        indices = [state["item_index"][item] for item in items]
        # 각 사용자의 코사인 유사도를 평균한 것과 동일합니다.
        content = (state["vectors"][indices] @ np.mean(vectors, axis=0)
                   if vectors else np.full(len(items), np.nan))
        cf = []
        for item in items:
            predictions = [state["model"].predict(str(user), item) for user in users]
            cf.append(np.mean([p.est if state["backend"] == "surprise" else p for p in predictions]))
        cn = normalize(content) if vectors else np.full(len(items), np.nan)
        fn = normalize(cf)
        scores = content_weight*cn+(1-content_weight)*fn if vectors else fn
        result = pd.DataFrame(dict(item_id=items, final_score=scores, content_score=content,
                                   cf_rating=cf, content_norm=cn, cf_norm=fn,
                                   skin_review_ratio=ratios.loc[items, skin].to_numpy()))
        result = result.sort_values(["final_score", "item_id"], ascending=[False, True]).head(k)
        result.insert(0, "skin_type", skin)
        result.insert(1, "rank", np.arange(1, len(result)+1))
        result["user_count"] = len(users)
        result["content_user_count"] = len(vectors)
        result["strategy"] = "skin_type_cohort_hybrid" if vectors else "skin_type_cohort_cf"
        rows.append(result)
        summary["recommended_count"] = len(result)
        summaries.append(summary)
    columns = ["skin_type", "rank", "item_id", "final_score", "content_score", "cf_rating",
               "content_norm", "cf_norm", "skin_review_ratio", "user_count", "content_user_count", "strategy"]
    return (pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=columns),
            pd.DataFrame(summaries))
