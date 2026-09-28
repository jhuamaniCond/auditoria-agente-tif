# -*- coding: utf-8 -*-
"""
servir_tablero.py
===============================================================================
Sirve la carpeta que contiene tablero.html como una pequena app web local,
usando solo http.server de la libreria estandar (sin Flask ni ningun
framework). Util para la demostracion: se abre en el navegador como una app,
no como un archivo suelto.

Por defecto escucha SOLO en localhost (no se expone a la red). Con
--solo-tablero no lista la carpeta ni sirve los demas archivos (resumen.json,
hallazgos): solo tablero.html.

Uso:
  python servir_tablero.py --carpeta ./salida --puerto 8000
  python servir_tablero.py --carpeta ./salida --solo-tablero
  (despues abrir http://localhost:8000/tablero.html)
===============================================================================
"""

import argparse
import functools
import http
import http.server
import os
import sys


class SoloTableroHandler(http.server.SimpleHTTPRequestHandler):
    """No expone el listing del directorio ni otros archivos: solo el tablero."""

    def list_directory(self, path):
        self.send_error(http.HTTPStatus.NOT_FOUND, "Solo se sirve tablero.html")
        return None

    def send_head(self):
        self.path = "/tablero.html"
        return super().send_head()


def main():
    ap = argparse.ArgumentParser(description="Sirve el tablero de cumplimiento como una app web local (solo stdlib).")
    ap.add_argument("--carpeta", default="salida", help="carpeta que contiene tablero.html")
    ap.add_argument("--puerto", type=int, default=8000, help="puerto local")
    ap.add_argument("--solo-tablero", action="store_true",
                    help="sirve exclusivamente tablero.html (sin listing ni acceso a resumen.json/hallazgos)")
    args = ap.parse_args()

    carpeta = os.path.abspath(args.carpeta)
    if not os.path.exists(os.path.join(carpeta, "tablero.html")):
        sys.exit("No existe tablero.html en %s — ejecuta antes generar_tablero.py" % carpeta)

    if args.solo_tablero:
        manejador = functools.partial(SoloTableroHandler, directory=carpeta)
    else:
        manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=carpeta)

    try:
        servidor = http.server.HTTPServer(("localhost", args.puerto), manejador)
    except OSError as e:
        sys.exit("No se pudo abrir localhost:%d (%s). Prueba con otro puerto: --puerto %d"
                 % (args.puerto, e.strerror or e, args.puerto + 1))
    with servidor:
        print("Tablero disponible en http://localhost:%d/tablero.html (Ctrl+C para detener)" % args.puerto)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
