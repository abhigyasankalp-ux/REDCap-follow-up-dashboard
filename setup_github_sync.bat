@echo off
setlocal enabledelayedexpansion
title REDCap Dashboard - GitHub Sync Setup & Repair
cls

cd /d "%~dp0"

echo =====================================================================
echo         GITHUB AUTOMATED SYNC CONFIGURATION & REPAIR TOOL
echo    REDCap Newborn Follow-up Dashboard (Dr. Vikar Saiyad & Abhigya)
echo =====================================================================
echo.

:: 1. Check Git Installation
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git for Windows is NOT installed or not found in system PATH!
    echo.
    echo Git is required to automatically push dashboard updates to GitHub.
    echo.
    echo Please download and install Git for Windows:
    echo   Official Download: https://git-scm.com/download/win
    echo.
    set /p OPEN_GIT="Would you like to open the Git download page in your browser? (Y/N): "
    if /i "!OPEN_GIT!"=="Y" (
        start "" "https://git-scm.com/download/win"
    )
    echo.
    echo After installing Git, please re-run this setup script.
    echo.
    pause
    exit /b 1
)

echo [OK] Git is installed on this computer.
git --version
echo.

:: 2. Ensure repository is initialized
if not exist ".git" (
    echo [INFO] Initializing Git repository in this folder...
    git init -b main
)

:: 3. Configure Git Identity if missing
for /f "tokens=*" %%a in ('git config user.name') do set GIT_USER=%%a
for /f "tokens=*" %%a in ('git config user.email') do set GIT_EMAIL=%%a

if "!GIT_USER!"=="" (
    echo [INFO] Setting Git user.name to 'Abhigya Sankalp'...
    git config user.name "Abhigya Sankalp"
) else (
    echo [OK] Git user.name: !GIT_USER!
)

if "!GIT_EMAIL!"=="" (
    echo [INFO] Setting Git user.email to 'abhigyasankalp.ux@gmail.com'...
    git config user.email "abhigyasankalp.ux@gmail.com"
) else (
    echo [OK] Git user.email: !GIT_EMAIL!
)
echo.

:: 4. Ensure Remote Origin URL is correct
set REPO_URL=https://github.com/abhigyasankalp-ux/REDCap-follow-up-dashboard.git
git remote remove origin >nul 2>nul
git remote add origin %REPO_URL%
echo [OK] Remote repository set to: %REPO_URL%
echo.

:: 5. Authentication Configuration
echo ---------------------------------------------------------------------
echo Choose how you would like to authenticate with GitHub on this PC:
echo ---------------------------------------------------------------------
echo   [1] Web Browser Login (Git Credential Manager - Recommended)
echo   [2] GitHub Personal Access Token (PAT)
echo   [3] Test current connection directly
echo.
set /p AUTH_CHOICE="Select an option (1, 2, or 3): "

if "%AUTH_CHOICE%"=="2" goto SETUP_TOKEN
if "%AUTH_CHOICE%"=="1" goto SETUP_BROWSER
goto TEST_CONNECTION

:SETUP_TOKEN
echo.
echo ---------------------------------------------------------------------
echo Step-by-step instructions to create a GitHub Personal Access Token:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Click "Generate new token" -^> "Generate new token (classic)"
echo   3. Note: "Dashboard Upload"
echo   4. Expiration: 90 days (or No expiration)
echo   5. Check the box: [x] repo (Full control of private/public repositories)
echo   6. Click "Generate token" at bottom and copy the token (starts with ghp_...)
echo ---------------------------------------------------------------------
echo.
set /p USER_TOKEN="Paste your GitHub Personal Access Token here: "
if "!USER_TOKEN!"=="" (
    echo [ERROR] No token entered. Skipping token save.
    goto TEST_CONNECTION
)

echo !USER_TOKEN!> github_token.txt
echo [SUCCESS] Token saved securely to 'github_token.txt' (shielded from git by .gitignore).
git remote set-url origin https://oauth2:!USER_TOKEN!@github.com/abhigyasankalp-ux/REDCap-follow-up-dashboard.git
goto TEST_CONNECTION

:SETUP_BROWSER
echo.
echo [INFO] Launching interactive browser authentication with Git Credential Manager...
echo If prompted, sign in with your GitHub account (abhigyasankalp-ux) in the browser window.
echo.
git credential-manager configure >nul 2>nul
git fetch origin main
if %errorlevel% neq 0 (
    echo.
    echo [NOTICE] If browser window didn't open or login failed, you can use Option 2 (Personal Access Token).
)
goto TEST_CONNECTION

:TEST_CONNECTION
echo.
echo =====================================================================
echo Testing GitHub connection and branch synchronization...
echo =====================================================================
git fetch origin main
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Could not connect to GitHub repository!
    echo Possible causes:
    echo   1. Incorrect credentials / permissions.
    echo   2. No internet connection.
    echo.
    echo Tip: You can generate a Personal Access Token at https://github.com/settings/tokens
    echo and paste it into "github_token.txt".
    echo.
    pause
    exit /b 1
)

echo [OK] Successfully connected to GitHub!
echo Synchronizing branches...
git pull --rebase origin main >nul 2>nul
if %errorlevel% neq 0 (
    git rebase --abort >nul 2>nul
    git pull origin main --allow-unrelated-histories --no-edit -X theirs >nul 2>nul
)

echo.
echo =====================================================================
echo [SUCCESS] GITHUB SYNCHRONIZATION IS FULLY CONFIGURED!
echo.
echo From now on, whenever you run "run_dashboard.bat", it will:
echo   1. Rebuild the dashboard with your latest Excel/REDCap data
echo   2. Automatically commit and push all updates to GitHub
echo   3. Update the live link:
echo      https://abhigyasankalp-ux.github.io/REDCap-follow-up-dashboard/
echo =====================================================================
echo.
pause
