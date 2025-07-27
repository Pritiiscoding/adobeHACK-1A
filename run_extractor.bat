@echo off
setlocal

set PYTHON_SCRIPT=extract_outline.py
set PDF_PATH=%~1

if "%PDF_PATH%"=="" (
    echo Please provide the path to a PDF file.
    exit /b 1
)

echo Running PDF outline extractor...
"venv\Scripts\python.exe" "%PYTHON_SCRIPT%" "%PDF_PATH%"

endlocal
