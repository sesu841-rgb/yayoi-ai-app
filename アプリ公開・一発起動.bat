@echo off
chcp 65001 > nul
echo ==============================================
echo [システム起動中...]
echo.
echo 裏側でAIサーバーを自動起動し、
echo 同時にスマホからアクセスできる公開URLを発行します。
echo ==============================================
echo.

start /B python -m uvicorn main:app --reload
python run_tunnel.py
pause
