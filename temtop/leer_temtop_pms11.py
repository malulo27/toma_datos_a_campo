#!/usr/bin/env python3
"""Lectura periódica del sensor de partículas Temtop PMS 11 (Elitech)
via Modbus RTU sobre RS485.

Ejemplo en Windows:
    py leer_temtop_pms11.py --puerto COM5 --archivo lecturas_pms11.csv --intervalo 60

Requiere:
    pip install pymodbus
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from pymodbus.client import ModbusSerialClient

BAUDRATE = 9600
DIRECCION_ESCLAVO = 254  # 0xFE
DIRECCION_REGISTRO = 3
CANTIDAD_REGISTROS = 12
CANALES = ["0.3um", "0.5um", "0.7um", "1.0um", "2.5um", "5.0um"]


def leer_sensor(client):
    """Hace una lectura y devuelve un diccionario canal -> valor (P/L), o None si hay error."""
    # Compatibilidad: pymodbus >=3.11 renombró el parámetro 'slave' a 'device_id'.
    try:
        result = client.read_input_registers(
            address=DIRECCION_REGISTRO,
            count=CANTIDAD_REGISTROS,
            device_id=DIRECCION_ESCLAVO,
        )
    except TypeError:
        result = client.read_input_registers(
            address=DIRECCION_REGISTRO,
            count=CANTIDAD_REGISTROS,
            slave=DIRECCION_ESCLAVO,
        )

    if result.isError():
        print(f"  Error en la lectura: {result}")
        return None

    regs = result.registers
    valores = {}
    for i, nombre in enumerate(CANALES):
        valor = (regs[i * 2] << 16) | regs[i * 2 + 1]
        valores[nombre] = valor

    return valores


def inicializar_csv(path: Path):
    """Crea el archivo CSV con encabezado si no existe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp"] + CANALES)
    except FileExistsError:
        pass


def guardar_lectura(path: Path, valores):
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp] + [valores[c] for c in CANALES])


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lee un Temtop PMS 11 por Modbus RTU/RS485 y guarda los conteos de partículas en CSV."
    )
    parser.add_argument(
        "--puerto",
        default="COM5",
        help="Puerto serie de Windows (predeterminado: COM5).",
    )
    parser.add_argument(
        "--archivo",
        default="lecturas_pms11.csv",
        help="Archivo CSV de salida (predeterminado: lecturas_pms11.csv).",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=60.0,
        help="Segundos entre lecturas (predeterminado: 60).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Timeout Modbus en segundos (predeterminado: 2).",
    )
    return parser.parse_args()


def main() -> int:
    args = parsear_argumentos()

    if args.intervalo <= 0:
        print("ERROR: --intervalo debe ser mayor que 0.", file=sys.stderr)
        return 2

    archivo = Path(args.archivo)
    inicializar_csv(archivo)

    client = ModbusSerialClient(
        port=args.puerto,
        baudrate=BAUDRATE,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=args.timeout,
    )

    try:
        if not client.connect():
            print(f"No se pudo conectar al puerto {args.puerto}", file=sys.stderr)
            return 1

        print(f"Conectado a {args.puerto}. Leyendo cada {args.intervalo:g}s. Ctrl+C para detener.")
        print(f"Guardando en: {archivo}\n")

        while True:
            valores = leer_sensor(client)

            if valores is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                linea = f"[{timestamp}] " + " | ".join(
                    f">{c}: {valores[c]}" for c in CANALES
                )
                print(linea)
                guardar_lectura(archivo, valores)
            else:
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    "Lectura fallida, se omite."
                )

            time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
        return 0
    finally:
        client.close()
        print("Puerto cerrado.")


if __name__ == "__main__":
    raise SystemExit(main())
