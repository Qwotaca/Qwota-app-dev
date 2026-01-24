@echo off
echo.
echo ========================================
echo   QWOTA - TEST APPLICATION DESKTOP
echo ========================================
echo.

REM Vérifier si Node.js est installé
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Node.js n'est pas installe!
    echo Telechargez-le sur: https://nodejs.org/
    pause
    exit /b 1
)

REM Vérifier si node_modules existe
if not exist "node_modules\" (
    echo Installation des dependances...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] Installation echouee!
        pause
        exit /b 1
    )
)

echo.
echo MODE DE TEST:
echo.
echo [1] Production  - Se connecte a ton serveur Render
echo [2] Development - Se connecte a localhost:8000 (serveur local)
echo.
set /p choice="Choisis un mode (1 ou 2): "

if "%choice%"=="2" (
    echo.
    echo ========================================
    echo   MODE DEVELOPMENT
    echo ========================================
    echo.
    echo [IMPORTANT] Avant de continuer:
    echo.
    echo 1. Ouvre un autre terminal
    echo 2. Lance ton serveur FastAPI:
    echo    python main.py
    echo 3. Verifie qu'il tourne sur http://localhost:8000
    echo.
    echo Appuie sur une touche quand ton serveur est pret...
    pause >nul

    REM Modifier temporairement le mode dans electron-main.js
    powershell -Command "(Get-Content electron-main.js) -replace \"const MODE = 'production';\", \"const MODE = 'development';\" | Set-Content electron-main.js"

    echo.
    echo Lancement de l'application en mode DEVELOPMENT...
    call npm start

    REM Restaurer le mode production
    powershell -Command "(Get-Content electron-main.js) -replace \"const MODE = 'development';\", \"const MODE = 'production';\" | Set-Content electron-main.js"
) else (
    echo.
    echo ========================================
    echo   MODE PRODUCTION
    echo ========================================
    echo.
    echo Verification de la configuration...

    REM Lire l'URL configurée
    for /f "tokens=*" %%a in ('powershell -Command "Select-String -Path electron-main.js -Pattern 'const PRODUCTION_URL' | Select-Object -First 1 | ForEach-Object { $_.Line }"') do set url_line=%%a

    echo.
    echo URL configuree: %url_line%
    echo.
    echo [ATTENTION] Verifie que cette URL est correcte!
    echo Si ce n'est pas le cas, edite electron-main.js (ligne 10)
    echo.
    echo Appuie sur une touche pour lancer l'application...
    pause >nul

    echo.
    echo Lancement de l'application en mode PRODUCTION...
    call npm start
)

echo.
echo Application fermee.
pause
