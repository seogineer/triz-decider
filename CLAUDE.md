# TRIZ Decider — Claude Code 작업 지침

## 프로젝트
TRIZ(모순 행렬 + 40 발명 원리)로 기술적 모순 해결 아이디어를 도출하는 **오픈소스 Claude Code 플러그인**.
전체 설계: `docs/DESIGN.md` — 구현 전 반드시 해당 절을 읽을 것.

## 핵심 원칙 (위반 금지)
- **판단은 LLM, 조회는 스크립트.** 모순 행렬 셀 값·원리 번호·원리 정의를 기억으로 생성하지 않는다. 반드시 `data/*.json`에서 읽는다.
- `lookup.py`는 **Python 3.9+ 표준 라이브러리만** 사용. 외부 네트워크 호출 금지.
- 데이터 경로는 스크립트 위치 기준 상대 경로(`../data/`)로 해석.
- 행렬 셀 값을 추측·보간하지 않는다. 출처가 확인되지 않은 셀은 비워 두고 `DATA_SOURCES.md`에 TODO로 기록.
- 서적·번역본 문장을 복제하지 않는다. 원리 설명·예시는 직접 작성.

## 현재 단계: v0.1
범위: 기술적 모순 흐름만 (DESIGN.md 4.2). 물리적 모순·인터뷰 흐름은 v0.2.
구현 순서: DESIGN.md 11.1 체크리스트를 위에서부터 순서대로.

## 명령
- 테스트: `pytest tests/`
- 데이터 검증: `python skills/triz-analysis/scripts/lookup.py validate`
- 플러그인 검증: `claude plugin validate .`
- 로컬 설치 테스트: `claude --plugin-dir .`

## 규칙
- 슬러그 `triz-decider`는 공식 디렉토리 등재 후 변경 불가.
- SKILL.md 본문 500줄 이하, 상세는 `references/`로 분리.
- 커밋 단위: 체크리스트 항목 1개 = 커밋 1개 이상. Conventional Commits 형식.
- 작업 완료 시 DESIGN.md 11.1 체크박스 갱신.
