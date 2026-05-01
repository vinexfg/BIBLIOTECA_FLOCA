@echo off
setlocal
set ROOT=%~dp0
if exist "%ROOT%.venv\Scripts\pythonw.exe" (
  "%ROOT%.venv\Scripts\pythonw.exe" "%ROOT%src\biblioteca_tk.py"
) else (
  pythonw "%ROOT%src\biblioteca_tk.py"
)
endlocal
