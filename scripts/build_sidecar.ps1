<#
.SYNOPSIS
Script tự động đóng gói FastAPI Backend thành file thực thi độc lập (Tauri Sidecar).

.DESCRIPTION
Dùng PyInstaller để đóng gói thư mục backend, sau đó đổi tên và di chuyển vào đúng thư mục của Tauri.
Phục vụ cho quy trình Build Production.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 BẮT ĐẦU ĐÓNG GÓI BACKEND SANG SIDECAR" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Kiểm tra môi trường
$RootDir = Join-Path -Path $PSScriptRoot -ChildPath ".."
$BackendDir = Join-Path -Path $RootDir -ChildPath "backend"
$TauriBinDir = Join-Path -Path $RootDir -ChildPath "frontend\src-tauri\bin"
$TargetArch = "x86_64-pc-windows-msvc"
$TargetExeName = "backend-$TargetArch.exe"
$VenvPath = Join-Path -Path $BackendDir -ChildPath "venv"

if (-not (Test-Path $BackendDir)) {
    Write-Host "❌ Lỗi: Không tìm thấy thư mục backend/" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $TauriBinDir)) {
    Write-Host "Tạo thư mục frontend/src-tauri/bin..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $TauriBinDir | Out-Null
}

# 2. Cài đặt PyInstaller nếu chưa có
Write-Host "`n[1/4] Kích hoạt môi trường ảo và kiểm tra PyInstaller..." -ForegroundColor Green
# Đứng ở thư mục Gốc để Pyinstaller nhận diện đúng package "backend.*"
Set-Location -Path $RootDir
if (Test-Path $VenvPath) {
    # Active venv in PowerShell
    & "$VenvPath\Scripts\Activate.ps1"
} else {
    Write-Host "Cảnh báo: Không tìm thấy venv tại $VenvPath. Sẽ dùng Python global." -ForegroundColor Yellow
}

pip install pyinstaller | Out-Null

# 3. Đóng gói bằng PyInstaller
Write-Host "`n[2/4] Bắt đầu đóng gói bằng PyInstaller (Quá trình này có thể mất vài phút)..." -ForegroundColor Green
# Đóng gói thành 1 file duy nhất (--onefile)
# KHÔNG dùng --noconsole để Tauri có thể bắt được Log stdout/stderr
# Ép PyInstaller lấy toàn bộ cấu trúc thư mục con của backend (--collect-submodules backend)
# Bắt buộc đính kèm thư viện tiktoken_ext để sửa lỗi Unknown encoding cl100k_base
pyinstaller --name "backend" --onefile `
  --hidden-import aiosqlite `
  --hidden-import passlib.handlers.bcrypt `
  --copy-metadata tiktoken `
  --collect-data tiktoken `
  --collect-data certifi `
  --hidden-import tiktoken_ext.openai_public `
  --hidden-import tiktoken_ext.bpe `
  --add-data "backend/credentials.json;." `
  --collect-submodules backend backend/main.py

if (-not $?) {
    Write-Host "❌ Lỗi: PyInstaller thất bại!" -ForegroundColor Red
    exit 1
}

# 4. Copy và đổi tên File sang thư mục Tauri Bin
$BuiltExe = Join-Path -Path $RootDir -ChildPath "dist\backend.exe"
$DestinationExe = Join-Path -Path $TauriBinDir -ChildPath $TargetExeName

Write-Host "`n[3/4] Sao chép file thực thi sang Tauri..." -ForegroundColor Green
if (Test-Path $BuiltExe) {
    Copy-Item -Path $BuiltExe -Destination $DestinationExe -Force
    Write-Host "Đã copy thành công: $TargetExeName vào thư mục tauri/bin/" -ForegroundColor Cyan
} else {
    Write-Host "❌ Lỗi: Không tìm thấy file exe sau khi build!" -ForegroundColor Red
    exit 1
}

# 5. Cập nhật cấu hình Tauri (Nhắc nhở)
Write-Host "`n[4/4] Dọn dẹp thư mục tạm..." -ForegroundColor Green
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "backend.spec" -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ HOÀN TẤT! Backend đã sẵn sàng chạy chung với ứng dụng Desktop." -ForegroundColor Green
Write-Host "Lưu ý: Hãy chắc chắn bạn đã cấu hình 'bundle.externalBin' trong tauri.conf.json như sau:" -ForegroundColor Yellow
Write-Host @"
"bundle": {
  "externalBin": [
    "bin/backend"
  ]
}
"@ -ForegroundColor Yellow
Write-Host "`nBây giờ bạn có thể chạy: cd frontend && npm run tauri build" -ForegroundColor Cyan
