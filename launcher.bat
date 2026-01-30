@echo off
title Basic RAT - Quick Launch
color 0A

:menu
cls
echo ================================================
echo     BASIC RAT - QUICK LAUNCHER
echo     Complete Merged Edition
echo ================================================
echo.
echo 1. Start C2 Server
echo 2. Start Client (Local Test)
echo 3. Start Controller
echo 4. Install Dependencies
echo 5. Compile All
echo 6. Exit
echo.
set /p choice="Select option (1-6): "

if "%choice%"=="1" goto server
if "%choice%"=="2" goto client
if "%choice%"=="3" goto controller
if "%choice%"=="4" goto install
if "%choice%"=="5" goto compile
if "%choice%"=="6" goto exit

echo Invalid option!
pause
goto menu

:server
cls
echo [+] Starting C2 Server...
python server.py
pause
goto menu

:client
cls
echo [+] Starting Client...
python client.py
pause
goto menu

:controller
cls
echo [+] Starting Controller...
python controller.py
pause
goto menu

:install
cls
echo [+] Installing dependencies...
pip install -r requirements.txt
echo.
echo [+] Installation complete!
pause
goto menu

:compile
cls
echo [+] Compiling all components...
python compile.py
echo.
echo [+] Compilation complete! Check dist/ folder
pause
goto menu

:exit
echo [+] Goodbye!
exit
