# TRIZ Decider

[English](README.md)

공학·제품 설계의 트레이드오프를 **TRIZ**로 푸는 Claude Code 플러그인입니다. 문제를 기술적 모순으로 구조화하고, 고전 모순 행렬을 조회한 뒤, 40 발명 원리로 해결 아이디어를 제안합니다.

서버·DB·API 키가 필요 없습니다. 추론은 Claude가, 조회는 표준 라이브러리만 쓰는 작은 Python 스크립트가 맡기 때문에 행렬 셀 값이나 원리 번호를 기억으로 지어내지 않습니다.

> **상태: v0.1 (정식 공개 전).** 기술적 모순만 지원합니다. 물리적 모순과 구조화 인터뷰는 v0.2에서 추가됩니다. 결과를 활용하기 전에 [데이터 상태](#데이터-상태)를 확인하세요.

## 설치

```
/plugin marketplace add seogineer/triz-decider
/plugin install triz-decider@triz-decider
```

로컬에서 시험하려면 `claude --plugin-dir .`

## 사용

```
/triz 전동 킥보드 최고 속도를 올리면 배터리가 너무 빨리 닳아요
```

세션에서 `/triz`가 인식되지 않으면 전체 이름 `/triz-decider:triz`를 쓰세요.

`/triz` 없이 트레이드오프를 자연어(한국어·영어)로 설명해도 `triz-analysis` 스킬이 자동으로 켜집니다. 답변은 입력한 언어를 따릅니다.

진행 순서:

1. "X를 개선하면 Y가 악화된다" 형태로 다시 쓰고 사용자에게 확인
2. X, Y를 39개 공학 파라미터에 매핑 (각 1~3개, 근거 포함)
3. 후보 조합을 모두 행렬에서 조회 (`lookup.py matrix`)
4. 원리를 등장 빈도순으로 집계
5. 원리별 정의 조회 (`lookup.py principle`)
6. 사용자 시스템에 맞춘 아이디어를 원리마다 1~3개 작성

## 동작 방식

| 단계 | 담당 |
| --- | --- |
| 문제 이해, 파라미터 매핑, 아이디어 작성 | Claude |
| 파라미터·원리 검증, 행렬 조회, 순위 집계 | `skills/triz-analysis/scripts/lookup.py` |

`lookup.py`(Python 3.9+, 표준 라이브러리만, 네트워크 호출 없음)는 JSON을 출력합니다.

```
python3 skills/triz-analysis/scripts/lookup.py matrix --improve 9 --worsen 19,22
python3 skills/triz-analysis/scripts/lookup.py principle --id 35,15
python3 skills/triz-analysis/scripts/lookup.py param --search 속도
python3 skills/triz-analysis/scripts/lookup.py validate
```

오류는 stderr의 JSON과 종료 코드(2 인자 오류, 3 범위 초과, 4 동일 파라미터, 5 데이터 오류)로 반환합니다. 빈 셀은 오류가 아니라 `empty_pairs`에 담깁니다.

스킬 폴더 안에 `data/`와 `scripts/`가 함께 있어서 스킬 폴더만 따로 Claude.ai에 올려도 동작합니다.

## 데이터 상태

| 데이터 | 상태 |
| --- | --- |
| 모순 행렬 | 서로 독립적으로 옮겨 적은 세 계열(영문 전사본 계열, MATRIZ 지식베이스, 러시아어 표)의 3분의 2 표결로 1248셀 전부를 확정했습니다. 지금은 보류된 셀이 없고, 앞으로 분쟁이 생기면 `unverified_cell` 경고로 알리는 장치는 그대로 있습니다. 인쇄본 원문과의 대조는 아직 하지 않았습니다. |
| 파라미터 39개, 원리 40개 | 번호·명칭은 교차 검증, 정의·하위 원리·예시는 이 프로젝트에서 직접 작성 |
| 매핑 정확도 | 평가 케이스 30건 블라인드 실행: 모든 실행에서 Top-3 적중 100%, 원리 번호 환각 0건, 보류된 셀에 걸렸을 때 9/9 사용자에게 알림. 표본이 작고 기대값을 작성자가 정했으며 실행 간 변동이 있으므로 벤치마크가 아니라 스모크 테스트로 보세요 (`tests/eval/results-v0.1.md`) |

출처, 검증 방법, 미확정 셀은 [DATA_SOURCES.md](DATA_SOURCES.md)에 있습니다. TRIZ 결과는 아이디어의 출발점이지 정답이 아닙니다. 매핑을 점검하고 아이디어를 검증한 뒤에 활용하세요.

## 개발

```
pip install pytest
pytest tests/
python skills/triz-analysis/scripts/lookup.py validate
claude plugin validate .
```

## 라이선스

코드(스크립트·테스트·매니페스트): [MIT](LICENSE). 이 프로젝트에서 작성한 텍스트(파라미터 정의, 원리 설명, 예시): CC BY 4.0, [LICENSE-DATA.md](LICENSE-DATA.md) 참조. 행렬 셀 값은 알츠슐러 고전 행렬을 따르며 출처는 DATA_SOURCES.md에 밝혔습니다.
