@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo [T.O.DAY] 필요한 프로그램을 설치합니다... (처음 한 번만 오래 걸려요)
python -m pip install -r requirements.txt
echo [T.O.DAY] 앱을 실행합니다. 브라우저가 자동으로 열립니다.
python -m streamlit run app.py
pause
