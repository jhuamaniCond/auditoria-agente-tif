# -*- coding: utf-8 -*-
"""
indexar_documentos.py
===============================================================================
Paso 1 del RAG (Retrieval-Augmented Generation) del skill
"verificador-cumplimiento-pims": trocea cada documento del inventario en
fragmentos (parrafos, separados por linea en blanco) y escribe un indice
(indice_chunks.json) que despues usa recuperar_fragmentos.py.

Es un RAG lexico (sin embeddings ni librerias externas): la recuperacion se
basa en coincidencia de palabras clave (TF-IDF), no en similitud semantica de
vectores. Alcanza para este corpus porque el vocabulario de los documentos y
el de requisitos.json se solapan a proposito (es como se redactan los
documentos reales de una auditoria). Solo libreria estandar de Python (>= 3.8).

Formato esperado del CSV de documentos:
  id_documento,tipo,fecha_documento,responsable,ubicacion,contenido

  contenido  texto con parrafos separados por una linea en blanco; cada
             parrafo se indexa como un fragmento (chunk) independiente.
             Acepta saltos de linea Unix (\n), Windows (\r\n) o clasico (\r),
             y CSV con o sin BOM. Si el CSV viene de Excel en codificacion
             ANSI/cp1252, use --encoding cp1252.

Uso:
  python indexar_documentos.py --documentos documentos_empresa_demo.csv --salida indice_chunks.json
===============================================================================
"""

import argparse
import csv
import json
import re
import sys

COLUMNAS = ["id_documento", "tipo", "fecha_documento", "responsable", "ubicacion", "contenido"]

# Parrafo = bloque separado del siguiente por una linea en blanco (tolera
# \r\n y lineas en blanco que contienen espacios o tabulaciones).
SEPARADOR_PARAFOS = re.compile(r"\n[ \t]*\n")


def cargar_documentos(ruta, encoding="utf-8-sig"):
    documentos = []
    try:
        archivo = open(ruta, encoding=encoding, newline="")
    except OSError as e:
        sys.exit("No se pudo abrir el CSV de documentos '%s': %s" % (ruta, e.strerror or e))
    try:
        with archivo:
            lector = csv.DictReader(archivo)
            faltan = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
            if faltan:
                sys.exit("El CSV no tiene las columnas: %s (se leyeron: %s)"
                         % (", ".join(faltan), ", ".join(lector.fieldnames or [])))
            for numero, fila in enumerate(lector, start=2):
                cortas = [c for c in COLUMNAS if fila.get(c) is None]
                if cortas:
                    sys.exit("Linea %d: faltan valores para %s (fila corta o celda sin comillas)"
                             % (numero, ", ".join(cortas)))
                documentos.append({c: (fila[c] or "") for c in COLUMNAS})
    except UnicodeDecodeError as e:
        sys.exit("El CSV no se puede decodificar como %s (%s, byte en posicion %d). "
                 "Si viene de Excel en ANSI, reintente con --encoding cp1252."
                 % (encoding, e.reason, e.start))
    return documentos


def trocear(contenido):
    """Divide el contenido en parrafos no vacios, separados por linea en blanco."""
    texto = contenido.replace("\r\n", "\n").replace("\r", "\n")
    partes = [p.strip() for p in SEPARADOR_PARAFOS.split(texto)]
    return [p for p in partes if p]


def indexar(documentos):
    chunks = []
    for doc in documentos:
        for i, texto in enumerate(trocear(doc["contenido"]), start=1):
            chunks.append({
                "id_documento": doc["id_documento"],
                "chunk_id": "%s-%02d" % (doc["id_documento"], i),
                "tipo": doc["tipo"],
                "fecha_documento": doc["fecha_documento"],
                "responsable": doc["responsable"],
                "ubicacion": doc["ubicacion"],
                "texto": texto,
            })
    return chunks


def main():
    ap = argparse.ArgumentParser(description="Indexa un corpus documental en fragmentos (chunks) para recuperacion RAG.")
    ap.add_argument("--documentos", required=True, help="CSV con los documentos (id_documento, tipo, fecha_documento, responsable, ubicacion, contenido)")
    ap.add_argument("--salida", default="indice_chunks.json", help="ruta del indice JSON a escribir")
    ap.add_argument("--encoding", default="utf-8-sig", help="codificacion del CSV (por defecto utf-8-sig; use cp1252 para CSV de Excel en ANSI)")
    args = ap.parse_args()

    documentos = cargar_documentos(args.documentos, encoding=args.encoding)
    chunks = indexar(documentos)

    if not documentos:
        sys.exit("ADVERTENCIA: el CSV no tiene filas de documentos; el indice quedara vacio.")
    sin_contenido = [d["id_documento"] for d in documentos if not d["contenido"].strip()]
    if sin_contenido:
        print("ADVERTENCIA: documentos sin texto en la columna 'contenido' (no generan fragmentos): %s"
              % ", ".join(sin_contenido))
    if not chunks:
        print("ADVERTENCIA: 0 fragmentos indexados. Revise que 'contenido' tenga parrafos separados por una linea en blanco.")

    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump({"documentos_indexados": len(documentos), "chunks": chunks}, f, ensure_ascii=False, indent=2)

    print("%d documentos -> %d fragmentos indexados en %s" % (len(documentos), len(chunks), args.salida))


if __name__ == "__main__":
    main()
