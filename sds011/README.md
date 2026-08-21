# Nova SDS011 en Windows

Script Python para leer un sensor Nova SDS011 conectado a una PC con Windows mediante un adaptador UART-USB y guardar las mediciones en CSV.

## Datos registrados

- fecha y hora
- PM2.5 en µg/m³
- PM10 en µg/m³
- identificador del sensor

## Requisitos

- Python 3
- adaptador UART-USB reconocido por Windows como puerto COM
- paquete `pyserial`

Instalación:

```powershell
py -m pip install -r requirements.txt
```

## Uso

Ejemplo para un sensor conectado en COM3:

```powershell
py sds011\leer_sds011.py --puerto COM3 --archivo datos_sds011.csv --intervalo 60
```

Si solamente existe un puerto serie en la PC, puede omitirse `--puerto` y el programa lo seleccionará automáticamente.

Para guardar cada trama válida recibida:

```powershell
py sds011\leer_sds011.py --puerto COM3 --intervalo 0
```

El archivo CSV tendrá este formato:

```text
fecha_hora,pm2_5_ug_m3,pm10_ug_m3,sensor_id
2026-08-21 15:30:00,8.4,16.2,AB12
```

## Descarga directa sin cuenta de GitHub

Desde cualquier PC Windows con acceso a Internet:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/malulo27/toma_datos_a_campo/main/sds011/leer_sds011.py" -OutFile "leer_sds011.py"
```

No es necesario iniciar sesión en GitHub.
