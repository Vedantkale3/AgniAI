#!/usr/bin/env bash
set -e
echo "== MRPL Sovereign AI Workbench Setup =="

cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env || true
cd ..

cd frontend
npm install
cd ..

echo ""
echo "NEXT STEPS:"
echo "1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
echo "2. Pull models:"
echo "   ollama pull qwen2.5-coder:32b"
echo "   ollama pull deepseek-r1:32b"
echo "   ollama pull qwen2.5:32b-instruct"
echo "   ollama pull qwen2.5-vl:7b"
echo "   ollama pull phi4:14b"
echo "3. Install tesseract-ocr: sudo apt install tesseract-ocr poppler-utils"
echo "4. Start backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "5. Start frontend: cd frontend && npm run dev"
echo "6. Open http://localhost:5173"
