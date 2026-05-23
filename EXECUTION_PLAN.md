# 구현 실행 계획서

> 본 문서는 `PLAN.md`의 후속 문서로, **실제 구현을 어떻게 진행할 것인가**를 다룬다.
> 진행 방식, 중간 검증 방법, 설정 파일 관리, 커밋 전략을 정의한다.

---

## 1. 개발 진행 방식

### 1.1 원칙
- **점진적(incremental)**: 한 번에 한 모듈씩, 작성 → 검증 → 커밋 순으로 진행
- **하향식 인터페이스 우선**: 추상 클래스/타입 먼저 정의 → 구체 구현은 나중에
- **항상 실행 가능한 상태 유지**: 어느 단계에서 멈춰도 부분 동작 가능
- **사용자 확인 게이트(🔒)**: 핵심 분기점에서 멈추고 확인 받음

### 1.2 Phase 구성

> 🔧 표시는 **사용자 설정 단계**(코드 작업이 아닌 외부 설정). 그 다음 Phase 진입 전에 마무리.

| Phase | 목표 | 끝나면 동작하는 것 | 게이트 |
|-------|------|------------------|--------|
| **P1. 스캐폴딩** | 디렉토리·메타파일 작성 | (실행 가능 코드 없음, 구조만) | 🔒 구조 확정 |
| **C0. 첫 커밋/push** | 스캐폴딩을 origin/master에 동기화 | 원격 레포에 초기 구조 반영 | 🔒 push 결과 |
| **P2. 핵심 도메인** | Post/SiteAdapter, filter, state | 단위 테스트 통과 | 🔒 P2 검증 |
| **🔧 S-Telegram** | **Telegram 봇 생성 + 토큰/chat_id 확보 → 로컬 `.env` + GitHub Secrets 동시 등록** | TELEGRAM_BOT_TOKEN/CHAT_ID 양쪽 사용 가능 | 🔒 등록 확인 |
| **P3. 외부 어댑터** | messenger (Telegram), example_site | Telegram에 테스트 메시지 전송 OK | 🔒 실제 Telegram 수신 |
| **P4. 오케스트레이션** | config, crawler, main | 로컬 E2E 실행 → 알림 도착 | 🔒 4개 E2E 시나리오 |
| **P5. CI/CD** | GitHub Actions 워크플로우 | `workflow_dispatch`로 클라우드 실행 성공 | 🔒 Actions 실행 결과 |
| **P6. 문서화** | docs/ 가이드, README | 초보자가 따라 할 수 있는 상태 | 🔒 P6 검증 |
| **🔧 S-Site** | **사용자가 실제 청약 사이트 URL + 관심 게시판 페이지 공유** | 어댑터 작성에 필요한 입력 확보 | 🔒 URL 확인 |
| **P7. 실제 사이트** | 사용자가 지정한 청약 사이트 어댑터 | 실제 게시판에서 알림 수신 | 🔒 실 알림 확인 |

### 1.3 커밋 전략
- **Phase당 1~3개 커밋** (논리적으로 응집된 단위)
- 커밋 메시지 형식: `<type>: <설명>` (Conventional Commits 단순화)
  - `feat`: 새 기능
  - `fix`: 버그 수정
  - `docs`: 문서만
  - `test`: 테스트 추가/수정
  - `chore`: 빌드/설정/잡일
  - `refactor`: 동작 변화 없는 코드 개선
- 예시:
  - `chore: scaffold project structure`
  - `feat: add SiteAdapter base + Post dataclass`
  - `feat: implement keyword include/exclude filter with tests`
  - `feat: implement Telegram message sender`
- **Push 시점**: 각 Phase 끝나는 시점에 한 번씩 push. 단, P5 시작 전에 반드시 한 번 push 필요 (GitHub Actions 등록 위해)

### 1.4 브랜치 전략
- **단일 브랜치 (`master`)** 직접 작업
  - 이유: 1인 개발, PR 리뷰 흐름 불필요, 단순성 우선
- 큰 실험적 변경이 필요해지면 그때 feature 브랜치 도입 검토

---

## 2. 중간 검증(Mid-Verification) 전략

### 2.1 검증 레벨 정의

| 레벨 | 도구 | 언제 |
|------|------|------|
| **L1. 정적 점검** | `python -m py_compile`, `ruff check` (옵션) | 코드 작성 직후 |
| **L2. 단위 테스트** | `pytest tests/` | 모듈 작성/수정 시 |
| **L3. 통합 실행** | `python -m src.main` (로컬, fixture 사용) | Phase 끝날 때 |
| **L4. 실제 외부 호출** | Telegram API 실호출, 실제 사이트 크롤링 | P3/P7 끝날 때 |
| **L5. CI 실행** | GitHub Actions `workflow_dispatch` | P5/P7 끝날 때 |

### 2.2 Phase별 검증 체크리스트

#### P2 검증 (핵심 도메인)
- [ ] `pytest tests/test_filter.py -v` — 포함/제외/조합 케이스 모두 통과
- [ ] `pytest tests/test_state.py -v` — 빈 파일/기존 데이터/추가 시나리오 통과
- [ ] `python -c "from src.sites.base import Post, SiteAdapter; print('ok')"` — import 성공
- [ ] 🔒 결과 보고 → 사용자 승인

#### P3 검증 (외부 어댑터)
- [ ] `python -c "from src.messenger import send_message; send_message('테스트')"` — 실제 Telegram 수신 확인
- [ ] `python -c "from src.sites.example_site import ExampleSite; print(ExampleSite('tests/fixtures/sample.html').fetch())"` — Post 리스트 출력
- [ ] 🔒 Telegram 화면 캡처 또는 수신 확인 보고 → 사용자 승인

#### P4 검증 (오케스트레이션)
- [ ] `config/sites.yml`이 example_site 1개만 등록한 상태로 `python -m src.main` 실행
- [ ] **첫 실행**: 픽스처의 모든 글이 알림으로 도착, `data/seen_ids.json` 생성됨
- [ ] **두 번째 실행**: 새 글 0건, 메시지 발송 없음, JSON 변화 없음
- [ ] **픽스처에 새 글 추가 후 실행**: 추가된 글만 알림으로 도착
- [ ] **필터 동작 확인**: `filters.yml`에 exclude 키워드 등록 → 해당 글 빠짐 확인
- [ ] 🔒 위 4개 시나리오 결과 보고 → 사용자 승인

#### P5 검증 (GitHub Actions)
- [ ] Secrets 등록 완료 확인 (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
- [ ] `git push` 후 Actions 탭에 워크플로우 인식
- [ ] `Run workflow` 수동 실행 → 모든 step 성공 (녹색)
- [ ] 로그에서 `python -m src.main` 출력 확인
- [ ] Telegram 메시지 수신 확인
- [ ] `seen_ids.json` 자동 커밋 발생 확인 (`git log` 또는 commit 페이지)
- [ ] 🔒 결과 보고 → 사용자 승인

#### P7 검증 (실제 사이트)
- [ ] 어댑터 단독 호출 → Post 리스트 정확히 파싱되는지 확인 (id, title, url, date)
- [ ] 로컬 전체 실행 → 의도한 글만 알림 도착
- [ ] Actions 수동 실행 → 동일 결과
- [ ] 🔒 24시간 후 자동 실행 결과 확인

### 2.3 검증 실패 시 대응
1. 실패 로그/메시지 그대로 보고
2. 원인 분석 후 수정 계획 제시 → 🔒 승인
3. 수정 → 동일 검증 재실행
4. 통과 시 다음 단계 진행

---

## 3. 설정 파일(Configuration) 관리

### 3.1 설정의 분류 — "어디에 두느냐" 결정 기준

| 종류 | 저장소 | 예시 | 이유 |
|------|--------|------|------|
| **사이트 정의** | `config/sites.yml` (git) | URL, 셀렉터, 어댑터 클래스 | 코드와 함께 버전 관리, 재현성 |
| **필터 키워드** | `config/filters.yml` (git) | 포함/제외 키워드 | 자주 바뀌지만 비밀 아님, 이력 관리 가치 |
| **비밀값** | GitHub Secrets (로컬은 `.env`) | Telegram 토큰, chat_id | 절대 git에 들어가면 안 됨 |
| **상태(state)** | `data/seen_ids.json` (git) | 본 게시글 ID 목록 | GitHub Actions가 자동 커밋해 동기화 |
| **로컬 임시** | `.env` (git에서 제외) | 개발용 토큰 | 개인 환경 격리 |

### 3.2 `config/sites.yml` 스키마
```yaml
# 사이트 목록. 새 사이트 추가 시 여기에 항목 추가하고 src/sites/ 에 어댑터 작성.
sites:
  - key: example                       # 사이트 식별자 (seen_ids.json 키로 사용)
    name: 예시 사이트                  # 표시용 이름
    adapter: example_site.ExampleSite  # src/sites/ 내 클래스 경로
    url: https://example.com/board     # 게시판 URL
    selectors:                          # 어댑터가 파싱에 사용
      row: "table.list tr.item"
      title: "td.title a"
      link: "td.title a@href"
      date: "td.date"
      id: "td.title a@data-id"         # 또는 URL에서 추출
    enabled: true                       # false면 스킵
```

### 3.3 `config/filters.yml` 스키마
```yaml
# 사이트 공통 필터. (필요 시 사이트별 필터로 확장 가능)
include: []        # 비우면 모든 글 통과
                   # 예: ["청약", "모집공고", "1순위"]
exclude:           # 제목에 포함되면 제외
  - 당첨자
  - 발표
  - 결과
```

### 3.4 비밀값 관리 (`.env` / GitHub Secrets)

**로컬 개발용 `.env`** (git에서 제외)
```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321
```
- 로드: `os.environ` 직접 읽기. (가벼움 우선, `python-dotenv` 의존성 추가는 보류)
- 사용 시: `set -a; source .env; set +a` (bash) 또는 PowerShell `$env:TELEGRAM_BOT_TOKEN="..."` 로 export 후 실행
- 또는 `.env.example` 만들어 git에 포함 (값 없는 템플릿)

**GitHub Secrets** (GitHub Actions 환경)
- 워크플로우의 `env:` 블록에서 `${{ secrets.* }}`로 주입
- 워크플로우 로그에 자동 마스킹 (`***`)

### 3.5 `.gitignore` (반드시 포함될 항목)
```
# 비밀값
.env
.env.local

# Python
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
.venv/
venv/

# IDE
.vscode/
.idea/

# OS
Thumbs.db
.DS_Store
```

### 3.6 `data/seen_ids.json` 라이프사이클
- **초기 상태**: `{}` (빈 객체)
- **커밋 권한**: 워크플로우의 `permissions: contents: write` + `github-actions[bot]` 커밋
- **충돌 방지**: 워크플로우는 하루 1회 실행되며 단일 브랜치에 commit/push. 동시 실행 가능성 매우 낮음. 만약 발생 시 push 실패 → 다음 실행에서 자연스럽게 복구
- **무한 증가 방지**: 사이트별 ID 최대 1000개 유지 (오래된 것부터 제거) — `src/state.py`에서 처리
- **수동 리셋**: `data/seen_ids.json`을 `{}`로 덮어쓰면 다음 실행에서 현재 게시판 전체가 "본 적 있음"으로 다시 시드됨 (=알림 폭주 방지) → 실행 시 자동 시드 옵션 추가

### 3.7 설정 변경 워크플로우
| 변경 종류 | 절차 |
|----------|------|
| 새 사이트 추가 | 1) `src/sites/<new>.py` 작성 2) `config/sites.yml`에 등록 3) 로컬 테스트 4) push |
| 키워드 추가/제거 | `config/filters.yml` 편집 → push (즉시 반영) |
| 토큰 변경 | GitHub Secrets 갱신 (코드 변경 없음) |
| 스케줄 변경 | `.github/workflows/daily-notify.yml`의 cron 수정 → push |

---

## 4. 에러 처리 & 로깅

### 4.1 에러 격리 원칙
- **사이트 단위 격리**: 한 사이트의 크롤링 실패가 다른 사이트나 전체 실행을 막지 않음
- **Telegram 발신 실패**: 로그 출력 후 종료 (워크플로우는 실패로 표시되어 사용자가 인지)
- **state 저장 실패**: 즉시 종료 (다음 실행에서 중복 알림 방지)

### 4.2 로깅 방식
- 표준 `logging` 모듈, `INFO` 레벨이 기본
- 포맷: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- 출력: stdout (GitHub Actions가 자동 캡처)
- 주요 로그 포인트:
  - 각 사이트 fetch 시작/완료/실패
  - 필터링 전/후 글 개수
  - 새 글 개수
  - Telegram 발신 시작/완료/실패
  - state 저장 완료

### 4.3 워크플로우 실패 알림 (선택)
- GitHub Actions가 실패하면 GitHub이 등록 이메일로 자동 알림
- 추가 알림 필요 시 `if: failure()` step으로 Telegram에 실패 메시지 발송 가능 (현재 범위 외)

---

## 5. 의존성 관리

### 5.1 `requirements.txt` 운영 원칙
- 최소 의존성: 4개만 (`requests`, `beautifulsoup4`, `lxml`, `PyYAML`)
- 버전 명시: `>=X.Y` 형태로 하한만 지정 (보안 패치 자동 수용)
- 새 의존성 추가 시:
  1) 정말 필요한지 검토 (표준 라이브러리로 가능한가?)
  2) `requirements.txt`에 추가
  3) 커밋 메시지에 사유 명시

### 5.2 Python 버전
- 로컬과 CI 모두 **Python 3.11+** 사용
- 워크플로우의 `actions/setup-python@v5`의 `python-version: '3.11'`로 고정

---

## 6. 작업 시 예상되는 리스크 & 대응

| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| 청약 사이트가 JS 렌더링 사이트 | 중 | 높음 | 발생 시 Playwright 어댑터 추가 (별도 phase) |
| 사이트 셀렉터 변경 | 중 | 중 | fetch 결과 0건이면 경고 로그 → 사용자가 인지 |
| Telegram 토큰 노출 | 낮 | 높음 | `.env`/`.gitignore` 철저, Secrets만 사용 |
| GitHub Actions 무료 한도 초과 | 매우 낮음 | 중 | Public repo는 무제한이므로 사실상 불가능 |
| 워크플로우 cron 지연 | 낮음 | 낮음 | 알려진 GitHub 특성. 분 단위 정밀도 미요구로 무시 |
| 사이트가 크롤러 차단 | 중 | 중 | User-Agent 헤더 설정, 요청 간격 두기, 발생 시 사용자에게 확인 |

---

## 7. 진행 시작 시 첫 단계 (P1 스캐폴딩 상세)

**아래는 사용자 승인을 받고 진행할 P1의 구체 작업 목록입니다.**

작업:
1. 디렉토리 생성: `src/`, `src/sites/`, `config/`, `data/`, `docs/`, `tests/`, `tests/fixtures/`, `.github/workflows/`
2. 빈 `__init__.py` 추가: `src/`, `src/sites/`, `tests/`
3. `.gitignore` 작성
4. `requirements.txt` 작성
5. `data/seen_ids.json` 작성 (`{}`)
6. `config/sites.yml` 작성 (example만 포함)
7. `config/filters.yml` 작성 (예시 키워드)
8. `.env.example` 작성

검증:
- `git status`로 추가된 파일 확인
- `pip install -r requirements.txt` 성공 확인
- 파일 트리 출력으로 사용자에게 보고

🔒 **P1 완료 후 사용자 승인 받고 P2로 진행**

---

## 8. 사용자 설정(🔧) 단계 상세

### 8.1 S-Telegram (P2 종료 후 / P3 진입 전)

**목표**: Telegram 토큰 1회 확보로 로컬과 GitHub Actions 양쪽에서 즉시 사용 가능한 상태 만들기.

1. **봇 생성** (Telegram 앱)
   - `@BotFather` 검색 → 대화 시작
   - `/newbot` 입력 → 봇 이름 지정 → username 지정 (`_bot` 으로 끝나야 함)
   - 응답에서 **HTTP API token** 복사 → `TELEGRAM_BOT_TOKEN` 값
2. **chat_id 확보**
   - 만든 봇과 대화창 열어 아무 메시지나(예: `/start`) 한 번 전송
   - 브라우저에서 `https://api.telegram.org/bot<TOKEN>/getUpdates` 접속
   - 응답 JSON 의 `"chat":{"id": ...}` 값 → `TELEGRAM_CHAT_ID` 값
3. **로컬 `.env` 작성**
   - 프로젝트 루트에서 `.env.example` 을 `.env` 로 복사
   - 두 값 채우기. `.env` 는 `.gitignore` 로 보호됨
4. **GitHub Secrets 등록** (같은 자리에서 같이 등록 권장)
   - GitHub 레포 → Settings → Secrets and variables → Actions → `New repository secret`
   - `TELEGRAM_BOT_TOKEN` 등록 → `TELEGRAM_CHAT_ID` 등록
5. **검증**
   - 사용자가 "등록 완료" 응답 → 🔒 통과
   - (선택) `curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"` 로 토큰 유효성 확인

### 8.2 S-Site (P6 종료 후 / P7 진입 전)

**목표**: 실제 어댑터 작성에 필요한 입력 확보.

수집할 정보:
- 게시판 페이지 URL (목록이 보이는 페이지)
- 사이트 식별용 짧은 이름 (예: `chungyak_home`)
- 알림에서 보고 싶은 글 유형 (있다면 키워드 → `filters.yml` 반영)
- 페이지가 JS 렌더링 필요한지 여부 (모르면 함께 확인)
- 인증/로그인 필요 여부 (대부분 아닐 것)

---

## 9. 핵심 게이트 요약 (한눈에)

```
P1 스캐폴딩         →  🔒 구조 OK?
C0 첫 커밋/push     →  🔒 origin/master 반영?
P2 핵심 도메인      →  🔒 단위 테스트 통과?
🔧 S-Telegram      →  🔒 .env + GitHub Secrets 등록 완료?
P3 외부 어댑터      →  🔒 실제 Telegram 수신?
P4 오케스트레이션    →  🔒 4개 E2E 시나리오 통과?
P5 CI/CD           →  🔒 Actions 클라우드 실행 성공?
P6 문서화          →  🔒 문서 검토 OK?
🔧 S-Site          →  🔒 실제 사이트 URL 확보?
P7 실제 사이트      →  🔒 실 사이트에서 의도한 알림 수신?
```

> 🔧 = 사용자 설정 단계. 코드 작업 없음, 그 자리에서 외부 설정만 마무리하고 다음 Phase로 이동.
