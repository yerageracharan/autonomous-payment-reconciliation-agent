@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup.bat first.
  pause
  exit /b 1
)
start "Agent 08 MCP Server" cmd /k "call .venv\Scripts\activate.bat && python src\mcp_server.py"
timeout /t 3 /nobreak >nul
call .venv\Scripts\activate.bat && streamlit run app.py
