@echo off
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor"
"C:\Python314\python.exe" "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\backend\scheduled_run.py" >> "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\logs\monitor_0500.log" 2>&1
