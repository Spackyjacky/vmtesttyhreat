@echo off
echo Building ThreatPad for Windows...

:: Install PyInstaller if needed
echo Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller tkinterdnd2

:: Remove stale spec file if present (causes icon path errors on rebuild)
if exist "ThreatPad.spec" del /f "ThreatPad.spec"

:: Build the Windows executable
echo Building executable...
if exist "threatpad.ico" (
    pyinstaller --onefile --windowed --name=ThreatPad --clean --icon=threatpad.ico --hidden-import=ascii_menu threatpad.py
) else (
    echo Note: threatpad.ico not found, building without custom icon...
    pyinstaller --onefile --windowed --name=ThreatPad --clean --hidden-import=ascii_menu threatpad.py
)

:: Check if build was successful
if exist "dist\ThreatPad.exe" (
    echo.
    echo ================================
    echo BUILD SUCCESSFUL!
    echo ================================
    echo Executable created: dist\ThreatPad.exe
    dir dist\ThreatPad.exe
    echo.
    echo The executable is ready for deployment!
) else (
    echo.
    echo ================================
    echo BUILD FAILED!
    echo ================================
    echo Check the output above for errors.
)

pause