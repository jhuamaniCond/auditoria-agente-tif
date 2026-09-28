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

Uso:
  python indexar_documentos.py --documentos documentos_empresa_demo.csv --salida indice_chunks.json
===============================================================================
"""

import argparse
import csv
import json

COLUMNAS = ["id_documento", "tipo", "fecha_documento", "responsable", "ubicacion", "contenido"]


def cargar_documentos(ruta):
    documentos = []
    with open(ruta, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        faltan = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
        if faltan:
            raise SystemExit("El CSV no tiene las columnas: %s" % ", ".join(faltan))
        for fila in lector:
            documentos.append(fila)
    return documentos


def trocear(contenido):
    """Divide el contenido en parrafos no vacios, separados por linea en blanco."""
    partes = [p.strip() for p in contenido.split("\n\n")]
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
    args = ap.parse_args()

    documentos = cargar_documentos(args.documentos)
    chunks = indexar(documentos)

    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump({"documentos_indexados": len(documentos), "chunks": chunks}, f, ensure_ascii=False, indent=2)

    print("%d documentos -> %d fragmentos indexados en %s" % (len(documentos), len(chunks), args.salida))


if __name__ == "__main__":
    main()
