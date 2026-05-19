@echo off
REM CrossMart 数据同步 + Git 推送
REM 用途: 每日定时任务 (Windows 任务计划程序)
REM 设置: schtasks /create /tn "CrossMart\Sync" /tr "C:\path\to\sync_and_push.bat" /sc daily /st 14:30

cd /d "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor"

echo [%date% %time%] Starting sync...

python -X utf8 backend\sync_to_frontend.py
if %ERRORLEVEL% NEQ 0 (
  echo [%date% %time%] Sync failed!
  exit /b 1
)

echo [%date% %time%] Pushing to GitHub...

git add frontend\data\monitor-data.json
git add frontend\data\selection-data.json
git add backend\sync_to_frontend.py

git diff --staged --quiet
if %ERRORLEVEL% EQU 0 (
  echo [%date% %time%] No changes to commit.
  exit /b 0
)

git commit -m "auto: sync monitor data %date%"
git push

echo [%date% %time%] Done.
