@echo off
echo ============================================
echo Configuration MySQL pour serveur C2
echo ============================================
echo.
echo Ce script va creer:
echo   - Base de donnees: c2_database
echo   - Utilisateur: c2_user
echo   - Mot de passe: VotreMotDePasse123!
echo.
echo Vous allez etre invite a entrer le mot de passe ROOT de MySQL
echo.
pause

echo.
echo Execution du script SQL...
mysql -u root -p < setup_mysql_database.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo ✓ Configuration MySQL reussie!
    echo ============================================
    echo.
    echo Appuyez sur une touche pour creer les tables...
    pause
    
    echo.
    echo Creation des tables...
    C:\Users\WINDOWS\Desktop\basic-rat\venv\Scripts\python.exe setup_mysql.py
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ============================================
        echo ✓ Tables creees avec succes!
        echo ============================================
    ) else (
        echo.
        echo ============================================
        echo X Erreur lors de la creation des tables
        echo ============================================
    )
) else (
    echo.
    echo ============================================
    echo X Erreur lors de la configuration MySQL
    echo Verifiez que MySQL est demarre et que vous avez entre le bon mot de passe root
    echo ============================================
)

echo.
pause
