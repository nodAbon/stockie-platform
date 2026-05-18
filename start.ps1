# Stockie (스토키) 통합 실행 스크립트

$Host.UI.RawUI.WindowTitle = "Stockie Stock Intelligence Platform - Startup Runner"

Clear-Host
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "   📈 Stockie (스토키) - 주린이를 위한 실시간 주식 지능형 비서 구동   " -ForegroundColor Yellow -BackgroundColor Blue
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "   프론트엔드(React), 백엔드(Gateway), AI분석엔진(Python)을 구동합니다...`n" -ForegroundColor Gray

$RootDir = Get-Location

# 1. Start Python Analysis Engine
Write-Host "[1/3] Python AI 분석 엔진 및 실시간 뉴스 크롤러 시작 중..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$RootDir\engine'; .\venv\Scripts\python.exe app.py" -WindowStyle Normal

# 2. Start Node.js API Gateway
Write-Host "[2/3] Node.js Express API Gateway 프록시 서버 구동 중..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$RootDir\backend'; npm run dev" -WindowStyle Normal

# 3. Start React Frontend Dev Server
Write-Host "[3/3] React (Vite + Tailwind v4) 대시보드 프론트엔드 기동 중..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$RootDir\frontend'; npm run dev -- --open" -WindowStyle Normal

Write-Host "`n=========================================================================" -ForegroundColor Green
Write-Host "   🚀 모든 Stockie 지능형 플랫폼 엔진 구동 완료!   " -ForegroundColor Green -Bold
Write-Host "   - 프론트엔드 대시보드 : http://localhost:5173" -ForegroundColor Cyan
Write-Host "   - Express API 게이트웨이 : http://localhost:4000" -ForegroundColor Cyan
Write-Host "   - Python AI 크롤러 엔진 : http://localhost:5000" -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Green
Write-Host "`n   *주의: 터미널 창을 닫으시면 해당 서비스가 중단됩니다. 구동 완료 후 브라우저가 자동 열립니다." -ForegroundColor Gray
