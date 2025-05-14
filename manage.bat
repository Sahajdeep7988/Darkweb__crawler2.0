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

:: Main menu
:MENU
cls
echo.
echo =====================================================
echo     DARK WEB CRAWLER - ADMIN CONTROL PANEL
echo =====================================================
echo Current directory: %CRAWLER_DIR%
echo.
echo  [1] Setup Firewall Exceptions (Run First)
echo  [2] Run Crawler (With Admin Rights)
echo  [3] Open Admin Shell
echo  [4] Check Tor Connection
echo  [5] Fix GeckoDriver (Download Manually)
echo  [6] Edit Target Sites
echo  [7] Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto SETUP_FIREWALL
if "%choice%"=="2" goto RUN_CRAWLER
if "%choice%"=="3" goto ADMIN_SHELL
if "%choice%"=="4" goto CHECK_TOR
if "%choice%"=="5" goto FIX_DRIVER
if "%choice%"=="6" goto EDIT_SITES
if "%choice%"=="7" goto EXIT
goto MENU

:SETUP_FIREWALL
cls
echo Setting up firewall exceptions...
cd /d "%CRAWLER_DIR%"
python "%CRAWLER_DIR%setup_firewall.py"
echo.
pause
goto MENU

:RUN_CRAWLER
cls
echo Running crawler with admin privileges...
echo Starting Tor check...
cd /d "%CRAWLER_DIR%"
:: Ensure Tor is running first
python -c "import socket; s=socket.socket(); result=s.connect_ex(('127.0.0.1', 9050)); s.close(); exit(0 if result==0 else 1)" >nul 2>&1
if %errorlevel% NEQ 0 (
    echo WARNING: Tor does not appear to be running.
    echo Please start Tor Browser before continuing.
    echo.
    echo [1] Continue anyway
    echo [2] Go back to menu
    set /p torchoice="Enter choice: "
    if "!torchoice!"=="1" (
        echo Continuing...
    ) else (
        goto MENU
    )
)
python "%CRAWLER_DIR%run_crawler.py"
echo.
pause
goto MENU

:ADMIN_SHELL
cls
echo Starting admin command shell...
cd /d "%CRAWLER_DIR%"
cmd
goto MENU

:CHECK_TOR
cls
echo Checking Tor connection...
cd /d "%CRAWLER_DIR%"
python -c "import socket; s=socket.socket(); result=s.connect_ex(('127.0.0.1', 9050)); s.close(); print('✅ Tor is running successfully!' if result==0 else '❌ Tor is NOT running. Please start Tor Browser.')"
echo.
pause
goto MENU

:FIX_DRIVER
cls
echo Running GeckoDriver fixer (bypasses GitHub API rate limits)...
cd /d "%CRAWLER_DIR%"
python "%CRAWLER_DIR%fix_drivers.py"
echo.
pause
goto MENU

:EDIT_SITES
cls
cd /d "%CRAWLER_DIR%"
if not exist "configs" mkdir configs
if not exist "configs\sites.json" (
    echo Creating default sites.json...
    echo { > configs\sites.json
    echo   "sites": ["http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"], >> configs\sites.json
    echo   "max_pages": 10, >> configs\sites.json
    echo   "depth": 1 >> configs\sites.json
    echo } >> configs\sites.json
)
echo Opening sites.json for editing...
notepad "%CRAWLER_DIR%configs\sites.json"
goto MENU

:EXIT
exit 