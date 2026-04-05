COMMAND CENTER — Build Instructions
=====================================

QUICK START
-----------
1. Open a terminal / command prompt in this folder
2. Run:   build.bat
3. Find the exe at:  dist\CommandCenter\CommandCenter.exe


REQUIREMENTS
------------
- Python 3.8+  (python.org)
- pip (comes with Python)
- Internet connection on first build (to download PyInstaller)


WHAT THE BUILD DOES
-------------------
1. Installs PyInstaller via pip
2. Bundles command_center.py into a Windows exe
3. Copies your memory/, data/, scripts/, logs/ folders next to the exe

The result is a dist\CommandCenter\ folder you can copy anywhere.
All your data files live next to the exe, not buried in a temp folder.


DISTRIBUTING
------------
Copy the entire dist\CommandCenter\ folder to wherever you want to run it.
Do NOT move just the .exe on its own — it needs the rest of the folder.


REBUILDING AFTER CODE CHANGES
------------------------------
Just run build.bat again. It cleans the previous build first.
Your data files in data/ and memory/ are NOT touched by the build.


TROUBLESHOOTING
---------------
- "Python not found"       → Add Python to your system PATH
- Antivirus blocks the exe → Add an exclusion for dist\CommandCenter\
  (PyInstaller exes are sometimes flagged as false positives)
- Missing module error     → Run: pip install <module> then rebuild
