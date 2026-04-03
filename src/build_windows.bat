@echo off
echo Building ThreatPad for Windows...

:: Install PyInstaller if needed
echo Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller tkinterdnd2

:: Build the Windows executable
echo Building executable...
pyinstaller --onefile --windowed --name=ThreatPad --clean --icon=threatpad.ico threatpad.py

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