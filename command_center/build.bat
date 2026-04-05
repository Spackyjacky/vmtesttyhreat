@echo off
title Command Center — EXE Builder
color 06

echo.
echo  ==========================================
echo   COMMAND CENTER — Windows EXE Builder
echo  ==========================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Make sure Python is in your PATH.
    pause
    exit /b 1
)

:: Install / upgrade PyInstaller
echo  [1/3] Installing PyInstaller...
pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo  [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)
echo       Done.
echo.

:: Clean previous build
echo  [2/3] Cleaning previous build...
if exist dist\CommandCenter rmdir /s /q dist\CommandCenter
if exist build rmdir /s /q build
if exist CommandCenter.spec del /q CommandCenter.spec
echo       Done.
echo.

:: Build the exe
echo  [3/3] Building executable...
echo.

pyinstaller ^
    --name "CommandCenter" ^
    --windowed ^
    --onedir ^
    --clean ^
    --noconfirm ^
    command_center.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

:: Copy data folders next to the exe
echo.
echo  Copying data folders into dist\CommandCenter...
if exist dist\CommandCenter (
    xcopy /e /i /q memory   "dist\CommandCenter\memory"   >nul 2>&1
    xcopy /e /i /q data     "dist\CommandCenter\data"     >nul 2>&1
    xcopy /e /i /q scripts  "dist\CommandCenter\scripts"  >nul 2>&1
    if not exist "dist\CommandCenter\logs" mkdir "dist\CommandCenter\logs"
    echo  Done.
)

echo.
echo  ==========================================
echo   BUILD COMPLETE
echo   Executable: dist\CommandCenter\CommandCenter.exe
echo  ==========================================
echo.
echo  You can copy the entire dist\CommandCenter folder
echo  anywhere on your machine and run CommandCenter.exe
echo.
pause
