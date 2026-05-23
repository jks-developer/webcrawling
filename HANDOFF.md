# HANDOFF — 다음 세션 인수인계 문서

> 본 문서는 **현재 세션 종료 시점의 프로젝트 상태**와 **다음 세션이 바로 이어할 수 있는 작업 지침**을 담는다.
> 작성: 2026-05-23 (최초), 갱신: 2026-05-23 (LH 추가 + 어댑터 레벨 지역 필터 도입)

---

## 1. 현재 상태 한 줄 요약

청약/공급 게시판 → Telegram 일일 알림 시스템이 **운영 가능 상태**.
현재 **7개 사이트** (중기부 경기 + SH 서울 + GH 경기 + 청약홈 APT + 청약홈 무순위/잔여 + LH 청약플러스 임대 + LH 청약플러스 분양) 등록 완료.
전국 통합 게시판(청약홈 / LH) 4개에는 **어댑터 레벨 지역 필터**(`allowed_regions: [서울, 경기]`)가 적용되어 비수도권 단일지역 글이 차단된다.

---

## 2. 프로젝트 위치 & 레포

| 항목 | 값 |
|------|-----|
| 로컬 경로 | `E:\99.Personal Dev\09.etc\webcrawling` |
| GitHub 레포 | https://github.com/jks-developer/webcrawling |
| 브랜치 | `master` |
| 인증된 git user (local) | `jks-developer` / `kwangsoon3931@gmail.com` |
| GCM 설정 | `credential.useHttpPath = true` (이 레포만, local) |
| `gh` 인증 계정 | `jangkwangsoon` (read 권한만, workflow_dispatch는 admin 권한 없음) |

> ⚠️ `gh` 인증 계정(`jangkwangsoon`)은 레포 admin이 아니라 **workflow_dispatch 트리거 불가**. CI 수동 실행은 **브라우저에서 jks-developer로 로그인 후 Actions → Run workflow** 사용.
> 또는 다음 세션에서 `gh auth login`으로 jks-developer 계정 추가하면 gh로도 트리거 가능.

---

## 3. 운영 중인 알림 설정

### 3.1 Telegram
- 봇 username: `Applyhome_notify_bot`
- 토큰/chat_id: `.env` (로컬), GitHub Secrets `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (CI)

### 3.2 GitHub Actions
- 워크플로우: `.github/workflows/daily-notify.yml` (active)
- 스케줄: 매일 **KST 09:00** (`cron: '0 0 * * *'` UTC)
- 권한: `contents: write` — 워크플로우가 `data/seen_ids.json` 자동 커밋 후 push

### 3.3 등록된 사이트 (`config/sites.yml`)
| key | name | status | adapter | 지역 필터 |
|-----|------|--------|---------|-----------|
| `mss_gyeonggi` | 중기부 경기 (특별공급) | ✅ enabled | `mss_gyeonggi.MssGyeonggi` (custom) | 사이트 자체 경기 한정 |
| `sh_seoul` | SH 서울주택도시공사 | ✅ enabled | `sh_seoul.SHSeoul` (custom: onclick `getDetailView`) | 사이트 자체 서울 한정 |
| `gh_gyeonggi` | GH 경기주택도시공사 | ✅ enabled | `gh_gyeonggi.GHGyeonggi` (custom: articleNo + date normalize) | 사이트 자체 경기 한정 |
| `applyhome_apt` | 청약홈 APT 분양/임대 | ✅ enabled | `applyhome.ApplyhomeApt` (custom: `data-hmno`/`data-pbno` + GET 디테일) | `allowed_regions: [서울, 경기]` |
| `applyhome_remndr` | 청약홈 APT 무순위/잔여세대 | ✅ enabled | `applyhome.ApplyhomeRemndr` (custom: same base, REMNDR detail URL) | `allowed_regions: [서울, 경기]` |
| `lh_apply_rental` | LH 청약플러스 임대주택 | ✅ enabled | `lh_apply.LHApply` (custom: `wrtancInfoBtn` data-id + mi 분기) | `allowed_regions: [서울, 경기]` |
| `lh_apply_sale` | LH 청약플러스 분양주택 | ✅ enabled | `lh_apply.LHApply` (custom: 같은 클래스, `mi=1027`) | `allowed_regions: [서울, 경기]` |
| `example` | 예시 사이트 (스캐폴딩용) | disabled | `example_site.ExampleSite` (generic CSS) | — |

### 3.4 필터 (`config/filters.yml`)
```yaml
include: []
exclude: [당첨자, 발표, 결과, 취소, 완료, 종료, 마감]
```

---

## 4. 아키텍처 요약 (다음 세션이 코드 다시 안 읽어도 되도록)

```
src/main.py
   → load_config()           # config/*.yml + .env/Secrets
   → fetch_all(sites)        # 각 사이트별 어댑터 import + fetch
       → SiteAdapter.fetch() # Post[] 반환
   → apply_filter()          # 포함/제외 키워드
   → state.is_seen() 로 중복 제거
   → send_summary()          # Telegram에 HTML 메시지
   → save_state()            # data/seen_ids.json 갱신
```

핵심 파일:
- `src/sites/base.py` — `Post` + `SiteAdapter` 인터페이스
- `src/sites/example_site.py` — 정적 HTML + CSS 셀렉터 기반 일반 어댑터
- `src/sites/mss_gyeonggi.py` — onclick 파싱이 필요한 커스텀 어댑터 (좋은 참고 사례)
- `src/config.py` — yaml + .env 로더
- `src/crawler.py` — 어댑터 동적 import 디스패처
- `src/main.py` — 오케스트레이션 진입점
- `tests/test_*.py` — 59개 테스트, `pytest tests/ -v` 로 실행

---

## 5. 새 사이트 추가하는 표준 절차 (이 패턴을 그대로 반복)

> 다음 세션에서 N번째 청약 사이트 추가할 때, 본 절차를 그대로 따르면 됨.
> 자세한 설명: `docs/ADD_SITE.md`

### Step 1 — 대상 사이트 정보 수집
- 게시판 URL (목록 페이지)
- 사이트 식별 키 (snake_case, 예: `lh_chungyak`)
- 표시 이름 (Telegram 메시지에 나올 한글, 예: `LH 청약센터`)
- (선택) 알림 키워드 추가 필요한지

### Step 2 — 페이지 구조 분석
```bash
cd "E:/99.Personal Dev/09.etc/webcrawling"
# 1) WebFetch 로 페이지 개요 파악
# 2) requests + BeautifulSoup 로 raw HTML 받아서 row 구조 확인
.venv/Scripts/python.exe -c "
import requests
from bs4 import BeautifulSoup
r = requests.get('<URL>', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
soup = BeautifulSoup(r.text, 'lxml')
# table/tr/td 또는 ul/li 등의 패턴 찾기, 첫 row 의 HTML 출력해서 검토
"
```
- **정적 HTML + 셀렉터로 충분**한 경우 → 경로 A (yaml만 추가)
- **onclick/JS 핸들러로 URL 구성** 또는 **JSON API/JS 렌더링** → 경로 B (커스텀 어댑터)

### Step 3-A — yaml 한 항목 추가 (정적 + 셀렉터 OK)
`config/sites.yml`에 추가:
```yaml
  - key: <site_key>
    name: <표시 이름>
    adapter: example_site.ExampleSite
    url: <URL>
    selectors:
      row: "<row CSS selector>"
      title: "<title CSS selector>"
      link: "<link CSS selector>@href"
      id: "<id CSS selector>@<attr>"      # 비우면 url을 id로 사용
      date: "<date CSS selector>"          # 선택
    enabled: true
```

### Step 3-B — 커스텀 어댑터 (URL이 href에 없거나 특수 처리 필요)
1. **테스트 픽스처 저장** — 현재 페이지 HTML을 `tests/fixtures/<key>_sample.html` 로 저장
2. **`src/sites/<key>.py` 작성** — `mss_gyeonggi.py`를 참고. SiteAdapter 상속, fetch() 구현
3. **`tests/test_<key>.py` 작성** — fixture 기반 단위 테스트 (5개 정도)
4. **`config/sites.yml`에 등록** — `adapter: <key>.<ClassName>` 형식

### Step 4 — 로컬 검증
```bash
.venv/Scripts/python.exe -m pytest tests/ -v        # 모든 테스트 통과 확인
.venv/Scripts/python.exe -c "
from src.sites.<key> import <ClassName>
posts = <ClassName>(key='<key>', url='<URL>').fetch()
print(len(posts), 'posts')
for p in posts: print(p.id, p.title)
"
```

### Step 5 — 커밋 + 사용자 승인 후 push
```bash
git add src/sites/<key>.py tests/test_<key>.py tests/fixtures/<key>_sample.html config/sites.yml
git commit -m "feat: add <site_name> adapter"
# 🔒 사용자에게 push 승인 요청 (master 직접 push 차단 규칙 있음 → 수동 승인 필요)
git push origin master
```

### Step 6 — CI 검증
1. **브라우저**에서 https://github.com/jks-developer/webcrawling/actions → `Daily Notify` → `Run workflow`
2. `gh run list --repo jks-developer/webcrawling --workflow="Daily Notify" --limit 1` 로 ID 확인
3. `gh run view <id> --repo jks-developer/webcrawling --log` 로 로그 확인
4. Telegram 알림 도착 확인
5. `git pull` 로 seen_ids 자동 커밋 sync

---

## 6. 알려진 제약/주의 사항

### 6.1 git push 차단
- 사용자 환경에 master 직접 push 차단 규칙 있음
- 매 commit 후 push 시 **사용자가 수동으로 허용**해야 함
- 자동화 우회 금지 (사용자 의도)

### 6.2 gh CLI 권한 한계
- `gh` 인증 계정(`jangkwangsoon`)은 `jks-developer/webcrawling`에 admin 권한 없음
- workflow_dispatch는 403 → 브라우저 트리거 사용
- read 작업(`gh run list/view`)은 가능
- 다음 세션에서 `gh auth login`으로 jks-developer 추가하면 더 편함

### 6.3 Python 환경
- 가상환경: `.venv` (Python 3.13 로컬, CI는 3.11)
- 런타임 deps: `requirements.txt`
- 테스트 deps: `requirements-dev.txt` (pytest 포함)
- 활성화 명령: `.venv\Scripts\python.exe ...` (직접 호출 권장)

### 6.4 콘솔 한글 깨짐
- Windows PowerShell cp949 콘솔에서 한글 출력이 깨져 보이지만 **데이터 자체는 정상**
- Telegram/파일 IO/HTTP 송신은 모두 UTF-8로 처리됨

### 6.5 파일 line ending (CRLF/LF)
- Python의 `Path.write_text(...)`는 Windows에서 CRLF 출력 → 기존 LF 파일 수정 시 diff에 잡힘
- 검증용 임시 mutation 후 `git checkout -- <file>`로 원본 복원 가능

### 6.6 seen_ids 자동 커밋
- 워크플로우가 `github-actions[bot]` 계정으로 `data/seen_ids.json` 자동 커밋 + push
- 로컬에서 작업 시작 전 `git pull` 필수

### 6.7 필터 변경 시 영향
- `filters.yml`의 exclude 키워드 변경 → 다음 실행부터 적용
- **이미 seen_ids에 있는 글은 알림 안 옴**. 새로 필터를 통과시키더라도 이미 본 글이면 silent
- 이전에 필터로 제외됐던 글을 강제 알림받고 싶다면 seen_ids에서 해당 ID 제거 (또는 사이트 키 통째로 리셋)

### 6.8 어댑터 레벨 지역 필터 (`options.allowed_regions`)
- `config/sites.yml`의 사이트 항목에 `options.allowed_regions: [서울, 경기]`를 적으면, 어댑터가 row의 지역 컬럼을 보고 비매칭 글을 drop.
- 디스패처(`src/crawler.py`)가 `options` dict를 어댑터 `__init__`에 키워드로 unpack. 옵션이 없으면 기존 동작(전국 통과)과 동일 — 회귀 없음.
- 매칭 규칙(`src/sites/base.region_passes`):
  - **substring 매칭** — `서울`은 `서울특별시`/`서울` 모두 매칭. 광역시도 풀네임/단축형 양쪽 호환.
  - **fail-open** — `""`/`-`/`전국`/`수도권`/`공통`/`OOO 외` 표기는 모두 통과. 누락 위험을 노이즈보다 우선시.
  - **현재 적용 대상**: `applyhome_apt`, `applyhome_remndr`, `lh_apply_rental`, `lh_apply_sale` 4개 (모두 전국 통합 게시판).
- 인천을 제외 결정: §7.1 참고. 단 `인천광역시 외`는 부천(=경기) 포함 가능성으로 fail-open 통과.
- 사이트별 row 지역 컬럼:
  - 청약홈 APT/Remndr: td[0] (단축형 `서울`/`경기`/`강원`...)
  - LH 임대/분양: td[3] (풀네임 `서울특별시`/`경기도`/`대구광역시 외`...)

---

## 7. 다음 세션이 할 일

### 7.1 사이트 추가 추천 진행 상황 (2026-05-23 결정)

사용자 조건: **서울+경기**, 4유형(민영분양/공공분양/공공임대/특별공급) 커버, **top 3-5 우선순위**.

특별공급 별도 사이트 조사 결과: **신혼/생애최초/신생아 특별공급 전용 게시판 사이트는 없음**. 마이홈포털(JS 동적 렌더링, Playwright 필요)·뉴:홈(정책 안내 중심)은 부적합. 모두 청약홈/LH/SH/GH 통합 게시판에 게시됨.

| 차수 | 사이트 | 상태 | 비고 |
|------|--------|------|------|
| 1차 | SH 서울주택도시공사 | ✅ 완료 | 정적 HTML + onclick `getDetailView` 파싱 |
| 1차 | GH 경기주택도시공사 | ✅ 완료 | 정적 HTML + articleNo 추출 + 날짜 정규화 |
| 2차 | 청약홈 APT 분양/임대 (applyhome.co.kr) | ✅ 완료 | 정적 HTML + `data-hmno` 속성 + GET 디테일 URL |
| 2차 | 청약홈 APT 무순위/잔여세대 | ✅ 완료 | 같은 base 클래스, REMNDR 디테일 URL만 다름 |
| 2차 | 청약홈 오피스텔/도시형/민간임대 | ⚠️ 미추가 | 디테일 GET 응답이 1.8KB 에러 페이지. 추후 POST/세션쿠키 조사 필요 |
| 3차 | LH 청약플러스 임대주택 (`mi=1026`) | ✅ 완료 | 콜드 세션 GET 정상. `wrtancInfoBtn` data-id 4개로 디테일 URL 재조립. `YYYY.MM.DD` 정규화. em.day 제거 |
| 3차 | LH 청약플러스 분양주택 (`mi=1027`) | ✅ 완료 | 같은 클래스 (`LHApply`), 보드 분기는 yaml URL의 `mi` 파라미터로 |
| 3차 | LH 청약플러스 토지/상가 (`mi=1062/1069`) | ❌ 사용자 결정 | 청약 4유형 범위 밖 |
| — | **어댑터 레벨 지역 필터 도입** | ✅ 완료 | `options.allowed_regions` + 디스패처 unpack + fail-open 정책 (§6.8) |
| 제외 | iH 인천도시공사 | ❌ 사용자 결정 | 서울+경기 범위 밖 |

### 7.2 즉시 할 작업

- [ ] **운영 모니터링 (1~2일)**: LH 보드가 매일 09:00 KST cron에서 정상 fetch 되는지 + 알림 도착 확인
- [ ] (선택) 청약홈 오피스텔/도시형/민간임대 보드 디테일 GET 분석 재시도 (`selectPRMOLttotPblancDetailView.do`)
- [ ] (선택) 라이브 운영 후 노이즈가 많으면 `allowed_regions` 정책 조정 — 예: `'외'` 자동 통과를 끄고 본부명(`서울지역본부`/`경기지역본부`) 화이트리스트 추가
- [ ] 사이트별로 필요한 키워드 조정 필요 시 `filters.yml` 업데이트

> 어댑터 추가 패턴/아키텍처는 `CLAUDE.md` 참고.

### 7.3 운영 모니터링 (낮은 우선순위)
- [ ] 매일 09:00 KST cron 실행 후 Actions 탭에서 결과 확인 (첫 며칠만)
- [ ] 사이트별 셀렉터 깨짐 모니터링 (`fetched 0 posts from <key>` 로그 패턴)
- [ ] seen_ids.json 비대해지면 (사이트당 1000 도달) 자동 evict 동작 확인

### 7.4 잠재 개선 (선택, 사용자 요청 시)
- 사이트별 필터 (현재는 글로벌)
- JS 렌더링 사이트 대응 시 Playwright 어댑터 도입 (의존성 추가됨)
- 실패 시 Telegram 알림 (현재는 GitHub의 워크플로우 실패 이메일만)
- RSS 피드 활용 (안정성 향상)

---

## 8. 다음 세션 빠른 시작 체크리스트

새 세션이 본 프로젝트에 들어오면:

1. ☐ 본 `HANDOFF.md` 읽기 (지금 이 문서)
2. ☐ `PLAN.md` / `EXECUTION_PLAN.md` 훑기 (배경)
3. ☐ `git log --oneline -10` 으로 최근 커밋 확인
4. ☐ `git pull origin master` 로 원격 동기화 (CI auto-commit 받기)
5. ☐ `cat data/seen_ids.json` 으로 현재 추적 중인 ID 확인
6. ☐ `.venv` 존재 확인 (없으면 `python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements-dev.txt`)
7. ☐ `pytest tests/` 실행해 회귀 없는지 확인
8. ☐ 사용자에게 다음 추가할 사이트 정보 요청

---

## 9. 핵심 커밋 히스토리 참조

```
d48f013 chore: update seen_ids [skip ci]                              ← CI 자동
848451c fix: restore exclude list for completed/result posts          ← 필터 복원
e70463d feat: add MSS Gyeonggi bulletin board adapter                 ← P7 (참고 사례)
7b41100 docs: add setup guides and rewrite README                     ← P6
c72b68f chore: disable example adapter and reset seen_ids             ← C-cleanup
aa70f55 chore: update seen_ids [skip ci]                              ← P5 CI 자동
2d1e1ea feat: add GitHub Actions daily-notify workflow                ← P5
47cf008 feat: add config loader, dispatcher, and main orchestration   ← P4
5062196 feat: add Telegram messenger and CSS-selector site adapter    ← P3
0d06ed7 feat: add core domain (Post, filter, state) with unit tests   ← P2
a0f59bc chore: scaffold project structure and planning docs           ← P1
```

새 사이트 추가의 좋은 참고 사례: `e70463d` (mss_gyeonggi adapter 추가 패턴)

---

## 10. 연락 / 위치 메모

- 프로젝트 메인 문서: `README.md`
- 설계 의도: `PLAN.md`
- 단계별 실행 계획: `EXECUTION_PLAN.md`
- Telegram 설정 가이드: `docs/SETUP_TELEGRAM.md`
- GitHub Actions 설정 가이드: `docs/SETUP_GITHUB.md`
- 새 사이트 추가 가이드: `docs/ADD_SITE.md`
- 본 인수인계 문서: `HANDOFF.md` ← 항상 최신화 권장
