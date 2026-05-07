---
status: complete
generatedAt: '2026-05-07'
sections_completed:
  - technology-stack
  - language-specific-rules
  - framework-specific-rules
  - testing-rules
  - code-quality-style
  - development-workflow
  - critical-dont-miss-rules
project: voice-pro
---

# Project Context — voice-pro

> Tài liệu này dành cho AI agents. Chứa các luật quan trọng, pattern, và constraint mà agents PHẢI tuân thủ khi implement code. Tập trung vào những điều không hiển nhiên mà LLM dễ bỏ sót.

---

## Technology Stack & Versions

### Monorepo
- Package manager: **pnpm 10.33.0** — luôn dùng `pnpm`, không dùng npm/yarn
- Node.js: **≥ 20**
- Workspace packages: `extension`, `dashboard`, `landing`, `shared`, `backend`

### Backend (Python)
- Python: **≥ 3.11**
- FastAPI: **≥ 0.115.6** — chạy bằng `uvicorn main:app` từ thư mục `backend/`
- SQLAlchemy: **≥ 2.0.36** — dùng syntax Mapped/mapped_column (2.x style), KHÔNG dùng `Column()` cũ
- Alembic: **≥ 1.14.0**
- psycopg2-binary: **≥ 2.9.10**
- Celery: **≥ 5.4.0** + Redis broker/backend
- pydantic-settings: **≥ 2.7.0**
- PyJWT: **≥ 2.10.1** + bcrypt **≥ 4.2.1**
- Stripe: **≥ 11.0.0**
- faster-whisper: **≥ 1.1.0** (STT)
- edge-tts: **≥ 7.0.0** (TTS)
- deep-translator: **≥ 1.11.4**

### Extension
- WXT: **≥ 0.20.0** + `@wxt-dev/module-react`
- React: **≥ 19.0.0** + TypeScript **~5.7.3**

### Dashboard
- Vite: **≥ 6.0.7** + React **≥ 19.0.0** + react-router-dom **≥ 7.15.0**
- TypeScript: **~5.7.3**

### Landing
- Next.js 15 App Router + TypeScript + Tailwind CSS v4 (SSG/SEO)

### Infrastructure (local dev)
- PostgreSQL: port **5434** (KHÔNG phải 5432 mặc định)
- Redis (Docker `voicepro-redis`): host port **6380** → container 6379

---

## Language-Specific Rules

### Python (Backend)
- Functions/variables: `snake_case` — `get_user_credits()`, `audio_job_id`
- Classes: `PascalCase` — `AudioPipeline`, `CreditService`
- Files/modules: `snake_case` — `credit_service.py`, `audio_tasks.py`
- Config: LUÔN dùng `pydantic-settings BaseSettings` + `@lru_cache` singleton — KHÔNG hardcode env vars
- SQLAlchemy: dùng syntax 2.x — `Mapped[type]` + `mapped_column()` — KHÔNG dùng `Column()` cũ
- Async: backend dùng **sync SQLAlchemy** (psycopg2) với Celery workers, không asyncpg
- All primary keys: `UUID` (`uuid.uuid4`) — KHÔNG dùng integer auto-increment
- Soft delete: check `deleted_at.is_(None)` trong mọi query trên bảng `users`
- Datetime: LUÔN `timezone=True` trong `mapped_column(DateTime(...))`, compare với `datetime.now(tz=UTC)`
- Pydantic validation: KHÔNG validate thủ công — để Pydantic auto-validate tại endpoint

### TypeScript (Extension & Dashboard)
- Variables/functions: `camelCase` — `userId`, `getCredits()`
- Components: `PascalCase` — `CreditBalance`, `DubModeToggle`
- Types/Interfaces: `PascalCase`, **không prefix `I`** — `UserProfile`, `AudioJob`
- Files (components): `PascalCase.tsx` — `CreditBalance.tsx`
- Files (utilities/hooks): `camelCase.ts` — `useCredits.ts`, `formatDuration.ts`
- JSON fields trong API: **`snake_case`** dù frontend là TypeScript — KHÔNG dùng camelCase
- Import/Export: Extension dùng `browser.*` (WXT auto-import), không dùng `chrome.*` trực tiếp

---

## Framework-Specific Rules

### FastAPI (Backend)
- App factory: LUÔN dùng `create_app()` pattern trong `main.py` — không khởi tạo trực tiếp top-level
- Routers: prefix `/api/v1/` bắt buộc cho mọi endpoint; routers mount trong `create_app()`
- Settings DI: dùng `get_settings()` với `@lru_cache` — KHÔNG import `Settings()` trực tiếp
- DB Session: inject qua `Depends(get_db_session)` — KHÔNG tạo session thủ công trong endpoint
- Error responses: LUÔN dùng `HTTPException` với `detail` là string mô tả — response body theo schema `{code, message, detail}`
- Middleware: thêm vào `create_app()`, thứ tự quan trọng (CORS trước RateLimit)
- Celery tasks: đặt trong `app/tasks/`, naming `snake_case` verb-noun — `process_audio_chunk`
- Celery config: `task_serializer="json"`, `result_serializer="json"` — KHÔNG dùng pickle

### React (Extension & Dashboard)
- State server: **TanStack Query v5** — KHÔNG dùng `useState` + `useEffect` để fetch API
- State client: **Zustand v5** — update immutable: `set(state => ({ ...state, field: value }))`
- Loading states: dùng TanStack Query `isLoading`/`isFetching` — KHÔNG tự quản lý `const [loading, setLoading]`
- Validation form: React Hook Form nếu form > 3 fields
- Component library (Dashboard): **shadcn/ui v4** + Tailwind CSS v4
- Extension popup: custom minimal components — KHÔNG dùng thư viện nặng (bundle size)
- Routing (Dashboard): React Router v7 — `App.tsx` là nơi setup routes

### WXT Extension
- Entry points: tất cả nằm trong `entrypoints/` — `background.ts`, `content.ts`, `popup/`
- Manifest permissions: khai báo trong `wxt.config.ts`, không sửa tay `manifest.json`
- Storage: LUÔN dùng `chrome.storage.local` — service worker không có `localStorage`
- Messages: LUÔN dùng typed union `ExtensionMessage` — KHÔNG dùng `any` hay string literal tự do
- API từ extension: `browser.*` (WXT auto-import) — ưu tiên hơn `chrome.*`
- Auth token: lưu trong `chrome.storage.local`, không cookie (service worker không hỗ trợ)
- Refresh token (extension): trả về trong **body JSON** (`refresh_token` field) — khác Dashboard (cookie)

### Auth Dual-Flow (Critical!)
- **Extension**: nhận `refresh_token` trong response body → lưu `chrome.storage.local`
- **Dashboard**: nhận refresh token qua **httpOnly cookie** — không expose trong body
- Backend endpoint `/auth/refresh`: phân biệt flow qua `use_extension_flow = bool(from_body)`
- Cookie attrs: `httponly=True`, `secure=True` chỉ khi `environment == "production"`

---

## Testing Rules

### Python (Backend)
- Test location: tập trung trong `backend/tests/`, mirror cấu trúc `app/` → `tests/test_auth.py`
- Framework: **pytest** — không dùng unittest
- DB availability guard: dùng fixture `postgres_live` để skip test khi PostgreSQL chưa chạy
- Redis cleanup: fixture `_clear_rate_limit_keys_session` xóa keys `vp:rl:*` trước full suite
- Redis singleton reset: fixture `_reset_redis_singleton` chạy sau mỗi test — reset async client cũ
- Rate limit reset: fixture `_reset_rate_limit_fail_open_log_throttle` reset throttle state
- TestClient: dùng `httpx.AsyncClient` hoặc FastAPI `TestClient` — inject `Depends` override
- Không test với production DB — luôn cần `postgres_live` fixture hoặc mock

### TypeScript (Extension & Dashboard)
- Test location: co-located cùng source file — `DubModeController.test.ts` cạnh `DubModeController.ts`
- Extension test: `*.test.ts` cho logic, mock `chrome.*` APIs
- Dashboard test: `*.test.tsx` cho components

### General
- Unit test: business logic, không hit DB hay external APIs
- Integration test: cần DB running — đánh dấu qua fixture `postgres_live`
- Celery tasks: test bằng cách gọi trực tiếp `.apply()` hoặc mock celery worker
- Coverage: ưu tiên critical paths (auth, billing, credit metering)

---

## Code Quality & Style Rules

### API Response Format
- Success: trả trực tiếp data object — KHÔNG wrap thêm envelope `{ data: ... }`
- Error: LUÔN dùng schema chuẩn: `{ "code": "CREDIT_EXHAUSTED", "message": "...", "detail": {} }`
- Paginated list: `{ "items": [...], "total": 42, "page": 1, "size": 20 }`
- Error codes chuẩn: `CREDIT_EXHAUSTED`, `DRM_DETECTED`, `UNSUPPORTED_PLATFORM`, `RATE_LIMITED`, `PIPELINE_ERROR`, `AUTH_REQUIRED`, `INVALID_INPUT`, `NOT_FOUND`

### Data Format Rules
- Dates/Times: **ISO 8601 UTC bắt buộc** → `"2026-05-06T14:30:00Z"` — KHÔNG Unix timestamp, KHÔNG local time
- Audio durations: `duration_seconds: float` → `125.4` — milliseconds chỉ dùng trong internal pipeline
- Booleans: `true/false` native JSON — KHÔNG `1/0` hay `"yes"/"no"`
- JSON field casing: **`snake_case`** cho tất cả request/response

### Database Naming
- Tables: `snake_case_plural` → `users`, `credit_transactions`, `stripe_webhook_events`
- Columns: `snake_case` → `user_id`, `created_at`, `target_lang`
- Foreign keys: `{table_singular}_id` → `user_id`, `job_id`
- Indexes: `idx_{table}_{column}` → `idx_users_email`

### Code Organization
- Backend: feature-based → `app/api/{feature}.py`, `app/tasks/{feature}.py`, `app/schemas/{feature}.py`
- Frontend: feature-based → `src/features/{feature}/` (components + hooks + api calls cùng chỗ)
- Shared TypeScript types: `shared/types/` (monorepo) hoặc `src/types/` (per-package)
- shadcn/ui components: `src/components/ui/` — auto-generated, không sửa tay
- Python utils: `app/utils/`, Python schemas dùng chung: `app/schemas/`

---

## Development Workflow Rules

### Monorepo Commands
- Chạy sub-package: `pnpm --filter <name> <command>` — ví dụ: `pnpm --filter extension dev`
- Chạy tất cả: `pnpm -r run build` / `pnpm -r --if-present run lint`
- Backend: `cd backend && uvicorn main:app --reload --port 8000`
- Backend package manager: **uv** (`uv sync`, `uv add <pkg>`) — KHÔNG dùng pip trực tiếp

### Local Dev Services
- PostgreSQL: port **5434** — service `postgresql-x64-18` trên Windows
- Redis: Docker `voicepro-redis`, host port **6380**
- Backend `.env`: `DATABASE_URL=postgresql+psycopg2://voicepro:voicepro@127.0.0.1:5434/voicepro`
- Celery worker: `python -m celery -A app.celery_app worker --loglevel=info` (trong `backend/`)
- Celery beat: `python -m celery -A app.celery_app beat --loglevel=info` (trong `backend/`)

### Database Migrations
- Tạo migration: `alembic revision --autogenerate -m "<mô tả>"` (trong `backend/`)
- Apply: `alembic upgrade head`
- KHÔNG sửa migration file đã commit — tạo migration mới nếu cần thay đổi
- File migrations: `backend/alembic/versions/` — naming `{NNN}_{epic_desc}.py`

### API Versioning
- Prefix bắt buộc: `/api/v1/` cho mọi endpoint
- Endpoint nouns: plural lowercase kebab → `/api/v1/audio-jobs`, `/api/v1/credit-transactions`
- Path params: snake_case → `/api/v1/audio-jobs/{job_id}`

### CI/CD
- Push to `main` → test → build Docker → SSH deploy Hetzner VPS
- Extension publish: tag `release/v*` → GitHub Action auto-publish Chrome Web Store
- Health check: `GET /health` — không cần auth

---

## Critical Don't-Miss Rules

### Anti-Patterns TUYỆT ĐỐI Tránh

**API & Data:**
- ❌ `userId` trong JSON response → ✅ phải là `user_id`
- ❌ Unix timestamp `1746540600` trong API → ✅ dùng `"2026-05-06T14:30:00Z"`
- ❌ `{ "error": "Something went wrong" }` → ✅ phải có `code` field
- ❌ Wrap response: `{ "data": { ... } }` → ✅ trả trực tiếp object
- ❌ camelCase JSON: `"balanceMinutes"` → ✅ `"balance_minutes"`

**Extension:**
- ❌ `sendMessage({ action: "start" })` không typed → ✅ dùng typed union `ExtensionMessage`
- ❌ `chrome.*` trực tiếp trong WXT → ✅ dùng `browser.*`
- ❌ Lưu token vào `localStorage` trong service worker → ✅ `chrome.storage.local`

**React/Frontend:**
- ❌ `const [loading, setLoading] = useState(false)` khi đã có TanStack Query
- ❌ `state.processingState = 'playing'` (mutation Zustand) → ✅ `set(state => ({ ...state, ... }))`
- ❌ Dùng integer PK → ✅ UUID

**Backend:**
- ❌ `Column(String)` SQLAlchemy cũ → ✅ `Mapped[str]` + `mapped_column(String(...))`
- ❌ Tạo `Settings()` trực tiếp → ✅ luôn gọi `get_settings()`
- ❌ Tạo DB session thủ công trong endpoint → ✅ `Depends(get_db_session)`
- ❌ Query users không filter `deleted_at.is_(None)` → ✅ luôn check soft delete

### Security Rules
- JWT secret: KHÔNG dùng default `dev-jwt-secret-change-me` trong production (min 32 chars)
- Audio: KHÔNG bao giờ lưu audio ra disk hay DB — ephemeral in-memory only
- Credit deduction: atomic với Redis transaction — rollback nếu TTS fail
- Stripe webhook: check idempotency qua `stripe_event_id` trong `stripe_webhook_events` trước khi process
- CORS: whitelist cụ thể extension origin + dashboard domain — không dùng `*`

### Audio Pipeline Constraints
- Faster-Whisper input: chỉ nhận **PCM 16kHz, mono, 16-bit** — extension PHẢI convert trước khi gửi
- Chunk boundaries: KHÔNG cắt giữa từ khi chia chunks
- Credit metering: đo duration ở **backend** — KHÔNG tin duration từ extension (tránh giả mạo)
- Free tier gate: atomic với job dispatch — tránh race condition

### Performance Gotchas
- Credit balance: KHÔNG cache trong Redis — luôn đọc từ DB (accuracy ≤1% error)
- Translation cache: Redis `translate:{lang_pair}:{text_hash}` TTL 24h — OK để cache
- TanStack Query retry: auto 2 lần + exponential backoff — không implement thủ công
- 401 flow: auto-refresh JWT → retry request gốc — dùng axios interceptor
