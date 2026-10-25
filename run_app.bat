@echo off
REM ย้าย Working Directory มายังโฟลเดอร์ของโปรเจกต์เสมอ (เพื่อให้หาไฟล์ hotstring_data.jason เจอ)
cd /d "%~dp0"

REM รันโปรแกรมด้วย pythonw.exe ใน .venv เพื่อไม่ให้มีหน้าต่างจอดำ
start "" ".venv\Scripts\pythonw.exe" main.py
