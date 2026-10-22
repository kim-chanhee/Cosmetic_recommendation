> 보관용: 정리 이전 실행 안내입니다. 현재 실행 방법은 [실행 가이드](../RUNNING.md)를 참고하세요.

# 추천 노트북 실행 방법

## 1. Cursor / Jupyter에서 실행

1. `3.추천.ipynb` 열기
2. **커널 선택**: `Python 3.13` (miniconda `base`) 또는 `pip install -r requirements.txt` 한 환경
3. 메뉴 **Run → Run All** (또는 셀 위에서 순서대로 실행)

첫 셀(§0)이 현재 커널에 패키지를 자동 설치합니다.

## 2. 터미널에서 한 번에 실행

```bash
cd /Users/Shared/Cosmetic_recommendation-main/추천시스템
/Applications/miniconda3/bin/python3 -m pip install -r requirements.txt
/Applications/miniconda3/bin/python3 -m jupyter nbconvert --to notebook --execute "3.추천.ipynb" --inplace
```

## 3. 자주 나는 오류

| 증상 | 해결 |
|------|------|
| `huggingface-hub` / `transformers` ImportError | §0 셀 재실행 또는 `pip install -r requirements.txt` |
| KoBERT `404 additional_chat_templates` | §0 후 §3 재실행 (캐시 우선 로드). 인터넷 필요 시 Hub 다운로드 |
| `Surprise` 미설치 | **정상** — Python 3.13은 §4에서 **sklearn SVD 대체** 자동 사용 |
| `merged_output.csv` 없음 | `추천시스템` 폴더에서 실행하거나 §0이 경로 자동 설정 |
| 그림 안 보임 | `figures/figure3_*.png`, `figure4_*.png` 파일 확인 |

## 4. 출력 파일

- `figures/figure3_skin_ratio_top10_recommended.png`
- `figures/figure4_hybrid_top10_scores.png`
