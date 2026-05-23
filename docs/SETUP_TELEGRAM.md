# Telegram 봇 설정

이 프로젝트는 Telegram Bot API로 메시지를 보냅니다. 처음 1회만 봇을 만들고 토큰/chat_id를 확보하면 됩니다.

## 1. 봇 생성 — BotFather

1. Telegram 앱(모바일/데스크톱)에서 **`@BotFather`** 검색 → 대화 시작
2. `/newbot` 입력
3. BotFather가 묻는 두 항목을 입력
   - **이름 (Display name)**: 한글 가능, 예 `청약 알림`
   - **Username**: 영문, `_bot`으로 끝나야 함, 예 `chungyak_notify_bot`
4. 응답 메시지에서 **HTTP API token**을 복사
   - 형식 예: `7212345678:AAEa-XXX-XXXXXXXXXXXXX`
   - 이 값이 환경변수 `TELEGRAM_BOT_TOKEN` 값

> 토큰이 노출되면 누구나 봇을 조작할 수 있습니다. 절대 git에 커밋하지 마세요. (이 레포의 `.gitignore`가 `.env`를 차단합니다.)

## 2. chat_id 확보

봇은 **상대방이 먼저 시작한 채팅**에만 메시지를 보낼 수 있습니다. 자기 자신에게 보내려면 본인이 자기 봇과 채팅을 시작해야 합니다.

1. BotFather 응답에 포함된 `t.me/<your_bot_username>` 링크 클릭 → 봇 채팅창 열기
2. 채팅창 하단 파란색 **`START`** 버튼 누르기 (또는 `/start` 입력)
3. 봇에게 아무 메시지 한 번 전송 (예: `hi`)
4. 브라우저에서 아래 URL 접속 (TOKEN 자리에 1단계 토큰 붙여넣기)
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
5. 응답 JSON에서 `"chat":{"id": 1234567890, ...}` 찾기
   - 이 숫자가 환경변수 `TELEGRAM_CHAT_ID` 값

### `result: []` 만 보이면

- 봇 채팅창에서 **`START` 버튼을 누르지 않았을 가능성**이 큼 — 다시 확인
- 메시지를 보낸 후 5~10초 대기하고 새로고침
- 토큰을 올바르게 복사했는지 확인 (콜론 `:` 포함)

## 3. 동작 확인 (선택)

브라우저에서 다음 URL을 누르면 즉시 봇이 메시지를 보냅니다.
```
https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=hello
```

봇 채팅창에 `hello` 메시지가 도착하면 정상.

## 4. 등록

확보한 두 값을 다음 두 곳에 등록합니다.

### 로컬 `.env` 파일 (개발용)
프로젝트 루트에 `.env` 파일을 만들고:
```env
TELEGRAM_BOT_TOKEN=7212345678:AAEa-XXX-XXXXXXXXXXXXX
TELEGRAM_CHAT_ID=1234567890
```

> `.env`는 `.gitignore`에 의해 git에서 제외됩니다.

### GitHub Secrets (운영용)
GitHub 레포 → **Settings** → **Secrets and variables** → **Actions** → `New repository secret`
- Name `TELEGRAM_BOT_TOKEN` / Value: 1단계 토큰
- Name `TELEGRAM_CHAT_ID` / Value: 2단계 숫자

자세한 GitHub 설정은 [SETUP_GITHUB.md](./SETUP_GITHUB.md) 참고.

## 트러블슈팅

| 증상 | 원인/해결 |
|------|----------|
| `Unauthorized` 401 | 토큰 오타 또는 봇 삭제됨 → 다시 발급 |
| `Bad Request: chat not found` | chat_id가 잘못되었거나, 사용자가 봇과 대화를 시작하지 않음 |
| `Forbidden: bot was blocked by the user` | 사용자가 봇을 차단함 → Telegram에서 봇 차단 해제 |
| `Too Many Requests` 429 | 일시적 레이트 리밋 → 잠시 후 재시도 |
