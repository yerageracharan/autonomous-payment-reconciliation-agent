@echo off
cd /d %~dp0
py -3.11 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Setup complete. Run start.bat to launch the MCP server and localhost dashboard.
pause
