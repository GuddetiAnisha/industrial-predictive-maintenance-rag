$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) { $Python = "py"; $PythonArgs = @("-3.11") }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = "python"; $PythonArgs = @() }
else { throw "Python 3.11+ was not found. Install it from python.org, enable Add Python to PATH, then rerun this script." }
if (-not (Test-Path ".venv")) { & $Python @PythonArgs -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
& ".\.venv\Scripts\python.exe" scripts\generate_data.py
& ".\.venv\Scripts\python.exe" -m pytest -q
Write-Host "Setup complete. Run .\run_backend.ps1 and .\run_dashboard.ps1 in separate terminals."
