@echo off
chcp 65001 >nul 2>&1
cd /d "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor"
"C:\Python314\python.exe" "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\reset_and_run.py" >> "C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\logs\monitor_1100.log" 2>&1