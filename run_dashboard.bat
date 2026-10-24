@echo off
setlocal enabledelayedexpansion
title REDCap Follow-up Dashboard Rebuilder
cls

:: Ensure current working directory is the script folder
cd /d "%~dp0"

echo =====================================================================
echo           SANKALP RESEARCH - NEWBORN FOLLOW-UP DASHBOARD
echo =====================================================================
echo.

:: 1. Check if Python is available in PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not recognized on this computer!
        echo.
        echo Possible Causes:
        echo   1. Python is not installed.
        echo   2. Python was installed without checking "Add python.exe to PATH".
        echo.
        echo Fix:
        echo   - Download Python from https://www.python.org/downloads/
        echo   - Run the installer and check the box: "[x] Add Python to PATH"
        echo   - Restart your terminal or computer.
        echo.
        pause
        exit /b 1
    )
    set PY_CMD=py
) else (
    set PY_CMD=python
)

:: 2. Check if required libraries are installed
echo Checking required libraries...
%PY_CMD% -c "import pandas, numpy, openpyxl, python_calamine" >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [NOTICE] Some required Python packages are missing on this computer.
    echo Installing missing packages...
    echo.
    
    :: Attempt 1: Install from offline wheels folder if available (No internet required!)
    if exist "wheels" (
        echo [INFO] Found local offline "wheels" folder. Installing offline...
        %PY_CMD% -m pip install --no-index --find-links=wheels pandas numpy openpyxl python-calamine xlrd reportlab jinja2
    )
    
    :: Attempt 2: If offline install was not run or failed, install online with trusted hosts (bypasses SSL/firewall blocks)
    %PY_CMD% -c "import pandas, numpy, openpyxl, python_calamine" >nul 2>nul
    if %errorlevel% neq 0 (
        echo [INFO] Installing online with trusted-host SSL bypass...
        if exist "requirements.txt" (
            %PY_CMD% -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org -r requirements.txt
        ) else (
            %PY_CMD% -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org pandas numpy openpyxl python-calamine xlrd reportlab jinja2
        )
    )

    :: Final check
    %PY_CMD% -c "import pandas, numpy, openpyxl, python_calamine" >nul 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install required packages!
        echo If you are behind an institutional firewall or proxy, see the instructions provided.
        echo.
        pause
        exit /b 1
    )
)

:: 3. Check Git availability for GitHub sync
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [NOTICE] Git is not installed on this PC.
    echo Dashboard will generate locally, but will not upload to GitHub.
    echo Run "setup_github_sync.bat" if you wish to configure GitHub upload.
    echo.
)

echo.
echo Step 1: Rebuilding dashboard with the latest datasheets...
echo.

%PY_CMD% generate_dashboard.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dashboard generation failed!
    echo Look at the error message above for details.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Rebuilt dashboard successfully!
echo.
echo Step 2: Opening "index.html"...
echo.

start "" "index.html"

echo.
echo =====================================================================
%PY_CMD% -c "import json, os; s=json.load(open('.github_sync_status.json')) if os.path.exists('.github_sync_status.json') else {}; exit(0 if s.get('success') else 1)" >nul 2>nul
if %errorlevel% equ 0 (
    echo [DONE] Dashboard generation & GitHub upload complete!
    echo Notice: If viewing on GitHub Pages, allow 1-2 minutes for deployment.
    echo Live link: https://abhigyasankalp-ux.github.io/REDCap-follow-up-dashboard/
) else (
    echo [NOTICE] Dashboard was generated locally, but GitHub upload did NOT succeed!
    echo If this is Abhigya's computer, please run:
    echo   -> setup_github_sync.bat
    echo to configure Git and your GitHub credentials or access token.
)
echo Press any key to close this window...
echo =====================================================================
pause >nul
