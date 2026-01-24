@echo off
echo.
echo ========================================
echo   QWOTA - BUILD APPLICATION DESKTOP
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

echo [1/4] Verification de Node.js...
node --version
npm --version
echo.

REM Vérifier si node_modules existe
if not exist "node_modules\" (
    echo [2/4] Installation des dependances...
    echo Cela peut prendre quelques minutes...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] Installation echouee!
        pause
        exit /b 1
    )
) else (
    echo [2/4] Dependances deja installees
)
echo.

REM Vérifier si l'icône existe
if not exist "build\" mkdir build
if not exist "build\icon.ico" (
    echo [ATTENTION] Aucune icone trouvee dans build/icon.ico
    echo Une icone par defaut sera utilisee
    echo.
    echo Pour ajouter une icone personnalisee:
    echo 1. Cree un fichier icon.ico (256x256)
    echo 2. Place-le dans le dossier build/
    echo.
)

echo [3/4] Nettoyage des anciens builds...
if exist "dist\" rmdir /s /q dist
echo.

echo [4/4] Construction de l'application...
echo Cela peut prendre 5-10 minutes...
call npm run build

if %ERRORLEVEL% EQ 0 (
    echo.
    echo ========================================
    echo   BUILD REUSSI!
    echo ========================================
    echo.
    echo Le fichier d'installation a ete cree:
    echo dist\Qwota-Setup-1.0.0.exe
    echo.
    echo Tu peux maintenant:
    echo 1. Tester l'installeur en double-cliquant dessus
    echo 2. Distribuer ce fichier a tes utilisateurs
    echo.
    echo Taille du fichier:
    dir "dist\*.exe" | find ".exe"
    echo.
    pause
) else (
    echo.
    echo [ERREUR] Le build a echoue!
    echo Verifie les messages d'erreur ci-dessus.
    echo.
    pause
    exit /b 1
)
