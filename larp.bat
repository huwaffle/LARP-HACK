@echo off
cd /d "%~dp0"
python -c "import questionary, rich, prompt_toolkit, pyperclip" 2>nul || python -m pip install -q -r requirements.txt
curl -s http://localhost:11434/api/tags >nul 2>&1 || (start "" /b ollama serve >nul 2>&1 & timeout /t 3 /nobreak >nul)
python larp.py %*
