@echo off
REM CrossMart 完整流水线：抓取 → 同步 → 推送到 GitHub
REM 用途: Windows 任务计划程序
REM 注册命令（以管理员身份运行）:
REM   schtasks /create /sc daily /st 06:00 /tn "CrossMart\MonitorSync" /tr "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\run_and_sync.bat" /f
REM   schtasks /create /sc daily /st 12:00 /tn "CrossMart\MonitorSync2" /tr "..." /f
REM   schtasks /create /sc daily /st 18:00 /tn "CrossMart\MonitorSync3" /tr "..." /f
REM   schtasks /create /sc daily /st 00:00 /tn "CrossMart\MonitorSync4" /tr "..." /f

setlocal enabledelayedexpansion

set PROJECT=C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor
cd /d "%PROJECT%"

echo [%date% %time%] ========== CrossMart Sync Start ==========

REM ── Step 0: 确保 Edge CDP 端口是活的 ──
REM     如果 Edge 被关掉了，尝试重新启动（静默）
tasklist /fi "IMAGENAME eq msedge.exe" 2>nul | find /i "msedge" >nul
if %errorlevel% neq 0 (
    echo [%date% %time%] Edge not running. Starting...
    start "" msedge --remote-debugging-port=9225 --remote-allow-origins=* --new-window about:blank
    timeout /t 5 /nobreak >nul
)

REM ── Step 1: 自动发现所有已监控的 ASIN ──
REM     从 backend/data/processed/ 下的目录名获取
set ASIN_LIST=
for /d %%i in (backend\data\processed\asin_*) do (
    set "NAME=%%~nxi"
    set "ASIN=!NAME:asin_=!"
    set "ASIN_LIST=!ASIN_LIST! !ASIN!"
)

if "!ASIN_LIST!"=="" (
    echo [%date% %time%] ERROR: No ASIN directories found!
    exit /b 1
)

echo [%date% %time%] ASINs to scan:!ASIN_LIST!

REM ── Step 2: 逐个抓取 ASIN ──
echo [%date% %time%] Starting ASIN scrape...
for %%a in (!ASIN_LIST!) do (
    echo [%date% %time%]   Checking %%a...
    python -X utf8 backend\run_monitor.py %%a
    if !errorlevel! neq 0 (
        echo [%date% %time%]   ⚠️  %%a failed, continuing
        REM 短暂等待，避免被风控
        timeout /t 2 /nobreak >nul
    ) else (
        echo [%date% %time%]   ✅ %%a done
    )
    REM ASIN 之间间隔 3-5 秒，降低频率
    timeout /t 3 /nobreak >nul
)

REM ── Step 3: 同步到前端 ──
echo [%date% %time%] Syncing to frontend...
python -X utf8 backend\sync_to_frontend.py
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Sync failed!
    exit /b 1
)
echo [%date% %time%] ✅ Sync complete

REM ── Step 4: 推送 GitHub ──
echo [%date% %time%] Pushing to GitHub...
git add --update
git add frontend\data\monitor-data.json
git add backend\sync_to_frontend.py

git diff --staged --quiet
if %errorlevel% equ 0 (
    echo [%date% %time%] No changes to commit.
) else (
    git commit -m "auto: monitor sync %date%"
    if !errorlevel! equ 0 (
        git push
        echo [%date% %time%] ✅ Pushed to GitHub
    ) else (
        echo [%date% %time%] ⚠️  Nothing to commit
    )
)

REM ── Step 5: 钉钉通知 ──
echo [%date% %time%] Notifying...
python -X utf8 backend\notify.py

echo [%date% %time%] ========== CrossMart Sync Done ==========
echo.
