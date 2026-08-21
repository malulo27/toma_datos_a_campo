@echo off
setlocal

REM ==============================================
REM Configuracion - ajustar puertos si es necesario
REM ==============================================
REM Asignacion observada actualmente:
REM   Nova SDS011 -> COM3
REM   Temtop PMS11 -> COM4
set "PUERTO_SDS011=COM3"
set "PUERTO_TEMTOP=COM4"
set "INTERVALO=60"

REM Carpeta donde se encuentra este .bat
cd /d "%~dp0"

REM Comprueba que Python este disponible
where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: No se encontro el comando "py" de Python.
    echo Instale Python 3 y marque la opcion para agregarlo al PATH.
    pause
    exit /b 1
)

REM Comprueba que existan los scripts
if not exist "sds011\leer_sds011.py" (
    echo ERROR: No se encontro sds011\leer_sds011.py
    pause
    exit /b 1
)

if not exist "temtop\leer_temtop_pms11.py" (
    echo ERROR: No se encontro temtop\leer_temtop_pms11.py
    pause
    exit /b 1
)

REM Crea carpeta para los CSV si no existe
if not exist "datos" mkdir "datos"

echo Iniciando sensores...
echo SDS011: %PUERTO_SDS011%
echo Temtop: %PUERTO_TEMTOP%
echo Intervalo: %INTERVALO% segundos
echo.
echo IMPORTANTE: cada sensor debe usar un puerto COM distinto y funcional.
echo Actualmente COM4 (Temtop) presenta un error de configuracion en Windows.
echo No use este BAT con ambos sensores hasta resolver COM4.
echo.

start "SDS011" cmd /k py "sds011\leer_sds011.py" --puerto %PUERTO_SDS011% --archivo "datos\datos_sds011.csv" --intervalo %INTERVALO%
start "Temtop PMS11" cmd /k py "temtop\leer_temtop_pms11.py" --puerto %PUERTO_TEMTOP% --archivo "datos\lecturas_pms11.csv" --intervalo %INTERVALO%

echo Se abrieron dos ventanas, una por sensor.
echo Esta ventana puede cerrarse.
endlocal
