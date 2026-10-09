@echo off
title LARP
cd /d "%~dp0"
python -c "import rich, prompt_toolkit, pyperclip" 2>nul || python -m pip install -q -r requirements.txt
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1 || (start "" /b ollama serve >nul 2>&1 & timeout /t 3 /nobreak >nul)
python -m larp %*
if errorlevel 1 pause
