"""추천 노트북과 시각화 노트북에서 사용하는 그래프 함수.

셀별 실행은 같은 폴더의 plot_skin_ratio.ipynb를 사용하세요.
"""
from pathlib import Path
import sys
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code/common"))
from skin_type_recommendations import SKIN_TYPES
DATA_PATH = PROJECT_ROOT / "outputs/data/recommendation/merged_output.csv"
RECOMMENDATIONS_PATH = PROJECT_ROOT / "outputs/data/recommendation/recommendations.csv"
OUT_DIR = PROJECT_ROOT / "outputs/figures/recommendation"


SKIN_MAP = {"건성": "Dry", "민감성": "Sensitive", "복합성": "Combination",
            "약건성": "Slightly Dry", "중성": "Normal", "지성": "Oily", "트러블성": "Troubled"}
SKIN_ORDER = ["Unknown", "Dry", "Sensitive", "Combination", "Slightly Dry", "Normal", "Oily", "Troubled"]
COLORS = ["#1B3A5C", "#2E5C8A", "#4A7EBB", "#A8C5E2", "#F5E6D3", "#F4A582", "#D66B2B", "#8B2E2E"]

def configure_font():
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["AppleGothic", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]:
        if name in installed:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


def ratio_matrix(reviews, items):
    """Figure 3은 전체 리뷰를 분모로 사용해 Unknown 비율도 명시합니다.

    추천 필터는 알려진 정보만 사용하므로 필터의 분모와 다릅니다.
    """
    frame = reviews.rename(columns={"product_name": "item_id"}).copy()
    frame["skin_en"] = frame.skin_type.map(SKIN_MAP).fillna("Unknown")
    rows = []
    for item in items:
        sub = frame.loc[frame.item_id == item, "skin_en"]
        if sub.empty:
            raise ValueError(f"추천 제품의 원본 리뷰가 없습니다: {item}")
        rows.append(sub.value_counts(normalize=True).reindex(SKIN_ORDER, fill_value=0).to_numpy())
    return np.array(rows)


def plot_skin_type_review_ratios(reviews, recommendations, out_dir=OUT_DIR):
    """각 피부 타입 추천 목록의 전체 리뷰 피부 분포를 원본 Figure 3 형식으로 표시."""
    configure_font()
    out_dir = Path(out_dir) / "by_skin_type_review_ratio"
    out_dir.mkdir(parents=True, exist_ok=True)
    palette = ["#3B4CC0", "#6685ED", "#98B9FA", "#C9D7EF",
               "#EED1C3", "#F7A889", "#E7654F", "#B40426"]
    display_names = ["Unknown"] + [next(k for k, v in SKIN_MAP.items() if v == s)
                                  for s in SKIN_ORDER[1:]]
    for skin in SKIN_TYPES:
        selection = recommendations.loc[recommendations.skin_type == skin].sort_values("rank")
        items = selection.item_id.tolist()
        fig, ax = plt.subplots(figsize=(16, max(4, len(items)*.82)), layout="constrained")
        ax.set_title(f"Review ratio by skin type for the top {len(items)} products\n"
                     f"Recommended for {skin} ({SKIN_MAP[skin]})", fontsize=14, pad=14)
        if not items:
            ax.text(.5, .5, "No products meet the skin-type threshold", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_axis_off()
        else:
            data = ratio_matrix(reviews, items)
            y = np.arange(len(items))
            left = np.zeros(len(items))
            for j, (name, color) in enumerate(zip(display_names, palette)):
                ax.barh(y, data[:, j], left=left, color=color, label=name, height=.6)
                left += data[:, j]
            labels = [textwrap.fill(item, width=46, break_long_words=False,
                                    break_on_hyphens=False)
                      for item in items]
            ax.set(yticks=y, yticklabels=labels, xlim=(0, 1), xlabel="Review ratio", ylabel="Product name")
            ax.tick_params(axis="y", labelsize=10, length=0, pad=10)
            ax.set_xticks(np.linspace(0, 1, 6))
            ax.invert_yaxis()
            ax.grid(axis="x", linestyle="--", color="#AAAAAA", linewidth=.6, alpha=.6)
            ax.legend(title="Skin type", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=10)
        filename = f"figure3_review_ratio_{SKIN_MAP[skin].lower().replace(' ', '_')}.png"
        fig.savefig(out_dir / filename, dpi=300, facecolor="white")
        plt.close(fig)


def plot_skin_type_recommendations(recommendations, summary, out_dir=OUT_DIR):
    """타입별 Top K를 통합 그림과 개별 300dpi 그림으로 저장합니다."""
    configure_font()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    details = out_dir / "by_skin_type"
    details.mkdir(exist_ok=True)

    def draw(ax, skin, size=9):
        data = recommendations.loc[recommendations.skin_type == skin].sort_values("rank")
        info = summary.loc[summary.skin_type == skin].iloc[0]
        ax.set_title(f"{skin} ({SKIN_MAP[skin]}) — Top {len(data)}\n"
                     f"Users: {info.user_count:,} | Candidates: {info.candidate_count}", fontsize=size+2, pad=12)
        if data.empty:
            ax.text(.5, .5, "No products meet the skin-type threshold", ha="center", va="center",
                    transform=ax.transAxes, fontsize=size)
            ax.set_axis_off()
            return
        labels = [textwrap.fill(f"{rank}. {item}", width=38, break_long_words=False,
                                break_on_hyphens=False)
                  for rank, item in zip(data["rank"], data.item_id)]
        y = np.arange(len(data))
        ax.barh(y, data.final_score, height=.56, color=COLORS[SKIN_ORDER.index(SKIN_MAP[skin])])
        ax.set(yticks=y, yticklabels=labels, xlim=(0, 1.17), xlabel="Hybrid score (within skin type)")
        ax.tick_params(axis="y", labelsize=size, length=0, pad=8)
        ax.invert_yaxis()
        ax.set_axisbelow(True)
        ax.grid(axis="x", color="#D9D9D9", linestyle="--", linewidth=.5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        for pos, score in enumerate(data.final_score):
            ax.text(score+.015, pos, f"{score:.4f}", va="center", fontsize=size)

    fig, axes = plt.subplots(4, 2, figsize=(28, 30), layout="constrained")
    for ax, skin in zip(axes.flat, SKIN_TYPES):
        draw(ax, skin)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0, .7, "Recommendations are computed separately for each skin type.\n"
                      "Candidates must meet the skin-type review ratio threshold.\n"
                      "Scores are normalized within each type, not across types.\n"
                      "Fewer than 10 results means fewer eligible products.",
                      fontsize=14, linespacing=1.8, transform=axes.flat[-1].transAxes)
    fig.savefig(out_dir / "figure3_skin_type_top10_recommendations.png", dpi=200, facecolor="white")
    plt.close(fig)
    for skin in SKIN_TYPES:
        fig, ax = plt.subplots(figsize=(16, 9), layout="constrained")
        draw(ax, skin, size=11)
        fig.savefig(details / f"top10_{SKIN_MAP[skin].lower().replace(' ', '_')}.png",
                    dpi=300, facecolor="white")
        plt.close(fig)


def plot_recommendation_figures(reviews, recommendations, out_dir=OUT_DIR):
    configure_font()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if recommendations.empty:
        # 이전 실행 그림이 새 결과처럼 남지 않도록 빈 상태를 명시합니다.
        for filename in ["figure3_skin_ratio_top10_products.png", "figure4_hybrid_top10_scores.png"]:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.text(.5, .5, "No unseen candidate products", ha="center", va="center")
            ax.axis("off")
            fig.savefig(out_dir / filename, dpi=180)
            plt.close(fig)
        return
    items = recommendations.item_id.tolist()
    data = ratio_matrix(reviews, items)
    y = np.arange(len(items))
    fig, ax = plt.subplots(figsize=(15, max(5, len(items)*.55)))
    left = np.zeros(len(items))
    for j, (skin, color) in enumerate(zip(SKIN_ORDER, COLORS)):
        ax.barh(y, data[:, j], left=left, label=skin, color=color)
        left += data[:, j]
    ax.set(yticks=y, yticklabels=items, xlim=(0, 1), xlabel="Review ratio",
           title=f"Skin type distribution of {len(items)} recommended products")
    ax.invert_yaxis()
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(out_dir / "figure3_skin_ratio_top10_products.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # 긴 상품명은 생략하지 않고 줄바꿈하여 논문 삽입 시에도 읽을 수 있게 합니다.
    labels = [textwrap.fill(f"{rank}. {item}", width=48,
                            break_long_words=False, break_on_hyphens=False)
              for rank, item in enumerate(items, start=1)]
    fig, ax = plt.subplots(figsize=(16, max(6, len(items)*.85)))
    ax.barh(y, recommendations.final_score, height=.58, color="#2E5C8A")
    ax.set(yticks=y, yticklabels=labels, xlim=(0, 1.08), xlabel="Hybrid score (relative to candidates)",
           title=f"Hybrid recommendation scores for the top {len(items)} products")
    ax.tick_params(axis="y", labelsize=11, length=0, pad=12)
    ax.tick_params(axis="x", labelsize=11)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#D9D9D9", linewidth=.6, linestyle="--")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.invert_yaxis()
    for position, score in enumerate(recommendations.final_score):
        ax.text(score+.012, position, f"{score:.6f}", va="center", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_dir / "figure4_hybrid_top10_scores.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("실제 추천 결과 그림 저장:", out_dir)

def main():
    reviews = pd.read_csv(DATA_PATH)
    plot_recommendation_figures(reviews, pd.read_csv(RECOMMENDATIONS_PATH))
    cohort_path = RECOMMENDATIONS_PATH.with_name("recommendations_by_skin_type.csv")
    summary_path = PROJECT_ROOT / "outputs/reports/recommendation/skin_type_summary.csv"
    if cohort_path.exists() and summary_path.exists():
        cohort = pd.read_csv(cohort_path)
        plot_skin_type_recommendations(cohort, pd.read_csv(summary_path))
        plot_skin_type_review_ratios(reviews, cohort)


if __name__ == "__main__":
    main()
