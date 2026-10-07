@echo off
cd /d "%~dp0"
python make_certs.py
exit /b %errorlevel%
