@echo off
REM Run the Textual TUI version of the backup manager
cd /d "%~dp0"
.venv\Scripts\python.exe backup_gui_textual.py
pause
