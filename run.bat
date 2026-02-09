@echo off
setlocal
set ROOT=%~dp0
if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" "%ROOT%src\biblioteca_tk.py"
) else (
  python "%ROOT%src\biblioteca_tk.py"
)
endlocal
