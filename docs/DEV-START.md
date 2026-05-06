# Hướng dẫn khởi động môi trường dev (Windows)

Tài liệu này mô tả **các bước và lệnh cần chạy mỗi lần** làm việc với backend Voice-Pro (và tùy chọn extension). Đường dẫn mẫu dùng repo tại `C:\Users\admin\Desktop\voice-pro\voice-pro` — thay bằng đường dẫn thực tế trên máy bạn.

## Giả định setup đã có

| Thành phần | Mô tả |
|------------|--------|
| PostgreSQL | Cài trên Windows, service **postgresql-x64-18** (hoặc tương đương), DB/user **`voicepro`**, port **5434** (hoặc chỉnh lại cho khớp `.env`). |
| Redis | Container Docker **`voicepro-redis`**, map host **`6380` → 6379** (không xung đột với Redis project khác trên 6379). |
| Python | ≥ 3.11, dependency backend đã cài (`uv sync` hoặc `pip install -e ".[dev]"` trong `backend/`). |
| File env | `backend/.env` tối thiểu gồm `DATABASE_URL` và `REDIS_URL`. |

### Mẫu `backend/.env`

```env
DATABASE_URL=postgresql+psycopg2://voicepro:voicepro@127.0.0.1:5434/voicepro
REDIS_URL=redis://127.0.0.1:6380/0

# Stripe (Epic 6 — tùy chọn cho webhook/checkout)
# STRIPE_API_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...
# STRIPE_PAID_PRICE_IDS=price_xxx,price_yyy
# STRIPE_PRICE_BASIC=price_basic
# STRIPE_PRICE_PRO=price_pro
# STRIPE_SUCCESS_URL=http://localhost:5173/?checkout=success
# STRIPE_CANCEL_URL=http://localhost:5173/?checkout=cancel
```

Đổi **port Postgres** (5434) hoặc **port Redis** (6380) nếu máy bạn khác.

---

## Mỗi lần bắt đầu dev — thứ tự gợi ý

### Bước 1: Bật dịch vụ PostgreSQL

- **Cách 1:** `Win + R` → `services.msc` → tìm **postgresql-…** → **Start** (nếu đang Stopped).
- **Cách 2 (PowerShell Administrator):**

```powershell
Start-Service postgresql-x64-18
```

(Tên service có thể khác — tra bằng `Get-Service *postgres*`.)

---

### Bước 2: Bật container Redis (Voice-Pro)

Nếu container đã tạo trước đó và chỉ bị stop:

```powershell
docker start voicepro-redis
```

Kiểm tra:

```powershell
docker ps --filter name=voicepro-redis
```

Phải thấy cột **PORTS** dạng `0.0.0.0:6380->6379/tcp`.

**Lần đầu** (chưa có container):

```powershell
docker run -d --name voicepro-redis -p 6380:6379 redis:7-alpine
```

Nếu báo tên đã tồn tại:

```powershell
docker rm -f voicepro-redis
docker run -d --name voicepro-redis -p 6380:6379 redis:7-alpine
```

---

### Bước 3 (khi có migration mới — không phải mỗi ngày)

Chỉ chạy sau khi `git pull` có thay đổi Alembic:

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m alembic upgrade head
```

---

### Bước 4: API — Uvicorn (terminal 1)

**Luôn `cd` vào thư mục `backend`** (module `app` nằm ở đó).

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Giữ terminal này mở. Kiểm tra: trình duyệt mở `http://127.0.0.1:8000/docs` hoặc `http://127.0.0.1:8000/health`.

---

### Bước 5: Celery worker (terminal 2) — bắt buộc cho pipeline STT/TTS

Job transcribe/synthesize chạy trên worker, **không** chạy trong Uvicorn.

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m celery -A app.celery_app worker --loglevel=info --pool=solo
```

- Trên Windows nên dùng **`--pool=solo`** để tránh lỗi prefork.
- Log mong đợi: `Connected to redis://127.0.0.1:6380/0` và `ready`.

---

### Bước 6 (tùy chọn): Celery Beat — lịch reset credit đầu tháng

Chỉ cần nếu bạn muốn task định kỳ (Epic 4) chạy đúng lịch **ngày 1 hàng tháng UTC**.

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m celery -A app.celery_app beat --loglevel=info
```

Có thể tạo file `celerybeat-schedule` trong `backend/` — có thể thêm vào `.gitignore` nếu không muốn commit.

---

### Bước 7 (tùy chọn): Extension Chrome

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\extension
npm install
npm run dev
```

Hoặc build:

```powershell
npm run build
```

Load unpacked: Chrome → **Extensions** → **Load unpacked** → chọn thư mục output (thường `extension\.output\chrome-mv3`). Cấu hình **API base** / OAuth Google theo `DESIGN.md` hoặc README extension.

---

## Checklist nhanh trước khi code

- [ ] PostgreSQL service: **Running**
- [ ] `docker ps` có **voicepro-redis** (port **6380**)
- [ ] Terminal 1: **uvicorn** (port **8000**)
- [ ] Terminal 2: **celery worker** (`--pool=solo`)
- [ ] (Tuỳ chọn) Terminal 3: **celery beat**
- [ ] (Tuỳ chọn) Extension: **npm run dev**

---

## Xử lý sự cố thường gặp

| Hiện tượng | Gợi ý |
|------------|--------|
| `The module app.celery_app was not found` | Chưa `cd` vào **`backend`**. |
| Celery: `Authentication required` (Redis) | Redis trên 6379 của project khác có password — dùng Redis riêng port **6380** như trên, hoặc thêm password vào `REDIS_URL`. |
| `Connection refused` Postgres | Service PostgreSQL chưa Start; hoặc sai **port** trong `DATABASE_URL`. |
| `/health` Redis disconnected | Container Redis chưa chạy hoặc sai `REDIS_URL`. |

---

## Tóm tắt lệnh copy-paste (4 terminal)

**Terminal A — Redis (nếu container stopped)**

```powershell
docker start voicepro-redis
```

**Terminal B — API**

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal C — Worker**

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Terminal D — Beat (tuỳ chọn)**

```powershell
cd C:\Users\admin\Desktop\voice-pro\voice-pro\backend
python -m celery -A app.celery_app beat --loglevel=info
```

---

*Cập nhật: phản ánh setup Postgres cục bộ (port 5434), Redis Docker `voicepro-redis` (6380), Celery pool solo trên Windows.*
