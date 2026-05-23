# 새 사이트 추가하기

본 프로젝트는 한 번 셋업하면 **사이트는 yaml 한 항목만 추가**하면 알림 대상이 됩니다. 사이트가 정적 HTML이면 코드 작성 없이 끝납니다.

## 두 가지 경로

| 경로 | 사용 시점 | 작업량 |
|------|----------|-------|
| **A. 셀렉터 추가만** (대부분) | 게시판이 정적 HTML이고 목록이 HTML로 바로 보임 | yaml 한 항목 (3분) |
| **B. 새 어댑터 클래스** | JS로 동적 로딩, 로그인 필요, JSON API 사용 등 특수 케이스 | Python 한 파일 (30분~) |

## 경로 A — 셀렉터만 추가

### 단계 1: 사이트 분석

브라우저 개발자 도구(F12) → Elements 탭으로 게시판 페이지 구조 확인.

찾아야 할 셀렉터 5개:
| 키 | 의미 | 예시 |
|----|------|------|
| `row` | 게시글 한 행을 감싸는 요소 | `tr.board-row` |
| `title` | 제목이 들어있는 요소 | `td.subject a` |
| `link` | 게시글 상세 URL이 들어있는 요소 + 속성 | `td.subject a@href` |
| `id` | 게시글 고유 식별자 + 속성 (URL에 있다면 URL을 그대로 써도 OK) | `td.subject a@data-num` |
| `date` (선택) | 작성일 텍스트 | `td.date` |

### 셀렉터 문법

- `selector@attr` → 매치된 요소의 `attr` 속성값
- `selector` (속성 없이) → 매치된 요소의 텍스트 (앞뒤 공백 제거)
- 비어 있는 키는 무시 (`id`가 없으면 url을 id로 사용)

### 단계 2: `config/sites.yml` 항목 추가

```yaml
sites:
  - key: chungyak_home
    name: 청약홈
    adapter: example_site.ExampleSite
    url: https://www.applyhome.co.kr/ai/aia/selectAptInfoView.do
    selectors:
      row: "table.tbl_st tbody tr"
      title: "td.tal a"
      link: "td.tal a@href"
      id: "td.tal a@data-houseManageNo"
      date: "td:nth-child(6)"
    enabled: true
```

- `key`: 영문 식별자. `seen_ids.json`의 버킷 키로 사용됨
- `name`: Telegram 메시지에 표시될 한글 이름
- `enabled`: false로 두면 실행 시 스킵

### 단계 3: 로컬 검증

```powershell
cd <project_root>
.venv\Scripts\python.exe -c "from src.sites.example_site import ExampleSite; from src.config import parse_sites; from pathlib import Path; sites = parse_sites(Path('config/sites.yml')); a = next(s for s in sites if s.key=='chungyak_home'); ad = ExampleSite(key=a.key, url=a.url, selectors=a.selectors); print(ad.fetch())"
```

또는 간단히 전체 파이프라인 실행:
```powershell
.venv\Scripts\python.exe -m src.main
```

- 게시글이 잘 추출되면 성공
- `fetched 0 posts`가 뜨면 셀렉터가 매치되지 않은 것 → row/title 셀렉터 다시 확인

### 단계 4: 커밋 & push

```powershell
git add config/sites.yml
git commit -m "feat: add chungyak_home site"
git push
```

GitHub Actions가 다음 스케줄에 자동으로 새 사이트를 처리합니다.

## 경로 B — 새 어댑터 클래스 작성

JS 렌더링/로그인/API 응답 등이 필요한 경우. 다음을 작성합니다.

### 단계 1: `src/sites/<my_site>.py` 생성

```python
from __future__ import annotations
from src.sites.base import Post, SiteAdapter


class MySite(SiteAdapter):
    def __init__(self, key: str, url: str, selectors: dict[str, str]) -> None:
        self.key = key
        self.url = url
        self.selectors = selectors   # 자유롭게 활용

    def fetch(self) -> list[Post]:
        # 어떤 방식으로든 게시글 목록을 만들어 반환
        # - requests + BeautifulSoup
        # - Playwright (별도 의존성 추가 필요)
        # - 사이트의 JSON API
        return [
            Post(
                id="고유ID",
                title="제목",
                url="상세 URL",
                date="2026-05-23",
                site_key=self.key,
            ),
            ...
        ]
```

### 단계 2: `config/sites.yml`에 어댑터 클래스 명시

```yaml
sites:
  - key: my_site
    name: 우리 사이트
    adapter: my_site.MySite          # 파일명.클래스명
    url: https://example.com/board
    selectors: {}                     # 어댑터가 직접 정의
    enabled: true
```

`crawler.build_adapter`는 `src.sites.<module>` 경로에서 클래스를 동적으로 import 합니다.

### 단계 3: 검증

로컬 실행 → 추출 결과 확인 → 의도대로 동작 → push.

## 운영 팁

- **셀렉터가 깨졌을 때 인지**: 사이트 개편으로 fetch 결과 0건이 되어도 워크플로우는 성공으로 표시됩니다. Actions 로그에서 `fetched 0 posts from <key>` 라인을 주기적으로 확인하세요.
- **너무 자주 폴링하지 않기**: 본 프로젝트는 1일 1회 기본이라 사이트에 부담이 없지만, cron 주기를 줄일 때는 robots.txt와 사이트 약관을 확인하세요.
- **User-Agent**: `ExampleSite`는 기본 UA로 `webcrawling-notifier/0.1`를 보냅니다. 사이트가 봇을 차단하면 어댑터에서 UA를 변경하세요.
- **인코딩**: BeautifulSoup + lxml 조합은 대부분의 한글 사이트를 자동 디코딩합니다. 깨지면 `requests.Response.encoding`을 수동 설정해보세요.
