# webcrawling

청약 게시판을 매일 한 번 크롤링해서 새 글을 Telegram으로 알려주는 자동 알림 봇.
PC를 켜둘 필요 없이 GitHub Actions가 무료로 매일 실행합니다.

## 기능

- 매일 09:00 KST 정해진 사이트 게시판 크롤링
- 키워드 포함/제외 필터링
- 이미 알린 글은 다시 알리지 않음 (중복 방지)
- Telegram 한 메시지에 요약 형태로 발신
- 사이트 추가는 yaml 한 항목 (간단한 정적 HTML의 경우)
- 비용 0원 (Public 레포 + GitHub Actions 무료 분량)

## 빠른 시작

### 1. 사전 준비
- Python 3.11+
- Git
- Telegram 봇 토큰과 chat_id ([설정 가이드](./docs/SETUP_TELEGRAM.md))

### 2. 로컬에서 돌려보기

```powershell
# 클론
git clone https://github.com/jks-developer/webcrawling.git
cd webcrawling

# 가상환경 + 의존성
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 환경변수 (.env)
Copy-Item .env.example .env
# notepad .env  -> TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 채우기

# 실행 (example 어댑터는 기본 disable, 실제 사이트를 추가한 뒤 실행)
.venv\Scripts\python.exe -m src.main
```

### 3. GitHub Actions로 자동 실행

레포 fork/clone 후 두 Secret을 등록하면 매일 자동 실행됩니다.
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- 자세한 절차: [docs/SETUP_GITHUB.md](./docs/SETUP_GITHUB.md)

## 사이트 추가

`config/sites.yml`에 항목 추가. 셀렉터로 게시글 행을 가리키면 끝.
자세한 절차: [docs/ADD_SITE.md](./docs/ADD_SITE.md)

## 필터 변경

`config/filters.yml`의 `include`/`exclude` 리스트를 수정.

```yaml
include: []         # 비우면 모든 글 통과
exclude:
  - 당첨자
  - 발표
  - 결과
```

## 프로젝트 구조

```
webcrawling/
├── .github/workflows/daily-notify.yml   # GitHub Actions cron + manual trigger
├── src/
│   ├── main.py            # 진입점 (오케스트레이션)
│   ├── config.py          # YAML + .env 로더
│   ├── crawler.py         # 사이트 어댑터 동적 디스패처
│   ├── filter.py          # 키워드 포함/제외 필터
│   ├── state.py           # seen_ids.json 관리
│   ├── messenger.py       # Telegram Bot API
│   └── sites/
│       ├── base.py        # Post + SiteAdapter
│       ├── example_site.py# 일반 CSS-selector 기반 어댑터 (정적 HTML용)
│       ├── mss_gyeonggi.py# 중기부 경기 (onclick doBbsFView 파싱)
│       ├── sh_seoul.py    # SH 서울 (onclick getDetailView 파싱)
│       ├── gh_gyeonggi.py # GH 경기 (articleNo 추출 + 날짜 정규화)
│       └── applyhome.py   # 청약홈 APT + 무순위/잔여 (베이스+서브클래스)
├── config/
│   ├── sites.yml          # 사이트 목록
│   └── filters.yml        # 알림 키워드
├── data/seen_ids.json     # 본 글 ID 저장 (워크플로우가 자동 커밋)
├── docs/                  # 설정 가이드
├── tests/                 # 단위 테스트 + 픽스처
├── requirements.txt       # 런타임 의존성
└── requirements-dev.txt   # 개발/테스트 추가 의존성
```

## 개발

### 테스트 실행
```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest tests/ -v
```

### 메시지 형식 (Telegram)
```
📋 오늘의 신규 공고 (3건)

[청약홈]
• <a href="...">○○ 아파트 1순위 모집공고</a> (2026-05-23)
• <a href="...">신혼희망타운 입주자 모집</a> (2026-05-22)

[LH]
• <a href="...">매입임대주택 입주자 모집</a> (2026-05-23)
```

## 동작 원리

1. `config/sites.yml`에 등록된 사이트마다 어댑터를 동적으로 import
2. 각 어댑터의 `fetch()`가 현재 게시판 목록을 `Post`로 반환
3. `config/filters.yml`의 포함/제외 키워드로 제목 기준 필터
4. `data/seen_ids.json`에 없는 ID만 "새 글"로 분류
5. 새 글이 있으면 Telegram에 요약 메시지 발송
6. 새 글의 ID를 state에 추가 → 워크플로우가 자동 커밋

## 문서

- [SETUP_TELEGRAM.md](./docs/SETUP_TELEGRAM.md) — 봇 만들고 토큰/chat_id 받기
- [SETUP_GITHUB.md](./docs/SETUP_GITHUB.md) — GitHub 레포 + Secrets + Actions 설정 (완전 초보용)
- [ADD_SITE.md](./docs/ADD_SITE.md) — 새 사이트 어댑터 추가
- [PLAN.md](./PLAN.md), [EXECUTION_PLAN.md](./EXECUTION_PLAN.md) — 초기 설계 문서

## 기술 스택

- Python 3.11+
- requests, beautifulsoup4, lxml, PyYAML
- GitHub Actions (cron + workflow_dispatch)
- pytest (개발)

## 라이선스

개인용 프로젝트. 자유롭게 fork해서 본인의 알림 봇으로 사용하세요.
