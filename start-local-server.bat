@echo off
echo ================================================
echo   QWOTA - SERVEUR DE DEVELOPPEMENT LOCAL
echo ================================================
echo.
echo Demarrage du serveur sur http://localhost:8080
echo.
echo Appuyez sur CTRL+C pour arreter le serveur
echo ================================================
echo.

cd /d "%~dp0"

REM Activer l'environnement virtuel si présent
if exist "venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
)

REM Démarrer uvicorn sur le port 8080
echo Lancement de FastAPI avec uvicorn...
echo.
echo URL: http://localhost:8080
echo Mode: Developpement (--reload active)
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080

pause
