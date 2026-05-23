# CLAUDE.md — 본 레포에서 Claude Code가 알아야 할 상시 컨텍스트

> 본 문서는 매 세션 자동 로드되는 가이드다. 인수인계/스냅샷성 정보는 `HANDOFF.md`에 있고, 본 문서는 **변하지 않는 규칙·아키텍처·관용 패턴**만 둔다.

## 1. 프로젝트 한 줄

청약/공급 게시판을 매일 09:00 KST에 크롤링해 새 글만 Telegram으로 알림. GitHub Actions cron으로 무인 운영.

## 2. 아키텍처 (1분 요약)

```
src/main.py
  → load_config()           # config/*.yml + .env/Secrets
  → fetch_all(sites)        # 사이트별 어댑터 동적 import + fetch()
  → apply_filter()          # include/exclude 키워드
  → state.is_seen()         # data/seen_ids.json 으로 중복 제거
  → send_summary()          # Telegram HTML 메시지
  → save_state()
```

핵심 인터페이스: `src/sites/base.py`의 `Post`(dataclass)와 `SiteAdapter`(ABC). 어댑터는 `fetch() -> list[Post]`만 구현.

## 3. 파일 지도

| 영역 | 경로 |
|---|---|
| 도메인 모델 | `src/sites/base.py` |
| 사이트 어댑터 | `src/sites/<key>.py` (5종: mss_gyeonggi, sh_seoul, gh_gyeonggi, applyhome, example_site) |
| 디스패처 | `src/crawler.py` (`adapter: "<module>.<ClassName>"` 동적 import) |
| 설정 로더 | `src/config.py` (`SiteConfig`, `FilterConfig`) |
| 진입점 | `src/main.py` |
| 사이트 등록 | `config/sites.yml` |
| 알림 필터 | `config/filters.yml` |
| 중복 상태 | `data/seen_ids.json` (CI가 자동 커밋) |
| 워크플로우 | `.github/workflows/daily-notify.yml` |
| 테스트 | `tests/test_*.py` + `tests/fixtures/` |
| 인수인계 | `HANDOFF.md` (다른 세션이 이어받을 때만 사용 — 매 작업 갱신 금지) |
| 설계 히스토리 | `PLAN.md`, `EXECUTION_PLAN.md` (역사적) |
| 운영 가이드 | `docs/SETUP_TELEGRAM.md`, `docs/SETUP_GITHUB.md`, `docs/ADD_SITE.md` |

## 4. 어댑터 추가 의사결정

```
정적 HTML + href에 디테일 URL 있음
  → 경로 A: config/sites.yml 한 항목 + adapter=example_site.ExampleSite (셀렉터만)
정적 HTML + href="#" + onclick/JS로 디테일 열림
  → 경로 B: src/sites/<key>.py 커스텀 어댑터 (mss/sh/gh/applyhome 패턴 참고)
SPA / 로그인 / 세션 쿠키 / JSON API
  → 경로 B + requests로 직접 호출 또는 Playwright 도입 검토
```

기존 어댑터별 처리 패턴:
- **mss_gyeonggi**: `tr.onclick`의 `doBbsFView('cb','bc')` 파싱 → `View.do?cbIdx&bcIdx` 재조립
- **sh_seoul**: `<a onclick="getDetailView('SEQ')">` 파싱 → `view.do?seq` 재조립
- **gh_gyeonggi**: 상대 href `?mode=view&articleNo=...` 파싱 + `YY.MM.DD` → `20YY-MM-DD` 정규화
- **applyhome**: `<tr data-hmno data-pbno>` 속성 + GET-동작 가능한 디테일 URL. 공유 베이스 클래스 + 서브클래스 패턴 (보드별 `DETAIL_BASE`만 오버라이드)

## 5. 작업 흐름 규칙

**모든 코드/문서/커밋/push는 계획 → 사용자 승인 → 실행 순서.** 다음 단계는 각각 별개 승인이 필요하다:

1. **설계/스코프** — 무엇을 만들고 어디까지 할지
2. **커밋** — 스테이징 파일 목록 + 커밋 메시지
3. **push** — master 직접 push는 사용자 환경에서 차단되어 있어 매번 수동 승인

새 사이트 추가 표준 절차 (`docs/ADD_SITE.md`도 동일하지만 요약):
1. WebFetch/requests로 페이지 구조 분석 → 정적/JS, 디테일 URL 패턴 확인
2. 디테일 URL이 GET으로 동작하는지 실제 호출 검증
3. fixture 저장 → 어댑터 작성 → 단위 테스트 작성 → yaml 등록
4. `pytest tests/ -v` + 라이브 fetch로 양방향 검증
5. 커밋 (코드+fixture+yaml 단일 커밋) → 승인 → push

`HANDOFF.md`는 **다른 세션이 작업을 이어받을 때의 인수인계 전용**이다. 매 작업마다 갱신하지 않는다. 갱신은 (a) 세션 종료 직전, (b) 다음 세션이 알아야 할 새 사실(등록된 사이트 목록 변경, 알려진 제약 추가, 다음 즉시 할 작업 변동)이 발생했을 때만.

## 6. 자주 쓰는 명령

```powershell
# 가상환경
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# 전체 테스트
.venv\Scripts\python.exe -m pytest tests/ -v

# 단일 어댑터 라이브 검증
.venv\Scripts\python.exe -c "from src.sites.<key> import <Class>; print(<Class>(key='<k>', url='<URL>').fetch()[:3])"

# 로컬 E2E (.env 필요)
.venv\Scripts\python.exe -m src.main

# CI 결과 (gh CLI는 read 권한만; workflow_dispatch는 브라우저)
gh run list --repo jks-developer/webcrawling --workflow="Daily Notify" --limit 5
```

## 7. 운영 제약

- 가상환경 Python 3.13 (로컬) / 3.11 (CI). 항상 `.venv\Scripts\python.exe`로 직접 호출.
- Windows PowerShell 콘솔(cp949)에서 한글 print는 깨져 보이지만 데이터·HTTP·Telegram은 UTF-8 정상.
- `master` 직접 push 차단 — 사용자 수동 승인 필요.
- `gh` 인증 계정은 admin 아님 → workflow_dispatch는 브라우저에서.
- 로컬 작업 시작 전 `git pull` (CI가 `seen_ids.json` 자동 커밋).
- `seen_ids`에 이미 있는 글은 필터를 새로 통과해도 알림 안 옴 (의도된 동작).

## 8. 디렉터리 컨벤션

- `.claude/`, `.omc/` — 세션 도구가 만드는 디렉터리. `.gitignore` 처리됨. 커밋 금지.
- `data/seen_ids.json` — CI가 `github-actions[bot]`로 자동 커밋. 로컬에서 수동 수정 시 push 전 주의.
- `tests/fixtures/<key>_sample.html` — 어댑터당 fixture 1개. 회귀 안정성을 위해 실제 응답을 그대로 저장.

## 9. 다음 행동이 막힐 때

- 새 세션이면 `HANDOFF.md`를 먼저 읽고 §7.2 "즉시 할 작업"부터 진행.
- 사이트 추가가 막히면 가장 가까운 패턴(mss/sh/gh/applyhome)의 어댑터를 그대로 카피해 차이점만 수정.
- 사용자 결정이 필요한 분기점에서는 자동 진행 금지. 옵션을 정리해 질문.
