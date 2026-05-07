# Chrome Web Store — release từ GitHub Actions

Workflow: [.github/workflows/cws-publish.yml](../.github/workflows/cws-publish.yml)

## Trigger

- Push tag khớp `release/**` (ví dụ `release/v1.0.0`).

Job **build-extension** luôn chạy: `pnpm install`, `pnpm --filter extension build`, zip thư mục `.output/chrome-mv3`, upload artifact.

Job **publish-cws** upload lên CWS **chỉ khi** đủ secrets (thiếu secret → log `::notice::` và thoát 0).

## GitHub Secrets (không commit vào repo)

| Secret | Mô tả |
|--------|--------|
| `CWS_EXTENSION_ID` | ID extension trên Developer Dashboard |
| `CWS_CLIENT_ID` | OAuth Client ID (Chrome Web Store API) |
| `CWS_CLIENT_SECRET` | OAuth Client Secret |
| `CWS_REFRESH_TOKEN` | Refresh token cho upload |

Lấy credential theo [Chrome Web Store API](https://developer.chrome.com/docs/webstore/using-api) (Chrome Developer Dashboard → nhóm API).

## Checklist thủ công (vẫn có thể cần tay)

- **UptimeRobot / monitoring**: không có IaC trong repo — cấu hình trên dashboard UptimeRobot (xem deferred-work W8).
- **Review CWS**: sau upload có thể cần submit for review trong Developer Dashboard.
- **OAuth Google extension**: biến `GOOGLE_OAUTH_CLIENT_ID` cho build extension là bước riêng (local / CI build), không thay thế secrets CWS ở trên.
