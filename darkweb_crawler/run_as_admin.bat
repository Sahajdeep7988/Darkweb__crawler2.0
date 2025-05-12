@echo off
:: Set correct directory paths
set "CRAWLER_DIR=%~dp0"

:: Check for admin rights
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

:: If error flag set, we don't have admin rights
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~f0", "%*", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs"
    cd /d "%CRAWLER_DIR%"
    
echo Running with administrator privileges...
echo Current directory: %CRAWLER_DIR%

:: Check what script to run
if "%1"=="" (
    echo Usage options:
    echo.
    echo run_as_admin.bat setup    - Setup firewall exceptions
    echo run_as_admin.bat crawler  - Run the crawler
    echo run_as_admin.bat shell    - Open a command prompt with admin rights
    echo run_as_admin.bat driver   - Fix GeckoDriver installation
    exit /B
)

if "%1"=="setup" (
    echo Setting up firewall exceptions...
    cd /d "%CRAWLER_DIR%"
    python "%CRAWLER_DIR%setup_firewall.py"
    pause
    exit /B
)

if "%1"=="crawler" (
    echo Running crawler with elevated privileges...
    cd /d "%CRAWLER_DIR%"
    python "%CRAWLER_DIR%run_crawler.py"
    pause
    exit /B
)

if "%1"=="shell" (
    echo Starting admin command shell...
    cd /d "%CRAWLER_DIR%"
    cmd /k cd /d "%CRAWLER_DIR%"
    exit /B
)

if "%1"=="driver" (
    echo Fixing GeckoDriver installation...
    cd /d "%CRAWLER_DIR%"
    python "%CRAWLER_DIR%fix_drivers.py"
    pause
    exit /B
)

echo Unknown command: %1
echo Valid commands: setup, crawler, shell, driver
pause 