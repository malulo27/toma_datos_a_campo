#!/usr/bin/env python3
"""
Lectura periódica del sensor de partículas Temtop PMS11 (Elitech)
vía Modbus RTU sobre RS485.

El PMS11 entrega conteos acumulados de partículas (partículas/L) para:
>0.3, >0.5, >0.7, >1.0, >2.5 y >5.0 µm.

Este script agrega PM1.0 y PM2.5 ESTIMADOS (µg/m³) a partir de esos conteos.
No es un valor PM2.5 nativo del PMS11: depende de supuestos sobre tamaño
representativo y densidad de las partículas.

Cada ejecución crea un CSV nuevo con fecha y hora en el nombre.

Requiere:
    py -m pip install pymodbus
"""

import argparse
import csv
import math
import time
from datetime import datetime
from pathlib import Path

from pymodbus.client import ModbusSerialClient


BAUDRATE = 9600
DIRECCION_ESCLAVO = 254
DIRECCION_REGISTRO = 3
CANTIDAD_REGISTROS = 12

CANALES = ["0.3um", "0.5um", "0.7um", "1.0um", "2.5um", "5.0um"]

# Límites de los intervalos usados para estimar masa.
BIN_LIMITS_PM1 = (
    (0.3, 0.5),
    (0.5, 0.7),
    (0.7, 1.0),
)

BIN_LIMITS_PM25 = (
    (0.3, 0.5),
    (0.5, 0.7),
    (0.7, 1.0),
    (1.0, 2.5),
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Lee Temtop PMS11 por Modbus RTU y guarda un CSV por ejecución."
    )
    parser.add_argument(
        "--puerto",
        default="COM6",
        help="Puerto COM del adaptador USB-RS485 (predeterminado: COM6)",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=6.0,
        help="Intervalo entre lecturas, en segundos (predeterminado: 6)",
    )
    parser.add_argument(
        "--directorio",
        default="datos",
        help="Carpeta donde guardar los CSV (predeterminado: datos)",
    )
    parser.add_argument(
        "--densidad",
        type=float,
        default=1.65,
        help=(
            "Densidad efectiva asumida de las partículas en g/cm3 "
            "(predeterminado: 1.65). Ajustable para calibración."
        ),
    )
    parser.add_argument(
        "--factor-pm1",
        type=float,
        default=1.0,
        help=(
            "Factor multiplicativo de calibración para PM1.0 estimado "
            "(predeterminado: 1.0)"
        ),
    )
    parser.add_argument(
        "--factor-pm25",
        type=float,
        default=1.0,
        help=(
            "Factor multiplicativo de calibración para PM2.5 estimado "
            "(predeterminado: 1.0)"
        ),
    )
    return parser.parse_args()


def leer_sensor(client):
    """Devuelve un diccionario canal -> partículas/L, o None si hay error."""
    try:
        result = client.read_input_registers(
            address=DIRECCION_REGISTRO,
            count=CANTIDAD_REGISTROS,
            device_id=DIRECCION_ESCLAVO,
        )
    except TypeError:
        # Compatibilidad con versiones anteriores de pymodbus.
        result = client.read_input_registers(
            address=DIRECCION_REGISTRO,
            count=CANTIDAD_REGISTROS,
            slave=DIRECCION_ESCLAVO,
        )

    if result.isError():
        print(f"Error en la lectura: {result}")
        return None

    regs = result.registers
    if len(regs) < CANTIDAD_REGISTROS:
        print(
            f"Respuesta incompleta: se esperaban {CANTIDAD_REGISTROS} "
            f"registros y llegaron {len(regs)}."
        )
        return None

    valores = {}
    for i, nombre in enumerate(CANALES):
        valor = (regs[i * 2] << 16) | regs[i * 2 + 1]
        valores[nombre] = valor

    return valores


def estimar_masa_ug_m3(valores, limites, densidad_g_cm3=1.65, factor=1.0):
    """
    Estima concentración másica (µg/m³) a partir de conteos acumulados del PMS11.

    Para cada intervalo:
      N(d_min-d_max) = N(>d_min) - N(>d_max)

    Se usa la media geométrica como diámetro representativo y se supone
    una partícula esférica con densidad efectiva constante.

    IMPORTANTE:
    El PMS11 comienza en >0.3 µm. Por lo tanto, estas estimaciones no incluyen
    partículas menores a 0.3 µm y no equivalen a una medición gravimétrica.
    """
    total = 0.0

    for d_min, d_max in limites:
        clave_min = f"{d_min:.1f}um"
        clave_max = f"{d_max:.1f}um"

        n_min = float(valores[clave_min])
        n_max = float(valores[clave_max])
        n_intervalo = max(n_min - n_max, 0.0)

        d_um = math.sqrt(d_min * d_max)

        masa_bin = (
            n_intervalo
            * densidad_g_cm3
            * (math.pi / 6.0)
            * (d_um ** 3)
            * 1e-3
        )
        total += masa_bin

    return total * factor


def estimar_pm1_ug_m3(valores, densidad_g_cm3=1.65, factor=1.0):
    return estimar_masa_ug_m3(
        valores,
        BIN_LIMITS_PM1,
        densidad_g_cm3=densidad_g_cm3,
        factor=factor,
    )


def estimar_pm25_ug_m3(valores, densidad_g_cm3=1.65, factor=1.0):
    return estimar_masa_ug_m3(
        valores,
        BIN_LIMITS_PM25,
        densidad_g_cm3=densidad_g_cm3,
        factor=factor,
    )

def crear_archivo_sesion(directorio):
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    return directorio / f"lecturas_pms11_{marca}.csv"


def inicializar_csv(path):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["timestamp"]
            + CANALES
            + ["pm1_0_estimado_ug_m3", "pm2_5_estimado_ug_m3"]
        )


def guardar_lectura(path, valores, pm1_estimado, pm25_estimado):
    with Path(path).open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow(
            [timestamp]
            + [valores[c] for c in CANALES]
            + [f"{pm1_estimado:.3f}", f"{pm25_estimado:.3f}"]
        )


def main():
    args = parse_args()

    if args.intervalo <= 0:
        raise SystemExit("--intervalo debe ser mayor que 0")
    if args.densidad <= 0:
        raise SystemExit("--densidad debe ser mayor que 0")
    if args.factor_pm1 <= 0:
        raise SystemExit("--factor-pm1 debe ser mayor que 0")
    if args.factor_pm25 <= 0:
        raise SystemExit("--factor-pm25 debe ser mayor que 0")

    archivo_csv = crear_archivo_sesion(args.directorio)
    inicializar_csv(archivo_csv)

    client = ModbusSerialClient(
        port=args.puerto,
        baudrate=BAUDRATE,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=2,
    )

    try:
        if not client.connect():
            print(f"No se pudo conectar al puerto {args.puerto}")
            return

        print(
            f"Conectado a {args.puerto}. "
            f"Leyendo cada {args.intervalo:g}s. Ctrl+C para detener."
        )
        print(f"CSV de esta ejecución: {archivo_csv}")
        print(
            "PM1.0 y PM2.5 mostrados = ESTIMACIONES derivadas de los conteos del PMS11 "
            f"(densidad={args.densidad:g} g/cm3, "
            f"factor PM1={args.factor_pm1:g}, factor PM2.5={args.factor_pm25:g}).\n"
        )

        while True:
            valores = leer_sensor(client)

            if valores is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pm1_estimado = estimar_pm1_ug_m3(
                    valores,
                    densidad_g_cm3=args.densidad,
                    factor=args.factor_pm1,
                )
                pm25_estimado = estimar_pm25_ug_m3(
                    valores,
                    densidad_g_cm3=args.densidad,
                    factor=args.factor_pm25,
                )

                conteos = " | ".join(
                    f">{c}: {valores[c]} P/L" for c in CANALES
                )

                print(
                    f"[{timestamp}] "
                    f"PM1.0 estimado: {pm1_estimado:.2f} µg/m³ | "
                    f"PM2.5 estimado: {pm25_estimado:.2f} µg/m³ | "
                    f"{conteos}"
                )

                guardar_lectura(archivo_csv, valores, pm1_estimado, pm25_estimado)
            else:
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    "Lectura fallida, se omite."
                )

            time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")

    finally:
        client.close()
        print("Puerto cerrado.")
        print(f"Datos guardados en: {archivo_csv}")


if __name__ == "__main__":
    main()
