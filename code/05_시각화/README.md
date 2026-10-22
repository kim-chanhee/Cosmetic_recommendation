# Results and Visualization

연구 결과를 상품 순위와 피부 타입별 리뷰 비율로 확인합니다.

## Top N Recommendation

![연구에서 제시한 추천 순위와 최종 점수](../../docs/assets/recommendation-example.png)

연구에서 사용한 추천 결과 예시입니다. 상품과 최종 점수를 보여 주며 현재 코드로 다시 실행한 결과와는 순위가 다를 수 있습니다.

## Review Ratio by Skin Type

![상품별 피부 타입 리뷰 비율](../assets/skin-type-review-ratio.png)

상위 10개 상품에 달린 리뷰를 피부 타입별 비율로 표현한 예시입니다. 각 막대는 상품 하나이며, 색상은 해당 상품의 전체 리뷰 중 피부 타입이 차지하는 구성비입니다. 이 그림 자체가 피부 타입별 Top 10 추천을 뜻하지는 않습니다.

## 같은 형식으로 현재 결과 생성하기

[plot_skin_ratio.ipynb](plot_skin_ratio.ipynb)를 위에서부터 실행하세요. 추천 CSV가 먼저 생성되어 있어야 합니다.

- 데이터 로드와 비율 계산을 셀별로 확인합니다.
- 타입별 추천 상품의 리뷰 비율을 300dpi PNG로 저장합니다.
- `PREVIEW_SKIN`으로 미리 볼 피부 타입을 선택합니다.
- 선택 셀에서 타입별 추천 점수 또는 개인 추천 그림을 생성합니다.

현재 코드는 **개인 추천**과 **피부 타입별 집단 추천**을 모두 제공합니다. 리뷰 비율 그래프는 추천된 상품의 리뷰 구성비를 설명하며, 추천 점수나 효과를 나타내지 않습니다. 미상 리뷰를 포함한 막대의 비율 합은 1입니다. 후보 선정에는 알려진 피부 정보만 분모로 사용하므로 필터 비율과 그래프 비율은 다릅니다.

[현재 건성 추천 리뷰 비율](../../outputs/figures/recommendation/by_skin_type_review_ratio/figure3_review_ratio_dry.png) · [타입별 이미지 폴더](../../outputs/figures/recommendation/by_skin_type_review_ratio/) · [현재 개인 추천 점수](../../outputs/figures/recommendation/figure4_hybrid_top10_scores.png)

현재 건성·지성·복합성은 각 10개, 민감성은 9개, 트러블성은 2개입니다. 약건성·중성은 기준을 충족하는 후보가 없어 빈 상태를 표시합니다.

보조 모듈은 [plot_skin_ratio.py](plot_skin_ratio.py)입니다. 프로젝트 루트에서 다음과 같이 실행할 수도 있습니다.

```bash
.venv/bin/python code/05_시각화/plot_skin_ratio.py
```

[전체 구현 안내](../README.md) · [실행 가이드](../../docs/RUNNING.md)
