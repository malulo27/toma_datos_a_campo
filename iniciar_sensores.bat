@echo off
setlocal

REM ==============================================
REM Configuracion - ajustar puertos si es necesario
REM ==============================================
REM Temtop confirmado actualmente en COM3.
REM El SDS011 debe tener OTRO puerto COM que abra correctamente.
set "PUERTO_TEMTOP=COM3"
set "PUERTO_SDS011=COM4"
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
echo Temtop: %PUERTO_TEMTOP%
echo SDS011: %PUERTO_SDS011%
echo Intervalo: %INTERVALO% segundos
echo.
echo IMPORTANTE: cada sensor debe usar un puerto COM distinto y funcional.
echo Si COM4 sigue dando error 31, no use este BAT hasta corregir ese puerto.
echo.

start "Temtop PMS11" cmd /k py "temtop\leer_temtop_pms11.py" --puerto %PUERTO_TEMTOP% --archivo "datos\lecturas_pms11.csv" --intervalo %INTERVALO%
start "SDS011" cmd /k py "sds011\leer_sds011.py" --puerto %PUERTO_SDS011% --archivo "datos\datos_sds011.csv" --intervalo %INTERVALO%

echo Se abrieron dos ventanas, una por sensor.
echo Esta ventana puede cerrarse.
endlocal
