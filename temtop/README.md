# Temtop PMS 11 (Elitech) en Windows

Script Python para leer periódicamente un sensor de partículas Temtop PMS 11 mediante Modbus RTU sobre RS485 y guardar los valores en CSV.

## Configuración verificada

- Puerto serie predeterminado: `COM5`
- Baudrate: `9600`
- Formato serie: `8N1`
- Dirección Modbus: `254` (`0xFE`)
- Registro inicial: `3`
- Cantidad de registros: `12`
- Intervalo predeterminado: `60` segundos
- Archivo predeterminado: `lecturas_pms11.csv`

## Canales registrados

- `0.3um`
- `0.5um`
- `0.7um`
- `1.0um`
- `2.5um`
- `5.0um`

Cada canal se obtiene combinando dos registros Modbus de 16 bits en un valor de 32 bits.

## Instalación

Desde la raíz del repositorio:

```powershell
py -m pip install -r requirements.txt
```

## Uso

Con los valores predeterminados:

```powershell
py temtop\leer_temtop_pms11.py
```

Indicando puerto, archivo e intervalo:

```powershell
py temtop\leer_temtop_pms11.py --puerto COM5 --archivo lecturas_pms11.csv --intervalo 60
```

## Descarga directa sin cuenta de GitHub

Desde una PC Windows con acceso a Internet:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/malulo27/toma_datos_a_campo/main/temtop/leer_temtop_pms11.py" -OutFile "leer_temtop_pms11.py"
```

No es necesario iniciar sesión en GitHub.
