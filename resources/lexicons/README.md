# KNU 감성 사전

기존 `combined_pos_words.txt`, `combined_neg_words.txt`는 macOS Alias여서 단어 내용을 읽을 수 없었습니다. 원래 Alias는 `.backups/before_pipeline_fixes.zip`에 보존했습니다.

현재 파일은 [공식 KNU 감성 사전](https://github.com/park1200656/KnuSentiLex)의 `SentiWord_info.json`에서 재구성한 UTF-8 단어 목록입니다. 이전에 사용했던 사용자 확장 사전과 동일하다고 가정하지 않습니다.

- `knu_sentiword.json`: 공식 원본 JSON.
- `combined_pos_words.txt`: 극성 > 0인 표현 4,863개.
- `combined_neg_words.txt`: 극성 < 0인 표현 9,824개.
- `provenance.json`: 원본 URL, 고정 커밋, SHA-256.

KNU 원본의 극성은 -2~2입니다. 기존 이진 사전 방식과 연결하기 위해 여기서는 부호에 따라 긍정·부정으로 나눕니다. 형태소 분석 후 충돌하는 표현은 감성 분석 노트북에서 제외하고, 점수 0은 판단 불가로 처리합니다.

출처: 군산대학교 Data Intelligence Lab, 온병원·박상민·나철원, KNU 한국어 감성사전. 원본 자료의 이용 조건과 출처 표기를 함께 확인하세요.
