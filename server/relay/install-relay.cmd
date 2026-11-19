@echo off
rem Instaluje przekaznik Polish Fighters na serwerze Oracle (Ubuntu) z Windows przez SSH.
rem Uruchom dwuklikiem albo w cmd: install-relay.cmd [ADRES_IP] [PLIK_KLUCZA_SSH]
setlocal EnableExtensions
chcp 65001 >nul

set "API=https://www.projektocalenie.pl/projekty/polish-fighters/api"
set "SCRIPT=https://raw.githubusercontent.com/w4sy1/polish-fighters/main/server/relay/install-relay.sh"
set "SSH_USER=ubuntu"
set "HERE=%~dp0"
set "LOG=%HERE%install-relay.log"
set "CONFIG=%HERE%relay_config.py"

where ssh >nul 2>&1
if errorlevel 1 (
  echo Brak programu ssh. Wlacz go: Ustawienia ^> Aplikacje ^> Funkcje opcjonalne ^> Klient OpenSSH.
  goto :fail
)

set "IP=%~1"
if not defined IP set /p "IP=Publiczny adres IP serwera Oracle: "
if not defined IP goto :fail

set "KEY=%~2"
if not defined KEY set /p "KEY=Plik klucza SSH pobrany z Oracle (przeciagnij go tutaj): "
if not defined KEY goto :fail
set "KEY=%KEY:"=%"
if not exist "%KEY%" (
  echo Nie ma pliku klucza: %KEY%
  goto :fail
)

rem OpenSSH odrzuca klucz, ktory moga czytac inni uzytkownicy Windows.
icacls "%KEY%" /inheritance:r /grant:r "%USERNAME%:R" >nul

echo.
echo Lacze z %SSH_USER%@%IP% i instaluje przekaznik (1-3 minuty)...
ssh -i "%KEY%" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 %SSH_USER%@%IP% "curl -fsSL %SCRIPT% | sudo bash -s -- %API%" > "%LOG%" 2>&1
set "RESULT=%errorlevel%"
type "%LOG%"
if not "%RESULT%"=="0" (
  echo.
  echo Instalacja nie powiodla sie. Pelny zapis: %LOG%
  goto :fail
)

findstr /b "RELAY_" "%LOG%" > "%CONFIG%"
for %%A in ("%CONFIG%") do if %%~zA==0 (
  echo Nie znaleziono ustawien przekaznika w zapisie: %LOG%
  goto :fail
)
del "%LOG%" >nul 2>&1

echo.
echo Gotowe. Zapisano: %CONFIG%
echo Wgraj ten plik na hosting obok passenger_wsgi.py i zrestartuj aplikacje Python.
echo Plik zawiera tajny klucz: nie udostepniaj go.
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
