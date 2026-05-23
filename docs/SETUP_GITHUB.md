# GitHub 설정 — 완전 초보용

이 프로젝트는 PC를 켜둘 필요 없이 **GitHub Actions**가 매일 정해진 시간에 크롤링 + 알림을 실행합니다. 이 문서는 GitHub을 처음 쓰는 분도 따라할 수 있도록 단계별로 안내합니다.

> 이미 레포가 있고 코드도 올려둔 상태라면 [5. Secrets 등록](#5-secrets-등록)부터 보시면 됩니다.

## 0. 사전 준비

- Telegram 봇 토큰과 chat_id가 손에 있어야 합니다 → [SETUP_TELEGRAM.md](./SETUP_TELEGRAM.md) 먼저 진행
- Git이 설치되어 있어야 합니다 → https://git-scm.com/downloads

## 1. GitHub 계정 만들기 (이미 있으면 건너뛰기)

1. https://github.com 접속 → `Sign up`
2. 이메일/비밀번호/사용자명 입력
3. 이메일 인증

## 2. 새 레포지토리 만들기

1. https://github.com 우상단 `+` → `New repository`
2. **Repository name**: `webcrawling` (또는 원하는 이름)
3. **Public** 선택 권장 — GitHub Actions가 무제한 무료
   - Private도 가능 (월 2000분 무료, 본 프로젝트는 분당 1회로 충분)
4. `Add a README file` 체크 (선택)
5. **Create repository** 클릭

## 3. 로컬 컴퓨터에 코드 받기

생성된 레포 페이지에서 초록색 `Code` 버튼 클릭 → HTTPS URL 복사

```powershell
# 원하는 작업 폴더에서
git clone https://github.com/<your_username>/webcrawling.git
cd webcrawling
```

## 4. 코드 작성 & push

본 프로젝트 파일들을 추가한 뒤:
```powershell
git add .
git commit -m "feat: initial scaffolding"
git push
```

> **여러 GitHub 계정 사용 시** push 중 권한 오류가 나면 [부록 A](#부록-a-여러-github-계정-쓰는-경우) 참고.

## 5. Secrets 등록

GitHub Actions가 사용할 비밀값을 등록합니다. **레포에 코드를 push한 뒤** 진행하세요.

1. 레포 페이지 → **`Settings`** 탭
2. 왼쪽 사이드바 → **`Secrets and variables`** → **`Actions`**
3. **`New repository secret`** 버튼
4. 다음 2개를 등록:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | BotFather가 준 토큰 |
| `TELEGRAM_CHAT_ID` | getUpdates로 알아낸 숫자 |

> 등록 후에는 Secret 값을 다시 볼 수 없습니다 (덮어쓰기만 가능). 토큰을 안전한 곳에도 따로 보관하세요.

## 6. Actions 활성화

1. 레포 페이지 → **`Actions`** 탭
2. (Public 레포의 경우) `I understand my workflows, go ahead and enable them` 클릭

워크플로우 `Daily Notify`가 보이면 성공.

## 7. 수동 테스트 실행

1. 좌측 사이드바에서 **`Daily Notify`** 클릭
2. 우측의 **`Run workflow`** 드롭다운 → 다시 **`Run workflow`** 클릭
3. 1~2분 대기 → 노란 점이 초록 체크로 바뀜

## 8. 결과 확인

성공 시:
- ✅ **Telegram에 요약 메시지** 도착 (새 글이 있을 때만)
- ✅ **Actions 로그**에 `sent N Telegram message(s)` 라인 표시
- ✅ **`chore: update seen_ids [skip ci]` 자동 커밋** 발생 (Commits 탭에서 확인)

실패 시 (빨간 X):
- 실행 결과 클릭 → 단계별 로그에서 빨간 step 확인
- 흔한 원인: Secrets 이름 오타, 토큰 만료, chat_id 잘못된 값

## 9. 일정 동작 확인

별도 조작 없이 다음 날 09:00 KST(=UTC 00:00)에 자동 실행됩니다. Actions 탭에 새 run이 생기는지 확인하세요.

> ⚠️ GitHub은 부하 상황에 따라 cron 트리거를 수십 분 늦출 수 있습니다. 본 프로젝트는 분 단위 정밀도가 필요 없으므로 정상.

## 운영 시 흔히 하는 작업

| 작업 | 방법 |
|------|------|
| 알림 시간 변경 | `.github/workflows/daily-notify.yml`의 `cron` 수정 → push |
| 키워드 변경 | `config/filters.yml` 편집 → push |
| 사이트 추가 | [ADD_SITE.md](./ADD_SITE.md) 참고 |
| 토큰 교체 | Settings → Secrets에서 해당 Secret 업데이트 (코드 변경 없음) |
| 알림 일시 중단 | `config/sites.yml`에서 모든 사이트 `enabled: false` 또는 워크플로우 `Disable workflow` |

## 부록 A: 여러 GitHub 계정 쓰는 경우

회사용과 개인용 계정을 분리해서 쓰고 있으면, push가 권한 오류로 막힐 수 있습니다.

**해결 방법: 이 레포에만 적용되는 로컬 설정** (다른 프로젝트 영향 0)
```powershell
cd <project_root>
git config --local credential.useHttpPath true
git config --local user.name "<github_username>"
git config --local user.email "<github_email>"
```

이후 push 시 브라우저 팝업이 한 번 뜸 → 원하는 계정으로 로그인하면 GCM이 이 레포 경로 전용으로 자격을 저장합니다. 다른 레포 영향 없음.
