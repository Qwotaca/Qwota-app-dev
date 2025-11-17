@echo off
echo.
echo ========================================
echo   BUILD QWOTA .EXE (Admin Mode)
echo ========================================
echo.

REM Vérifier si on tourne en admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Execution en mode administrateur
    echo.
) else (
    echo [ERREUR] Ce script doit etre execute en tant qu'administrateur!
    echo.
    echo Comment faire:
    echo 1. Clique droit sur build-as-admin.bat
    echo 2. Choisis "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo [1/2] Suppression du cache problematique...
rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" 2>nul

echo.
echo [2/2] Lancement du build...
echo Cela va prendre 5-10 minutes...
echo.

cd /d "%~dp0"
call npm run build

if %ERRORLEVEL% EQ 0 (
    echo.
    echo ========================================
    echo   BUILD REUSSI!
    echo ========================================
    echo.
    echo Fichier cree: dist\Qwota-Setup-1.0.0.exe
    echo.
) else (
    echo.
    echo [ERREUR] Le build a echoue!
    echo.
)

pause
