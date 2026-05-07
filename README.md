# Voice-Pro — Universal Video Dubber

> **Nghe bất kỳ video nào bằng ngôn ngữ của bạn — không phải subtitle, mà là giọng nói thật.**

Chrome Extension + SaaS backend cho phép người dùng nghe dubbed audio của bất kỳ video YouTube nào bằng ngôn ngữ mẹ đẻ, đồng bộ hoàn toàn với video gốc. Pipeline: **Faster-Whisper STT → Neural MT → Edge-TTS** — chạy in-browser, không upload file, không rời khỏi trang.

---

## Tại sao sản phẩm này tồn tại

~1.5 tỷ người không nói tiếng Anh đang tiêu thụ content YouTube, Coursera, và các nền tảng video. 90%+ nội dung chất lượng cao tồn tại chủ yếu bằng tiếng Anh. Subtitle đòi hỏi cognitive load đọc song song với xem — **audio dubbing giải phóng hoàn toàn giới hạn đó.**

**Không có competitor nào** đang triển khai audio dubbing ở browser extension level với chất lượng này:

| Competitor | Approach | Gap |
|---|---|---|
| Language Reactor (500K users) | Subtitle only | Không có audio dubbing |
| Papago / DeepL Extension | Text translation | Không xử lý audio/video |
| Maestra / HappyScribe | Upload-based SaaS | Không phải browser-native |
| ElevenLabs Dubbing | Upload API | $50+/month, không có extension |

---

## Tính năng

### MVP (Phase 1 — Tháng 1-3)

- **Dub Mode** — thay toàn bộ audio bằng giọng nói ngôn ngữ đích
- **10 ngôn ngữ:** Tiếng Việt, Nhật, Hàn, Tây Ban Nha, Bồ Đào Nha, Indonesia, Hindi, Đức, Pháp, Ả Rập
- **YouTube support** (primary platform, no DRM)
- **Credit system:** 10 phút/tháng miễn phí → $9/month (120 phút) → $19/month (unlimited)
- **DRM detection** + graceful error cho Netflix, Disney+, Amazon Prime
- Web dashboard: số dư credits, lịch sử, billing

### Growth (Phase 2 — Tháng 4-9)

- **Learn Mode** — audio song ngữ xen kẽ gốc + dịch (cho học ngôn ngữ)
- **Shadow Mode** — luyện phát âm với Whisper scoring
- Mở rộng platform: Coursera, Vimeo, Udemy, bất kỳ HTML5 video
- Voice cloning (F5-TTS), auto-dub khi mở video

### Vision (Phase 3 — Tháng 10+)

- VoiceOS full platform
- API tier cho developers
- Real-time dubbing cho live streams
- Firefox Android + Safari iOS
- Team/family plans

---

## Kiến trúc

### Monorepo Structure

```
voice-pro/
├── extension/     # WXT (Chrome Extension Manifest V3)
├── dashboard/     # Vite + React 19 + shadcn/ui (SPA)
├── landing/       # Next.js 15 App Router (SSG/SEO)
├── backend/       # Python FastAPI + Celery
├── shared/        # TypeScript types dùng chung
└── README.md
```

### Audio Pipeline

```
tabCapture API → PCM 16kHz mono →  POST /api/v1/pipeline/process-chunk
                                          ↓
                              Faster-Whisper STT (RunPod GPU)
                                          ↓
                              Deep-Translator (Neural MT)
                                          ↓
                              Edge-TTS synthesis
                                          ↓
                    audio/mpeg stream → Web Audio API inject → video sync
```

**Latency targets:** first chunk ≤ 3s, subsequent chunks ≤ 1.5s, sync offset ≤ 300ms

### Tech Stack

| Layer | Technology |
|---|---|
| Extension | WXT v0.20+ · React 19 · TypeScript 5.7 |
| Dashboard | Vite · React 19 · shadcn/ui v4 · Tailwind CSS v4 |
| Landing | Next.js 15 App Router · SSG · Tailwind CSS v4 |
| Backend | Python 3.11+ · FastAPI · Celery · SQLAlchemy 2.x |
| Database | PostgreSQL 17 (port **5434**) · Alembic |
| Cache/Queue | Redis 7 (Docker, host port **6380**) |
| STT | Faster-Whisper (RunPod Serverless GPU) |
| TTS | Edge-TTS (400+ voices, miễn phí) |
| Translation | Deep-Translator |
| Billing | Stripe |
| Auth | JWT + Google OAuth (extension) · bcrypt (dashboard) |
| Infra | Hetzner CPX22 VPS · Docker Compose · Nginx · Certbot |
| CI/CD | GitHub Actions → SSH deploy · Chrome Web Store auto-publish |
| Monitoring | Sentry · Plausible · UptimeRobot |
| Package manager | pnpm 10.33.0 (JS) · uv (Python) |

---

## Development Setup

### Prerequisites

- Node.js ≥ 20, pnpm 10.33.0
- Python ≥ 3.11, uv
- Docker Desktop (cho Redis + PostgreSQL)
- PostgreSQL chạy trên port **5434** (không phải 5432 mặc định)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/voice-pro.git
cd voice-pro
pnpm install          # cài toàn bộ workspace
```

### 2. Backend Setup

```bash
cd backend
cp .env.example .env  # điền các giá trị cần thiết
uv sync               # cài Python dependencies
alembic upgrade head  # apply database migrations
```

`.env` quan trọng:

```env
DATABASE_URL=postgresql+psycopg2://voicepro:voicepro@127.0.0.1:5434/voicepro
REDIS_URL=redis://localhost:6380/0
JWT_SECRET=<min-32-chars>
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Start Local Services

```bash
# Redis (Docker)
docker run -d --name voicepro-redis -p 6380:6379 redis:7

# Backend API
cd backend
uvicorn main:app --reload --port 8000

# Celery Worker (tab mới)
cd backend
python -m celery -A app.celery_app worker --loglevel=info

# Celery Beat (tab mới)
cd backend
python -m celery -A app.celery_app beat --loglevel=info
```

### 4. Frontend Services

```bash
# Chrome Extension (dev mode)
pnpm --filter extension dev

# Dashboard SPA
pnpm --filter dashboard dev

# Landing Page
pnpm --filter landing dev
```

### 5. Load Extension vào Chrome

1. Mở `chrome://extensions`
2. Bật **Developer mode**
3. Click **Load unpacked** → chọn thư mục `extension/.output/chrome-mv3`

---

## API Overview

Tất cả endpoints có prefix `/api/v1/`. Docs tự động tại `http://localhost:8000/docs`.

| Endpoint | Method | Mô tả |
|---|---|---|
| `/api/v1/auth/register` | POST | Đăng ký tài khoản |
| `/api/v1/auth/login` | POST | Đăng nhập, nhận JWT |
| `/api/v1/auth/refresh` | POST | Refresh JWT token |
| `/api/v1/pipeline/process-chunk` | POST | Xử lý audio chunk (STT→MT→TTS) |
| `/api/v1/pipeline/progress/{job_id}` | GET | SSE stream tiến trình xử lý |
| `/api/v1/credits/balance` | GET | Số dư credits |
| `/api/v1/billing/checkout` | POST | Tạo Stripe checkout session |
| `/api/v1/billing/webhook` | POST | Stripe webhook handler |
| `/health` | GET | Health check (không cần auth) |

**Error schema chuẩn:**
```json
{ "code": "CREDIT_EXHAUSTED", "message": "Hết credits. Vui lòng nâng cấp.", "detail": {} }
```

---

## Database Migrations

```bash
cd backend

# Tạo migration mới
alembic revision --autogenerate -m "mô tả thay đổi"

# Apply migrations
alembic upgrade head

# Rollback 1 bước
alembic downgrade -1
```

> **Quy tắc:** KHÔNG sửa migration file đã commit. Tạo migration mới nếu cần thay đổi.

---

## Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Chạy với PostgreSQL thật
python -m pytest tests/ -v -m "not skip_no_db"

# Frontend (extension)
pnpm --filter extension test

# Frontend (dashboard)
pnpm --filter dashboard test
```

> Test cần PostgreSQL chạy trên port 5434. Dùng fixture `postgres_live` để skip khi DB chưa sẵn.

---

## Business Model

| Plan | Giá | Credits |
|---|---|---|
| Free | $0/tháng | 10 phút/tháng |
| Basic | $9/tháng | 120 phút/tháng |
| Pro | $19/tháng | Unlimited |

**Target metrics (6 tháng):**
- 10,000+ Chrome Web Store installs
- 500+ paid users
- MRR $4,500+
- Free → Paid conversion ≥ 8%
- Chrome Store rating ≥ 4.5 sao

---

## Supported Platforms

| Platform | Status |
|---|---|
| YouTube | ✅ MVP |
| Coursera, Vimeo, Udemy, Khan Academy | ✅ MVP |
| Bất kỳ HTML5 video không có DRM | ✅ MVP |
| Netflix, Disney+, Amazon Prime, HBO Max | ❌ DRM-protected — graceful error |

---

## Deployment

### Production (Hetzner VPS)

```bash
# SSH vào VPS
ssh admin@<vps-ip>

# Deploy mới nhất
cd /opt/voice-pro
docker compose pull
docker compose up -d
```

### Chrome Web Store

Extension tự động publish khi tạo tag `release/v*`:
```bash
git tag release/v1.0.0
git push origin release/v1.0.0
```

---

## Security

- Audio xử lý **in-memory only** — không bao giờ lưu ra disk hay database
- JWT access token: 24h · Refresh token: 30d
- Payment xử lý hoàn toàn bởi Stripe — không có card data chạm backend
- CORS whitelist: chỉ extension origin + dashboard domain, không dùng `*`
- Stripe webhook: idempotency check qua `stripe_event_id` trước khi process

---

## Contributing

```bash
# Tạo branch mới từ main
git checkout -b feature/ten-tinh-nang

# Chạy lint trước khi commit
pnpm -r --if-present run lint

# Format Python
cd backend && uv run ruff format .
```

---

## License

MIT

---

*Built on [Voice-Pro](https://github.com/abus-aikorea/voice-pro) stack: Faster-Whisper · Edge-TTS · Deep-Translator*
