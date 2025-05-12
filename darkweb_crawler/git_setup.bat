@echo off
echo =====================================================
echo     DARK WEB CRAWLER - GITHUB SETUP
echo =====================================================
echo This script will help you initialize a Git repository
echo and push your project to GitHub as a private repository.
echo.
echo Make sure you have:
echo  1. Git installed on your system
echo  2. A GitHub account
echo  3. GitHub CLI (gh) installed (optional but recommended)
echo.
echo Press any key to continue...
pause >nul

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo ❌ Git is not installed. Please install Git first.
    echo   Download from: https://git-scm.com/downloads
    pause
    exit /B
)

echo ✅ Git is installed.
echo.

:: Initialize repo if needed
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo.
)

:: Create .gitkeep files for empty directories
mkdir -p drivers
mkdir -p outputs\scraped_data
mkdir -p configs
echo. > drivers\.gitkeep
echo. > outputs\scraped_data\.gitkeep

:: Check if configs/sites.json exists, create sample if not
if not exist "configs\sites.json" (
    echo Creating sample sites.json...
    echo { > configs\sites.json
    echo   "sites": ["http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"], >> configs\sites.json
    echo   "max_pages": 5, >> configs\sites.json
    echo   "depth": 1 >> configs\sites.json
    echo } >> configs\sites.json
)

:: Add files to git
echo Adding files to Git...
git add .
git add -f drivers\.gitkeep outputs\scraped_data\.gitkeep
echo.

:: Check if GitHub CLI is installed
gh --version >nul 2>&1
if %errorlevel% EQU 0 (
    echo ✅ GitHub CLI is installed. You can use it to create a private repository.
    echo.
    echo To create and push to a private GitHub repository:
    echo.
    echo   1. Commit your changes:
    echo      git commit -m "Initial commit"
    echo.
    echo   2. Create a private repository on GitHub:
    echo      gh repo create darkweb_crawler --private --source=. --push
    echo.
) else (
    echo ℹ️ GitHub CLI not found. You can still create a repository manually.
    echo.
    echo To push to GitHub:
    echo.
    echo   1. Commit your changes:
    echo      git commit -m "Initial commit"
    echo.
    echo   2. Create a private repository on GitHub via browser
    echo      https://github.com/new
    echo.
    echo   3. Add the remote and push:
    echo      git remote add origin https://github.com/YOUR_USERNAME/darkweb_crawler.git
    echo      git branch -M main
    echo      git push -u origin main
    echo.
)

echo Would you like to commit your changes now? (y/n)
set /p commit_choice="Enter choice: "
if /i "%commit_choice%"=="y" (
    echo.
    echo Enter a commit message (default: "Initial commit"):
    set /p commit_msg="Commit message: "
    
    if "%commit_msg%"=="" set commit_msg=Initial commit
    
    echo.
    echo Committing with message: "%commit_msg%"
    git commit -m "%commit_msg%"
    
    echo.
    echo Repository is ready for pushing to GitHub!
    echo Remember to create a PRIVATE repository to avoid sharing sensitive code.
)

echo.
echo ✅ Git setup complete.
echo.
pause 