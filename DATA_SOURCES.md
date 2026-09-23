# DATA_SOURCES

데이터 출처·검증 상태 기록. 설계: `docs/DESIGN.md` 9장. 검증일: 2026-09-24.

## 1. 요약

| 파일 | 상태 |
| --- | --- |
| `contradiction-matrix.json` | **교차 검증 완료** (1239셀 확정, 9셀 미확정). 아래 2장 |
| `parameters.json` | 번호·명칭은 독립 자료와 대조 완료, 정의·키워드는 직접 작성 |
| `inventive-principles.json` | 번호·명칭은 대조 완료, **본문(하위 원리·예시)은 재작성 대상** (3장) |
| `separation-principles.json` | v0.2 범위, 미검증 (5장) |

## 2. contradiction-matrix.json

### 2.1 레거시 데이터 폐기
저장소 초기 데이터(1138셀)는 출처가 없었고, 아래 독립 자료와 비교하면 공통 1074셀 중 **약 255셀만 일치**했으며 16·20행이 통째로 없었다. 신뢰할 수 없어 **전량 폐기하고 교차 검증된 값으로 교체**했다(원본은 git 이력에 있음).

### 2.2 사용한 자료
| 기호 | 자료 | 라이선스 | 용도 |
| --- | --- | --- | --- |
| G | TRIZ Consulting Matrix Analyzer, `altschuller_matrix_bilingual.json` (https://www.triz-consulting.de/MatrixAnalyzer/), 2026-09-24 접근, 파일 SHA-256 `6fff8cf4…` | 명시 없음 | **검증 전용.** 로컬 대조에만 쓰고 파일을 저장소에 넣지 않았다 |
| F | luchi2333/triz-worker-innovation-research, `references/contradiction-matrix.json`, 커밋 `6bd7158e` | MIT | 채택 값의 출처. 이 자료의 audit 문서에 따르면 위 G 및 kamil-szczepanik/TRIZ-Agents의 XLS 전사본과 대조했다 |
| B | Cappe6969/triz-innovation-skill, `contradiction_matrix.csv`, 커밋 `28fb6795` | MIT | 교차 확인 |
| E | caolvfeng/TRIZ-_AI_Powered_Contradiction_Matrix_Analysis, `data/contradiction_matrix.py`, 커밋 `e9a4a944` | MIT | 교차 확인 |
| D | Antropocosmist/triz-engineering-solver, `resources/contradiction_matrix.json`, 커밋 `251084f1` | MIT | 교차 확인 (1190셀 부분집합, 58셀 없음) |

### 2.3 사용하지 않은 자료 (이유)
- flyersworder/triz-ai `matrix.json`: 50×50 행렬(2345셀). DESIGN 9.1의 제외 대상(Mann 계열 확장 행렬)에 해당
- d-oit/do-knowledge-studio: 0 기준 번호 체계이고 다른 자료와 사실상 일치하지 않음(488셀 중 2셀)
- triz40.com: 사이트 내 도구 데이터를 통째로 가져오는 것은 데이터베이스 권리 위험이 있어 사용하지 않음
- 학술 PDF(IOSR, KIT 등): 전체 행렬을 싣고 있지 않음

### 2.4 검증 방법과 결과
1. G(독립 온라인 자료)와 F·B·E·D(MIT 전사본)를 같은 형식(개선-악화 키)으로 파싱
2. 채택 조건: **G와 F가 완전히 같고**, B·E·D 중 하나 이상이 같은 값일 것. 값의 배열 순서까지 일치해야 함
3. 결과: 비어 있지 않은 셀 1248개 중 **1239셀 확정**, **9셀은 자료 간 상이**해 `unverified_cells`로 분리
4. 나머지 234개 비대각 셀은 모든 자료에서 비어 있어 "원리 없음"으로 확정(스키마 5.2에 따라 키 생략)
5. 16·20행 포함 39행 모두 확정 셀을 가짐. `missing_rows`는 비어 있음
6. 채택하지 않은 값은 추측·보간하지 않았다

### 2.5 미확정 9셀 (`unverified_cells`, 조회 시 `empty_pairs` + `unverified_cell` 경고)
원인은 (a) XLS 전사본에서 쉼표가 빠진 셀(1-38, 8-25, 33-10, 34-1), (b) 온라인 표기가 원리 1개를 뺀 셀(1-28, 7-28, 15-25, 15-31), (c) 원본 자체의 중복 표기(18-35의 `1` 중복)로 보인다. 어느 쪽이 맞는지는 인쇄본 원문이 있어야 가릴 수 있다.

| 셀 | G(온라인) | F | B | E | D |
| --- | --- | --- | --- | --- | --- |
| 1-28 | 28, 27, 35 | 28, 27, 35, 26 | 28, 27, 35, 26 | 28, 27, 35, 26 | 28, 27, 35, 26 |
| 1-38 | 26, 19 | 26, 35, 18, 19 | 26, 35, 18, 19 | 26, 35, 18, 19 | 26, 35, 18, 19 |
| 7-28 | 26, 28 | 25, 26, 28 | 26, 28 | 25, 26, 28 | 25, 26, 28 |
| 8-25 | 35, 16 | 35, 16, 32, 18 | 35, 16, 32, 18 | 35, 16, 32, 18 | 35, 16, 32, 18 |
| 15-25 | 20, 10, 28 | 20, 10, 28, 18 | 20, 10, 28, 18 | 20, 10, 28, 18 | 20, 10, 28, 18 |
| 15-31 | 21, 39, 16 | 21, 39, 16, 22 | 21, 39, 16, 22 | 21, 39, 16, 22 | 21, 39, 16, 22 |
| 18-35 | 15, 1, 1, 19 | 15, 1, 19 | 15, 1, 19 | 15, 1, 19 | 15, 1, 19 |
| 33-10 | 28 | 28, 13, 35 | 28, 13, 35 | 28, 13, 35 | 28, 13, 35 |
| 34-1 | 2, 11 | 2, 27, 35, 11 | 2, 27, 35, 11 | 2, 27, 35, 11 | 2, 27, 35, 11 |

- [ ] 인쇄본(Altshuller 원전 또는 그 정식 번역본) 또는 제3의 독립 자료로 9셀 확정 후 `unverified_cells`에서 `cells`로 이동

### 2.6 한계
- 모든 자료가 궁극적으로 알츠슐러 고전 행렬의 전사본이라는 점은 같다. G와 F 계열은 서로 다른 경로의 전사이지만, **인쇄 원본과의 직접 대조는 하지 않았다**.
- 원리 순서는 자료 간 일치(4개 자료 동일)하며 원문 순서를 따른다고 가정한다.
- [ ] 릴리스 전 무작위 표본 30셀을 인쇄본과 대조(가능한 경우)
- 라이선스 판단은 법률 자문이 아니다. 행렬 셀 값은 알츠슐러가 공개한 사실 데이터이며 위 MIT 전사본과 출처를 명시해 채택했다. 공식 디렉토리 제출 전 재확인한다.

## 3. inventive-principles.json
- 번호 1~40과 원리 명칭은 F·H(`inventive_principles_bilingual.json`, TRIZ Consulting)와 위치별로 대조했다. 개념은 전부 일치하고 표기 차이만 있다(예: #2 Taking out / Separation, #15 Dynamics / Dynamization)
- **본문 재작성 필요**: 하위 원리 개수가 독립 자료와 다른 원리가 21개이고, 레거시 영문 본문은 널리 쓰이는 표준 영어 표현과 매우 유사한 문장이 있다. CLAUDE.md의 "서적·번역본 문장 복제 금지"에 따라 하위 원리와 예시를 직접 다시 쓴다 → 다음 작업

## 4. parameters.json
- 39개 번호·영문명을 G의 파라미터 목록과 위치별로 대조했다. 표기 차이만 있다(예: #10 Force / Force (Intensity), #37 Difficulty of detecting/measuring / Difficulty of detection)
- 레거시 #30, #31 명칭은 표준과 달라 G 기준으로 `Object-affected harmful factors` / `Object-generated harmful factors`로 고쳤다(G는 단수 표기)
- 정의(ko/en)와 키워드는 이 프로젝트에서 직접 작성했다
- [ ] 정의·키워드 리뷰, 평가 케이스(DESIGN 10.1) 결과에 따라 키워드 보강
- `references/parameters-39.md`는 `parameters.json`에서 생성하며 `tests/test_data_integrity.py`가 동기화를 검사한다

## 5. separation-principles.json (v0.2 범위)
- ID를 `SP1~4` → `time/space/system/condition`으로 변환. 나머지는 레거시 그대로이며 **미검증**
- [ ] `question.ko` 4개 `TODO`
- [ ] 연계 발명 원리 목록 출처 확인 (DESIGN 5.4)
- [ ] 예시 문장의 독창성 확인
