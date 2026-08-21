# Toma de datos a campo

Scripts para adquirir y registrar datos de sensores conectados a una PC, con foco en uso desde Windows y descarga directa sin necesidad de una cuenta de GitHub.

## Sensores

### Nova SDS011

Disponible en `sds011/leer_sds011.py`.

Lee PM2.5 y PM10 mediante UART-USB, valida las tramas recibidas y guarda los registros en CSV.

### Temtop PMS 11 (Elitech)

Disponible en `temtop/leer_temtop_pms11.py`.

Lee por Modbus RTU sobre RS485 los canales de partículas `0.3um`, `0.5um`, `0.7um`, `1.0um`, `2.5um` y `5.0um`, y guarda los datos en CSV.

## Instalación básica

```powershell
py -m pip install -r requirements.txt
```

## Repositorio público

Al ser un repositorio público, los archivos pueden descargarse desde una PC con acceso a Internet sin iniciar sesión en GitHub, usando los enlaces RAW o `Invoke-WebRequest` desde PowerShell.
