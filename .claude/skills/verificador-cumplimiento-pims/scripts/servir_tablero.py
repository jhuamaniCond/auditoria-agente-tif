# -*- coding: utf-8 -*-
"""
servir_tablero.py
===============================================================================
Sirve la carpeta que contiene tablero.html como una pequeña app web local,
usando solo http.server de la libreria estandar (sin Flask ni ningun
framework). Util para la demostracion: se abre en el navegador como una app,
no como un archivo suelto.

Uso:
  python servir_tablero.py --carpeta ./salida --puerto 8000
  (despues abrir http://localhost:8000/tablero.html)
===============================================================================
"""

import argparse
import functools
import http.server
import os


def main():
    ap = argparse.ArgumentParser(description="Sirve el tablero de cumplimiento como una app web local (solo stdlib).")
    ap.add_argument("--carpeta", default="salida", help="carpeta que contiene tablero.html")
    ap.add_argument("--puerto", type=int, default=8000, help="puerto local")
    args = ap.parse_args()

    carpeta = os.path.abspath(args.carpeta)
    if not os.path.exists(os.path.join(carpeta, "tablero.html")):
        raise SystemExit("No existe tablero.html en %s — ejecuta antes generar_tablero.py" % carpeta)

    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=carpeta)
    with http.server.HTTPServer(("localhost", args.puerto), manejador) as servidor:
        print("Tablero disponible en http://localhost:%d/tablero.html (Ctrl+C para detener)" % args.puerto)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
