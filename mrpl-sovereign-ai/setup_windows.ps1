# MRPL Sovereign AI Workbench - Windows setup script
Write-Host "== MRPL Sovereign AI Workbench Setup ==" -ForegroundColor Cyan

cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env -ErrorAction SilentlyContinue
cd ..

Write-Host "Backend deps installed. Edit backend/.env if your Ollama models use different tags." -ForegroundColor Green

cd frontend
npm install
cd ..

Write-Host "Frontend deps installed." -ForegroundColor Green

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Install Ollama (https://ollama.com) and pull models:"
Write-Host "   ollama pull qwen2.5-coder:32b"
Write-Host "   ollama pull deepseek-r1:32b"
Write-Host "   ollama pull qwen2.5:32b-instruct"
Write-Host "   ollama pull qwen2.5-vl:7b"
Write-Host "   ollama pull phi4:14b"
Write-Host "   (If your GPU can't fit 32B models, swap in 7B/14B tags in backend/.env)"
Write-Host ""
Write-Host "2. Install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki"
Write-Host ""
Write-Host "3. Start backend:  cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "4. Start frontend: cd frontend; npm run dev"
Write-Host "5. Open http://localhost:5173"
