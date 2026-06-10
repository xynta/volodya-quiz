@echo off
REM Сборка консольного квиза в один .exe на Windows.
REM Результат: dist\volodya_quiz.exe
cd /d "%~dp0"

python -m pip install -r requirements-build.txt
python -m PyInstaller volodya_quiz.spec --noconfirm --clean

echo.
echo Готово! Запусти dist\volodya_quiz.exe (двойной клик).
pause
