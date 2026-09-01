@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3.11 -m venv .venv) else (python -m venv .venv)
if errorlevel 1 goto :error
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist .env copy .env.example .env
.venv\Scripts\python.exe scripts\generate_data.py
.venv\Scripts\python.exe -m pytest -q
call setup_external_real_data.cmd
echo Setup complete. Use run_backend.cmd and run_dashboard.cmd in two VS Code terminals.
exit /b 0
:error
echo Python 3.11 or 3.12 is required and must be available on PATH.
exit /b 1
