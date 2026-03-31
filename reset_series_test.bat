@echo off
setlocal

pushd "%~dp0" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Could not switch to script directory.
  exit /b 1
)

set "ROOT=%~dp0"
set "SCRIPT=%ROOT%_reset_series_api_test.py"
set "PY_EXE=C:/Users/SJKnight/virtual_environments/sailing_app/Scripts/python.exe"

if not exist "%SCRIPT%" (
  echo ERROR: Could not find _reset_series_api_test.py in %ROOT%
  exit /b 1
)

if not exist "%PY_EXE%" (
  set "PY_EXE=python"
)

echo.
echo ===============================================
echo   Series reset helper for QA testing
echo ===============================================
echo 1^) Default reset ^(Series_API_Test, club cleanup, 1 race tomorrow^)
echo 2^) Series-only cleanup ^(Series_API_Test only^)
echo 3^) Create 3 races ^(2 days ahead, 30 min spacing^)
echo 4^) Custom args
echo 5^) Show script help
echo.
set /p CHOICE=Choose option [1-5]: 

if "%CHOICE%"=="1" goto option1
if "%CHOICE%"=="2" goto option2
if "%CHOICE%"=="3" goto option3
if "%CHOICE%"=="4" goto option4
if "%CHOICE%"=="5" goto option5

echo Invalid option.
exit /b 1

:option1
"%PY_EXE%" "%SCRIPT%"
goto done

:option2
"%PY_EXE%" "%SCRIPT%" --series-name "Series_API_Test" --cleanup-scope series
goto done

:option3
"%PY_EXE%" "%SCRIPT%" --series-name "Series_API_Test" --cleanup-scope series --race-count 3 --days-ahead 2 --spacing-minutes 30
goto done

:option4
echo Example: --series-name "Series_API_Test" --cleanup-scope series --race-count 2
set /p EXTRA=Enter extra args for _reset_series_api_test.py: 
"%PY_EXE%" "%SCRIPT%" %EXTRA%
goto done

:option5
"%PY_EXE%" "%SCRIPT%" --help
goto done

:done
echo.
echo Exit code: %ERRORLEVEL%
pause
popd
endlocal
