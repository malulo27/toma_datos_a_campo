#!/usr/bin/env python3
"""Lectura y registro de un sensor Nova SDS011 por UART/USB.

Ejemplo en Windows:
    py leer_sds011.py --puerto COM3 --archivo datos_sds011.csv --intervalo 60

El sensor SDS011 transmite tramas de 10 bytes a 9600 baud, 8N1.
Este programa valida cabecera, cola y checksum antes de registrar los datos.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import serial
from serial.tools import list_ports

BAUDRATE = 9600
HEADER = 0xAA
COMMAND = 0xC0
TAIL = 0xAB
FRAME_SIZE = 10


def detectar_puerto() -> str:
    """Devuelve el único puerto serie disponible o informa cuáles existen."""
    puertos = list(list_ports.comports())

    if not puertos:
        raise RuntimeError("No se detectaron puertos serie en Windows.")

    if len(puertos) == 1:
        return puertos[0].device

    detalle = "\n".join(
        f"  {p.device}: {p.description or 'sin descripción'}" for p in puertos
    )
    raise RuntimeError(
        "Se detectó más de un puerto serie. Indique uno con --puerto.\n"
        f"Puertos disponibles:\n{detalle}"
    )


def leer_trama(ser: serial.Serial) -> Optional[Tuple[float, float, str]]:
    """Busca y valida una trama SDS011.

    Retorna (pm2_5, pm10, sensor_id) o None si la trama no es válida.
    """
    anterior: Optional[int] = None

    while True:
        dato = ser.read(1)
        if not dato:
            return None

        actual = dato[0]

        if anterior == HEADER and actual == COMMAND:
            resto = ser.read(8)
            if len(resto) != 8:
                return None

            trama = bytes([HEADER, COMMAND]) + resto

            if trama[-1] != TAIL:
                anterior = actual
                continue

            checksum_calculado = sum(trama[2:8]) & 0xFF
            checksum_recibido = trama[8]
            if checksum_calculado != checksum_recibido:
                anterior = actual
                continue

            pm2_5_raw = trama[2] | (trama[3] << 8)
            pm10_raw = trama[4] | (trama[5] << 8)
            sensor_id = f"{trama[6]:02X}{trama[7]:02X}"

            return pm2_5_raw / 10.0, pm10_raw / 10.0, sensor_id

        anterior = actual


def guardar_csv(
    archivo: Path,
    fecha_hora: datetime,
    pm2_5: float,
    pm10: float,
    sensor_id: str,
) -> None:
    """Agrega una medición a un CSV y crea la cabecera cuando es necesario."""
    archivo.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not archivo.exists() or archivo.stat().st_size == 0

    with archivo.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if nuevo:
            writer.writerow(["fecha_hora", "pm2_5_ug_m3", "pm10_ug_m3", "sensor_id"])
        writer.writerow(
            [
                fecha_hora.isoformat(sep=" ", timespec="seconds"),
                f"{pm2_5:.1f}",
                f"{pm10:.1f}",
                sensor_id,
            ]
        )


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lee un Nova SDS011 conectado por UART/USB y guarda PM2.5 y PM10 en CSV."
    )
    parser.add_argument(
        "--puerto",
        help="Puerto serie de Windows, por ejemplo COM3. Si se omite y hay uno solo, se detecta automáticamente.",
    )
    parser.add_argument(
        "--archivo",
        default="datos_sds011.csv",
        help="Archivo CSV de salida (predeterminado: datos_sds011.csv).",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=60.0,
        help="Segundos mínimos entre registros guardados. Use 0 para guardar todas las tramas válidas (predeterminado: 60).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout de lectura del puerto serie en segundos (predeterminado: 5).",
    )
    return parser.parse_args()


def main() -> int:
    args = parsear_argumentos()

    if args.intervalo < 0:
        print("ERROR: --intervalo no puede ser negativo.", file=sys.stderr)
        return 2

    try:
        puerto = args.puerto or detectar_puerto()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    archivo = Path(args.archivo)

    print(f"Puerto: {puerto}")
    print(f"Baudrate: {BAUDRATE} (8N1)")
    print(f"Archivo: {archivo.resolve()}")
    print(f"Intervalo de registro: {args.intervalo:g} s")
    print("Presione Ctrl+C para finalizar.\n")

    try:
        with serial.Serial(
            port=puerto,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=args.timeout,
        ) as ser:
            ser.reset_input_buffer()
            ultimo_guardado: Optional[float] = None

            while True:
                medicion = leer_trama(ser)
                if medicion is None:
                    print("Sin trama válida dentro del timeout.", file=sys.stderr)
                    continue

                pm2_5, pm10, sensor_id = medicion
                ahora_monotonic = time.monotonic()

                debe_guardar = (
                    args.intervalo == 0
                    or ultimo_guardado is None
                    or ahora_monotonic - ultimo_guardado >= args.intervalo
                )

                if debe_guardar:
                    ahora = datetime.now()
                    guardar_csv(archivo, ahora, pm2_5, pm10, sensor_id)
                    ultimo_guardado = ahora_monotonic
                    print(
                        f"{ahora:%Y-%m-%d %H:%M:%S} | "
                        f"PM2.5={pm2_5:.1f} µg/m³ | "
                        f"PM10={pm10:.1f} µg/m³ | ID={sensor_id}"
                    )

    except serial.SerialException as exc:
        print(f"ERROR de puerto serie: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nLectura finalizada por el usuario.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
