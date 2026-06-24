@echo off
echo Starting Project Controls Intelligence Hub...
echo.
cd /d "%~dp0"
python -m streamlit run dashboard.py --server.port 8755 --server.headless true
pause
