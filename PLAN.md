# 청약 게시판 → Telegram 일일 알림 봇 — 계획서

## 프로젝트 위치 & 레포지토리

- **로컬 경로**: `E:\99.Personal Dev\09.etc\webcrawling`
- **GitHub 레포**: https://github.com/jks-developer/webcrawling
- **현재 브랜치**: `master`

---

## 1. 목적 (Context)

청약 사이트 게시판에 매일 올라오는 신규 공고를 놓치지 않기 위해, 매일 정해진 시간에 새 글을 요약해 Telegram으로 받아보는 자동 알림 시스템을 구축한다.

**제약/원칙**
- PC를 켜두지 않아도 동작해야 함
- 비용 0원
- 안정적이고 유지보수 부담이 작을 것
- 사이트는 추후 추가 가능한 확장 구조

---

## 2. 핵심 결정 사항 (인터뷰 결과)

| 항목 | 결정 | 비고 |
|------|------|------|
| 메신저 | **Telegram Bot** | 무료, API 단순, 토큰 영구 |
| 언어/스택 | **Python 3.11+** | requests + BeautifulSoup |
| 호스팅 | **GitHub Actions (Public repo)** | cron 트리거, 비용 0 |
| 스케줄 | **매일 오전 9시 (KST)** 1회 | UTC 00:00 |
| 사이트 | 구조만 먼저 | URL은 추후 추가, 다중 사이트 확장 가능 |
| 필터 | **포함 + 제외 키워드 조합** | YAML로 관리 |
| 중복 방지 | **`seen_ids.json` 파일** | 워크플로우가 자동 커밋 |
| 메시지 형식 | **한 메시지에 요약 목록** | 제목 + 링크 |
| 의존성 관리 | **`requirements.txt`** | 단순함 |
| 크롤링 도구 | **requests + BeautifulSoup** | 정적 HTML 사이트 가정, 필요 시 Playwright 폴백 |
| 문서 수준 | **GitHub 완전 초보용 가이드 포함** | 별도 docs/ 디렉토리 |

---

## 3. 프로젝트 구조

```
webcrawling/                          # 프로젝트 루트 (= 레포 루트)
├── PLAN.md                           # 본 계획서
├── README.md                         # 프로젝트 개요/실행법
├── .gitignore
├── requirements.txt
├── .github/
│   └── workflows/
│       └── daily-notify.yml          # cron: 매일 09:00 KST (= UTC 00:00)
├── src/
│   ├── __init__.py
│   ├── main.py                       # 진입점 (오케스트레이션)
│   ├── config.py                     # YAML 로더
│   ├── crawler.py                    # 사이트 어댑터 디스패처
│   ├── filter.py                     # 포함/제외 키워드 매칭
│   ├── state.py                      # seen_ids.json 읽기/쓰기
│   ├── messenger.py                  # Telegram Bot API 호출
│   └── sites/
│       ├── __init__.py
│       ├── base.py                   # SiteAdapter 추상 클래스
│       └── example_site.py           # 샘플 어댑터
├── config/
│   ├── sites.yml                     # 사이트별 URL/셀렉터 정의
│   └── filters.yml                   # 포함/제외 키워드 리스트
├── data/
│   └── seen_ids.json                 # {"site_key": ["id1", "id2", ...]}
├── docs/
│   ├── SETUP_GITHUB.md               # GitHub 초보 가이드
│   ├── SETUP_TELEGRAM.md             # 봇 생성 → 토큰 → chat_id 획득
│   └── ADD_SITE.md                   # 새 사이트 추가하는 법
└── tests/
    ├── __init__.py
    ├── test_filter.py                # 필터 로직 단위 테스트
    └── fixtures/
        └── sample.html               # 샘플 HTML 픽스처
```

---

## 4. 모듈별 구현 상세

### 4.1 `src/sites/base.py` — 사이트 어댑터 인터페이스
```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Post:
    id: str          # 게시글 고유 ID (URL 또는 num)
    title: str
    url: str
    date: str        # YYYY-MM-DD
    site_key: str    # 사이트 식별자

class SiteAdapter(ABC):
    @abstractmethod
    def fetch(self) -> list[Post]:
        """게시판 목록 페이지를 파싱해 Post 리스트 반환"""
```
> 새 사이트 추가 시 이 클래스를 상속만 하면 됨. `sites.yml`에 등록.

### 4.2 `src/config.py` — 설정 로더
- `config/sites.yml`: 사이트 키, URL, CSS 셀렉터, 어댑터 클래스명
- `config/filters.yml`: `include: [...]`, `exclude: [...]` 키워드 리스트
- 환경변수 로드: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (Secrets에서 주입)

### 4.3 `src/crawler.py` — 어댑터 디스패처
- `sites.yml` 읽어 각 사이트 어댑터 인스턴스 생성 → `fetch()` 실행
- 단일 사이트 실패가 전체 실행을 막지 않도록 `try/except` 격리

### 4.4 `src/filter.py` — 키워드 필터링
- 제목 기준 매칭 (대소문자 무시, 부분 일치)
- `include`가 비어있으면 모든 글 통과 → 그 후 `exclude` 적용
- 둘 다 정의되어 있으면 AND 조합 (포함 ∩ 비제외)

### 4.5 `src/state.py` — 중복 방지
- `data/seen_ids.json`을 읽어 사이트별 이미 본 ID set으로 보유
- 새 ID만 필터링해서 반환
- 실행 후 새 ID를 추가해 저장 → 워크플로우가 커밋

### 4.6 `src/messenger.py` — Telegram 발신
- `https://api.telegram.org/bot<TOKEN>/sendMessage`
- HTML parse_mode 사용, 메시지당 4096자 제한 → 초과 시 분할
- 메시지 형식 예시:
  ```
  📋 오늘의 신규 청약 공고 (3건)

  [청약홈] 2026-05-23
  • <a href="...">○○ 아파트 1순위 모집공고</a>
  • <a href="...">△△ 신혼희망타운 공고</a>

  [LH] 2026-05-23
  • <a href="...">매입임대주택 입주자 모집</a>
  ```
- 새 글 0건이면 발신 안 함 (조용함)

### 4.7 `src/main.py` — 진입점
```python
def main():
    cfg = load_config()
    sites = build_adapters(cfg)
    seen = load_seen_ids()
    new_posts = []
    for site in sites:
        try:
            posts = site.fetch()
            posts = apply_filter(posts, cfg.filters)
            posts = [p for p in posts if p.id not in seen[site.key]]
            new_posts.extend(posts)
            seen[site.key].update(p.id for p in posts)
        except Exception as e:
            log_error(site.key, e)
    if new_posts:
        send_telegram_summary(new_posts)
    save_seen_ids(seen)
```

### 4.8 `.github/workflows/daily-notify.yml`
```yaml
name: Daily Notify
on:
  schedule:
    - cron: '0 0 * * *'   # UTC 00:00 = KST 09:00
  workflow_dispatch:       # 수동 실행 버튼

permissions:
  contents: write          # seen_ids.json 커밋 권한

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python -m src.main
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      - name: Commit updated state
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/seen_ids.json
          git diff --staged --quiet || git commit -m "chore: update seen_ids [skip ci]"
          git push
```

### 4.9 `requirements.txt`
```
requests>=2.31
beautifulsoup4>=4.12
lxml>=5.0
PyYAML>=6.0
```

---

## 5. GitHub 설정 가이드 (`docs/SETUP_GITHUB.md`)

> 레포 `jks-developer/webcrawling`는 이미 생성·clone되어 있음. 아래는 그 상태에서 이어지는 단계.

1. **소스 코드 작성 후 push**
   ```
   git add .
   git commit -m "feat: initial scaffolding"
   git push
   ```
2. **Secrets 등록** — GitHub 레포 페이지 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
   - `TELEGRAM_BOT_TOKEN` (BotFather에서 받은 값)
   - `TELEGRAM_CHAT_ID` (getUpdates 응답에서 추출)
3. **Actions 활성화** — `Actions` 탭 진입 → 워크플로우 인식 확인 → 필요 시 `I understand my workflows, go ahead and enable them` 클릭
4. **수동 테스트 실행** — `Actions` 탭 → `Daily Notify` → 우측 `Run workflow` 버튼
5. **로그 확인** — 실행 결과 클릭 → 각 step 로그 확인 (특히 `python -m src.main`, `Commit updated state`)
6. **스케줄 동작 확인** — 다음 날 09:00 KST에 자동 실행 발생 확인

---

## 6. Telegram 봇 설정 가이드 (`docs/SETUP_TELEGRAM.md`)

1. **봇 생성**
   - Telegram 앱에서 `@BotFather` 검색
   - `/newbot` → 봇 이름과 username 지정
   - 응답에 포함된 **HTTP API token** = `TELEGRAM_BOT_TOKEN`
2. **chat_id 획득**
   - 자신이 만든 봇과 대화창 열어서 `/start` 한 번 전송
   - 브라우저에서 `https://api.telegram.org/bot<TOKEN>/getUpdates` 접속
   - 응답 JSON에서 `"chat":{"id": 123456789}` 찾기 → 이 값이 `TELEGRAM_CHAT_ID`
3. **테스트 발신**
   - `https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<ID>&text=hello`
   - 봇으로부터 "hello" 메시지 수신 확인

---

## 7. 검증 계획

### 7.1 로컬 단위 테스트
- `python -m pytest tests/` — 필터 로직 검증
- `python -m src.main` 로컬 실행 (환경변수로 토큰 주입) → 콘솔 로그 + Telegram 수신 확인

### 7.2 샘플 사이트로 E2E
- `example_site.py` 어댑터가 정적 HTML 픽스처(`tests/fixtures/sample.html`)를 파싱하도록 작성
- 첫 실행: 모든 글이 새 글로 잡혀 알림 → `seen_ids.json` 갱신 확인
- 두 번째 실행: 새 글 0건 → 메시지 발송 안 됨 확인
- 픽스처에 새 항목 추가 → 해당 글만 알림 확인

### 7.3 GitHub Actions 검증
- Push 후 `workflow_dispatch`로 수동 실행
- 로그에서 각 단계 통과 확인
- `seen_ids.json` 자동 커밋 발생 확인
- 다음 날 09:00 KST 자동 실행 확인

### 7.4 실제 사이트 추가 시 검증
- 새 어댑터 작성 → 로컬 `fetch()` 단독 호출로 Post 리스트 확인
- 셀렉터 변경 대응 위해 fetch 결과가 0건이면 워크플로우 로그에 경고 출력

---

## 8. 작업 순서 (구현 단계)

1. 디렉토리 스캐폴딩 (`src/`, `config/`, `data/`, `docs/`, `tests/`, `.github/workflows/`)
2. `requirements.txt`, `.gitignore` 작성
3. `src/sites/base.py` — Post / SiteAdapter 정의
4. `src/sites/example_site.py` — 픽스처 기반 샘플 어댑터
5. `src/filter.py` + `tests/test_filter.py`
6. `src/state.py`
7. `src/messenger.py`
8. `src/config.py` + `config/sites.yml`, `config/filters.yml`
9. `src/crawler.py`, `src/main.py` (전체 오케스트레이션)
10. `.github/workflows/daily-notify.yml`
11. `docs/SETUP_GITHUB.md`, `docs/SETUP_TELEGRAM.md`, `docs/ADD_SITE.md`
12. `README.md` (개요 + 빠른 시작)
13. 로컬 E2E 검증 → 커밋/푸시
14. GitHub Secrets 등록 → 수동 workflow_dispatch 실행 → 결과 확인
15. (사용자 별도 작업) 실제 청약 사이트 URL/셀렉터 추가

---

## 9. 향후 확장 (현재 범위 외)

- 사이트별 RSS가 있다면 어댑터에서 우선 사용 (HTML 파싱보다 안정)
- Playwright 어댑터를 `base.py` 동일 인터페이스로 추가 (JS 렌더링 사이트 대응)
- 알림 시간 다중화 (cron 줄 추가만으로)
- 우선순위 키워드 → 별도 채널/이모지 강조
- 게시글 본문까지 일부 미리보기 포함
