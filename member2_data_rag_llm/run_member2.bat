@echo off
REM Start Member 2 (RAG/LLM) FastAPI service on port 8001.
REM Run from the member2_data_rag_llm folder. Assumes a venv named "venv".
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)
set MEMBER2_PORT=8001
python api_server.py
