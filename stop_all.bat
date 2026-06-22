@echo off
REM ============================================================
REM 一键关闭所有项目脚本（保留 OpenClaw / node）
REM 双击运行即可
REM ============================================================
echo.
echo [stop_all] 正在关闭所有 python 脚本（保留 OpenClaw）...
echo.

REM 杀掉所有 python 进程（api_server.py / run_monitor.py / scheduler 等）
REM OpenClaw 是 node 进程，不受影响
taskkill /F /IM python.exe   >nul 2>&1 && echo   - 已结束 python.exe
taskkill /F /IM python3.exe  >nul 2>&1 && echo   - 已结束 python3.exe
taskkill /F /IM pythonw.exe  >nul 2>&1 && echo   - 已结束 pythonw.exe

echo.
echo [stop_all] 完成。OpenClaw 仍在运行。
echo.
echo 当前剩余的 node/python 进程：
tasklist /FI "IMAGENAME eq node.exe" 2>nul | findstr /I node.exe
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I python.exe || echo   （已无 python 进程）
echo.
pause
