@echo off
cd /d "%~dp0"
echo Downloading official NASA IMS and MIMII pump datasets.
echo Approximately 1.5 GB or more may be downloaded and extraction needs additional disk space.
.venv\Scripts\python.exe scripts\download_external_datasets.py
