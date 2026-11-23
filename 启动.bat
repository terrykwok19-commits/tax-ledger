@echo off
title 收入税费表 · 取数服务
cd /d "%~dp0"
set "PY=C://Users//Administrator//.workbuddy//binaries//python//envs//yqy-report//Scripts//python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" -c "import playwright" >nul 2>nul
if errorlevel 1 (
  echo.
  echo 当前 Python 没有 playwright 模块：%PY%
  echo 请把本文件里的 PY 改成带 playwright 的解释器，或先装 playwright。
  echo.
  pause
  exit /b 1
)
"%PY%" "%~dp0server.py" %*
echo.
echo 服务已停止。
pause
