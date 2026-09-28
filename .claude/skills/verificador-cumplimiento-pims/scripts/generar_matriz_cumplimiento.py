# -*- coding: utf-8 -*-
"""
generar_matriz_cumplimiento.py
===============================================================================
Ultimo paso del skill "verificador-cumplimiento-pims". NO decide si un
requisito esta cubierto: esa lectura de los fragmentos recuperados por RAG y
el juicio de suficiencia los hace el modelo (SKILL.md, paso 4), escribiendo
`evaluacion.csv`. Este script solo:

  - valida que evaluacion.csv trae un veredicto para cada uno de los 15
    requisitos de requisitos.json,
  - cruza cada veredicto con requisitos.json (nombre, clausula, criticidad)
    para enriquecer el reporte,
  - calcula la prioridad de atencion (criticidad, un nivel menos si PARCIAL),
  - genera resumen.json y un hallazgo_<REQ-ID>.md por cada requisito no
    CUBIERTO, citando la justificacion textual que escribio el modelo,
  - si se le da el indice de documentos, reporta cuales nunca fueron citados
    como evidencia por ningun requisito (candidatos a "no relacionados").

Solo libreria estandar de Python (>= 3.8).

Formato esperado de evaluacion.csv (una fila por requisito, REQ-01..REQ-15):
  requisito_id      REQ-01 .. REQ-15
  estado            CUBIERTO | PARCIAL | SIN_EVIDENCIA
  evidencia_citada  chunk_id(s) que sustentan el veredicto, separados por ";"
                    (vacio si SIN_EVIDENCIA)
  justificacion     explicacion escrita por el modelo tras leer los
                    fragmentos recuperados; para PARCIAL/SIN_EVIDENCIA debe
                    decir explicitamente que falta o que esta mal

Uso:
  python generar_matriz_cumplimiento.py --evaluacion evaluacion.csv --requisitos requisitos.json --salida ./salida
  python generar_matriz_cumplimiento.py --evaluacion evaluacion.csv --requisitos requisitos.json --indice indice_chunks.json --salida ./salida
===============================================================================
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
REQUISITOS_POR_DEFECTO = os.path.join(AQUI, "..", "requisitos.json")
PLANTILLA_HALLAZGO = os.path.join(AQUI, "..", "plantillas", "hallazgo_cumplimiento.md")

ESTADOS_VALIDOS = {"CUBIERTO", "PARCIAL", "SIN_EVIDENCIA"}
PLAZO_DIAS_POR_PRIORIDAD = {"alta": 30, "media": 60, "baja": 90}


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_evaluacion(ruta):
    filas = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        columnas = ["requisito_id", "estado", "evidencia_citada", "justificacion"]
        faltan = [c for c in columnas if c not in (lector.fieldnames or [])]
        if faltan:
            sys.exit("evaluacion.csv no tiene las columnas: %s" % ", ".join(faltan))
        for numero, fila in enumerate(lector, start=2):
            req_id = fila["requisito_id"].strip()
            estado = fila["estado"].strip().upper()
            if estado not in ESTADOS_VALIDOS:
                sys.exit("Linea %d: estado invalido '%s' (CUBIERTO|PARCIAL|SIN_EVIDENCIA)" % (numero, estado))
            if req_id in filas:
                sys.exit("Linea %d: requisito_id '%s' repetido" % (numero, req_id))
            evidencia = [e.strip() for e in fila["evidencia_citada"].split(";") if e.strip()]
            filas[req_id] = {
                "requisito_id": req_id, "estado": estado,
                "evidencia_citada": evidencia, "justificacion": fila["justificacion"].strip(),
            }
    return filas


def prioridad_atencion(criticidad, estado, cfg_prioridad):
    if estado == "CUBIERTO":
        return None
    orden = cfg_prioridad["orden_criticidad"]
    nivel = orden.index(criticidad)
    if estado == "PARCIAL" and cfg_prioridad.get("bajar_un_nivel_si_parcial") and nivel > 0:
        nivel -= 1
    return orden[nivel]


def construir_resultados(evaluacion, requisitos_cfg):
    faltantes = sorted(set(requisitos_cfg["requisitos"]) - set(evaluacion))
    if faltantes:
        sys.exit("evaluacion.csv no trae veredicto para: %s" % ", ".join(faltantes))
    sobrantes = sorted(set(evaluacion) - set(requisitos_cfg["requisitos"]))
    if sobrantes:
        sys.exit("evaluacion.csv trae requisito_id que no existen en requisitos.json: %s" % ", ".join(sobrantes))

    resultados = []
    for req_id, req in requisitos_cfg["requisitos"].items():
        ev = evaluacion[req_id]
        resultados.append({
            "requisito_id": req_id, "nombre": req["nombre"], "clausula": req["clausula"],
            "descripcion": req["descripcion"], "tipo_evidencia_esperada": req["tipo_evidencia_esperada"],
            "criticidad": req["criticidad"], "estado": ev["estado"],
            "evidencia_citada": ev["evidencia_citada"], "justificacion": ev["justificacion"],
            "prioridad_atencion": prioridad_atencion(req["criticidad"], ev["estado"], requisitos_cfg["prioridad"]),
        })

    orden_estado = {"SIN_EVIDENCIA": 0, "PARCIAL": 1, "CUBIERTO": 2}
    orden_criticidad = {"alta": 0, "media": 1, "baja": 2}
    resultados.sort(key=lambda r: (orden_estado[r["estado"]], orden_criticidad[r["criticidad"]], r["requisito_id"]))
    return resultados


def documentos_no_citados(ruta_indice, resultados):
    if not ruta_indice or not os.path.exists(ruta_indice):
        return None
    indice = cargar_json(ruta_indice)
    todos = sorted({c["id_documento"] for c in indice["chunks"]})
    citados = set()
    for r in resultados:
        for chunk_id in r["evidencia_citada"]:
            citados.add(chunk_id.rsplit("-", 1)[0])
    return [d for d in todos if d not in citados]


def cargar_plantilla():
    if os.path.exists(PLANTILLA_HALLAZGO):
        with open(PLANTILLA_HALLAZGO, encoding="utf-8") as f:
            return f.read()
    return None


def texto_acciones(r):
    plazo = PLAZO_DIAS_POR_PRIORIDAD[r["prioridad_atencion"]]
    tipo = r["tipo_evidencia_esperada"][0] if r["tipo_evidencia_esperada"] else "evidencia"
    acciones = []
    if r["estado"] == "SIN_EVIDENCIA":
        acciones.append("Elaborar y aprobar %s que cubra el requisito." % tipo)
    else:
        acciones.append("Corregir o completar la evidencia existente para cerrar lo señalado en la brecha (sección 3).")
    acciones.append("Registrar la evidencia corregida y volver a indexarla.")
    acciones.append("Asignar responsable y verificar antes de %d dias (prioridad %s)."
                     % (plazo, r["prioridad_atencion"].upper()))
    return "\n".join("%d. %s" % (i, a) for i, a in enumerate(acciones, start=1))


def escribir_hallazgo(r, indice, carpeta, plantilla, ahora):
    id_hallazgo = "GAP-%s-%03d" % (ahora.strftime("%Y%m%d"), indice)
    ruta = os.path.join(carpeta, "hallazgo_%s.md" % r["requisito_id"])

    evidencia_txt = ("- " + "\n- ".join(r["evidencia_citada"])) if r["evidencia_citada"] else "Ninguna evidencia relevante encontrada tras revisar los documentos recuperados."

    campos = {
        "id_hallazgo": id_hallazgo,
        "fecha_revision": ahora.strftime("%Y-%m-%d %H:%M:%S"),
        "requisito_id": r["requisito_id"],
        "nombre_requisito": r["nombre"],
        "clausula": r["clausula"],
        "criticidad": r["criticidad"].upper(),
        "estado": r["estado"].replace("_", " "),
        "prioridad_atencion": r["prioridad_atencion"].upper(),
        "tipo_evidencia_esperada": ", ".join(r["tipo_evidencia_esperada"]),
        "descripcion": r["descripcion"],
        "evidencia_encontrada": evidencia_txt,
        "brecha": r["justificacion"],
        "acciones": texto_acciones(r),
    }

    if plantilla:
        texto = plantilla
        for k, v in campos.items():
            texto = texto.replace("{{%s}}" % k, v)
    else:
        texto = "\n".join("%s: %s" % (k, v) for k, v in campos.items())

    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(texto)
    return id_hallazgo, ruta


def imprimir_resumen(resultados, hallazgos, no_citados):
    cubiertos = sum(1 for r in resultados if r["estado"] == "CUBIERTO")
    parciales = sum(1 for r in resultados if r["estado"] == "PARCIAL")
    sin_evidencia = sum(1 for r in resultados if r["estado"] == "SIN_EVIDENCIA")

    print("=" * 92)
    print("VERIFICADOR DE CUMPLIMIENTO PIMS - matriz de cumplimiento")
    print("=" * 92)
    print("Requisitos evaluados : %d" % len(resultados))
    print("Cubiertos            : %d" % cubiertos)
    print("Parciales            : %d" % parciales)
    print("Sin evidencia        : %d" % sin_evidencia)
    print("Hallazgos generados  : %d" % len(hallazgos))
    if no_citados:
        print("Documentos no citados por ningun requisito: %s" % ", ".join(no_citados))
    print("-" * 92)
    print("%-8s %-46s %-14s %-10s %s" % ("REQ", "NOMBRE", "ESTADO", "CRITICID.", "PRIORIDAD ATENCION"))
    print("-" * 92)
    for r in resultados:
        prioridad = r["prioridad_atencion"].upper() if r["prioridad_atencion"] else "-"
        print("%-8s %-46s %-14s %-10s %s" % (
            r["requisito_id"], r["nombre"][:46], r["estado"], r["criticidad"].upper(), prioridad))
    print("-" * 92)
    for id_h, ruta, r in hallazgos:
        print("%s  %-8s %-10s -> %s" % (id_h, r["requisito_id"], r["prioridad_atencion"].upper(), os.path.relpath(ruta)))


def main():
    ap = argparse.ArgumentParser(description="Formatea la evaluacion de cumplimiento (hecha por el modelo) en matriz y hallazgos.")
    ap.add_argument("--evaluacion", required=True, help="CSV con el veredicto por requisito, escrito por el modelo")
    ap.add_argument("--requisitos", default=REQUISITOS_POR_DEFECTO, help="JSON de requisitos (por defecto: requisitos.json del skill)")
    ap.add_argument("--indice", default=None, help="indice_chunks.json, para reportar documentos no citados por ningun requisito")
    ap.add_argument("--salida", default="salida", help="carpeta donde se escriben resumen.json y hallazgos")
    args = ap.parse_args()

    requisitos_cfg = cargar_json(args.requisitos)
    evaluacion = cargar_evaluacion(args.evaluacion)
    resultados = construir_resultados(evaluacion, requisitos_cfg)
    no_citados = documentos_no_citados(args.indice, resultados)

    os.makedirs(args.salida, exist_ok=True)
    ahora = datetime.now().replace(microsecond=0)
    plantilla = cargar_plantilla()
    hallazgos = []
    for r in resultados:
        if r["estado"] != "CUBIERTO":
            id_h, ruta = escribir_hallazgo(r, len(hallazgos) + 1, args.salida, plantilla, ahora)
            hallazgos.append((id_h, ruta, r))

    with open(os.path.join(args.salida, "resumen.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "generado": ahora.strftime("%Y-%m-%d %H:%M:%S"),
            "archivo_evaluacion": os.path.basename(args.evaluacion),
            "requisitos_evaluados": len(resultados),
            "cubiertos": sum(1 for r in resultados if r["estado"] == "CUBIERTO"),
            "parciales": sum(1 for r in resultados if r["estado"] == "PARCIAL"),
            "sin_evidencia": sum(1 for r in resultados if r["estado"] == "SIN_EVIDENCIA"),
            "documentos_no_citados": no_citados,
            "resultados": resultados,
        }, fh, ensure_ascii=False, indent=2)

    imprimir_resumen(resultados, hallazgos, no_citados)
    print("\nresumen.json escrito en %s" % os.path.relpath(args.salida))


if __name__ == "__main__":
    main()
