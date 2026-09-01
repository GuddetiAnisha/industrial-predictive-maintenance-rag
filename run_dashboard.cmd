@echo off
cd /d "%~dp0"
set API_URL=http://127.0.0.1:8000
.venv\Scripts\python.exe -m streamlit run dashboard\dashboard.py --server.port 8501
