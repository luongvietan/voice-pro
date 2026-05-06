$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$running = docker compose -f docker-compose.dev.yml ps --status running --quiet api 2>$null
if (-not $running) {
    Write-Error "Stack chưa chạy. Khởi động: docker compose -f docker-compose.dev.yml up -d"
    exit 1
}

Write-Host "CẢNH BÁO: Thao tác này sẽ XÓA toàn bộ dữ liệu dev database!" -ForegroundColor Yellow
$confirm = Read-Host "Nhập 'yes' để tiếp tục"
if ($confirm -ne "yes") {
    Write-Host "Hủy bỏ."
    exit 0
}

docker compose -f docker-compose.dev.yml exec -T api alembic downgrade base
docker compose -f docker-compose.dev.yml exec -T api alembic upgrade head
Write-Host "Database reset xong." -ForegroundColor Green
