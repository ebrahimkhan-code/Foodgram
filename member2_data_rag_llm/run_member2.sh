#!/usr/bin/env bash
# Start Member 2 (RAG/LLM) FastAPI service on port 8001.
# Run from the member2_data_rag_llm folder. Uses a venv named "venv" if present.
set -e
cd "$(dirname "$0")"
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi
export MEMBER2_PORT="${MEMBER2_PORT:-8001}"
python api_server.py
