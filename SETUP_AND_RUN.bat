@echo off
setlocal EnableDelayedExpansion

:: Set correct directory paths
set "CRAWLER_DIR=%~dp0"
cd /d "%CRAWLER_DIR%"

:: Check for admin rights
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

:: If error flag set, we don't have admin rights
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~f0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)

echo =====================================================
echo  DARK WEB CRAWLER - COMPLETE SETUP AND RUN
echo =====================================================
echo This script will automatically:
echo  1. Set up firewall exceptions
echo  2. Fix GeckoDriver installation
echo  3. Check Tor connection
echo  4. Run the crawler
echo =====================================================
echo.
echo Press any key to continue...
pause >nul

:: Step 1: Set up firewall exceptions
echo.
echo [STEP 1/4] Setting up firewall exceptions...
cd /d "%CRAWLER_DIR%"
python "%CRAWLER_DIR%setup_firewall.py"
echo.
echo Firewall setup complete. Press any key to continue...
pause >nul

:: Step 2: Fix GeckoDriver
echo.
echo [STEP 2/4] Installing GeckoDriver (bypassing GitHub API)...
cd /d "%CRAWLER_DIR%"
python "%CRAWLER_DIR%fix_drivers.py"
echo.
echo GeckoDriver setup complete. Press any key to continue...
pause >nul

:: Step 3: Check Tor connection
echo.
echo [STEP 3/4] Checking Tor connection...
cd /d "%CRAWLER_DIR%"
echo.
echo Make sure Tor Browser is running before continuing!
echo.
echo Checking Tor connection...
python -c "import socket; s=socket.socket(); result=s.connect_ex(('127.0.0.1', 9050)); s.close(); print('✅ Tor is running successfully!' if result==0 else '❌ Tor is NOT running. Please start Tor Browser.')"

python -c "import socket; s=socket.socket(); result=s.connect_ex(('127.0.0.1', 9050)); s.close(); exit(0 if result==0 else 1)" >nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo ❌ Tor is not running. Please:
    echo   1. Start Tor Browser
    echo   2. Keep it running in the background
    echo   3. Run this script again
    echo.
    echo Press any key to exit...
    pause >nul
    exit /B
)

echo.
echo Tor connection verified. Press any key to continue...
pause >nul

:: Step 4: Run the crawler
echo.
echo [STEP 4/4] Running the crawler...
cd /d "%CRAWLER_DIR%"
python "%CRAWLER_DIR%run_crawler.py"
echo.
echo Crawler execution completed.
echo.
echo Press any key to exit...
pause >nul 