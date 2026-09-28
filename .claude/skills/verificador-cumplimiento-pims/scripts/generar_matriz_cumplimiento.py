# -*- coding: utf-8 -*-
"""
generar_matriz_cumplimiento.py
===============================================================================
Ultimo paso del skill "verificador-cumplimiento-pims". NO decide si un
requisito esta cubierto: esa lectura de los fragmentos recuperados por RAG y
el juicio de suficiencia los hace el modelo (SKILL.md, paso 4), escribiendo
`evaluacion.csv`. Este script:

  - valida que evaluacion.csv trae un veredicto para cada uno de los 15
    requisitos de requisitos.json,
  - valida las citas: si se le da el indice (indice_chunks.json), NINGUN
    chunk_id citado puede ser inventado (existe en el indice), y todo
    veredicto CUBIERTO/PARCIAL debe traer al menos una cita — asi cada
    decision es re-verificable releyendo el fragmento,
  - cruza cada veredicto con requisitos.json (nombre, clausula, criticidad)
    para enriquecer el reporte, y emite ADVERTENCIAS informativas (no cambian
    el veredicto): evidencia citada con fecha posiblemente vencida segun
    'vigencia_max_dias', o cuyo tipo no coincide con el esperado cuando el
    veredicto es CUBIERTO,
  - calcula la prioridad de atencion (criticidad, un nivel menos si PARCIAL),
  - genera resumen.json y un hallazgo_<REQ-ID>.md por cada requisito no
    CUBIERTO, citando la justificacion textual que escribio el modelo,
  - con el indice, reporta cuales documentos nunca fueron citados como
    evidencia por ningun requisito (candidatos a "no relacionados").

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
  python generar_matriz_cumplimiento.py --evaluacion evaluacion.csv --requisitos requisitos.json --indice indice_chunks.json --salida ./salida
  python generar_matriz_cumplimiento.py --evaluacion evaluacion.csv --salida ./salida   # sin validacion de citas
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
FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]


def cargar_json(ruta, descripcion):
    """Lee un JSON con mensajes de error claros en vez de traceback crudo."""
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            return json.load(f)
    except OSError as e:
        sys.exit("No se pudo leer %s '%s': %s" % (descripcion, ruta, e.strerror or e))
    except json.JSONDecodeError as e:
        sys.exit("%s '%s' no es JSON valido: %s (linea %d, columna %d)"
                 % (descripcion, ruta, e.msg, e.lineno, e.colno))


def cargar_evaluacion(ruta):
    filas = {}
    try:
        archivo = open(ruta, encoding="utf-8-sig", newline="")
    except OSError as e:
        sys.exit("No se pudo abrir evaluacion.csv '%s': %s" % (ruta, e.strerror or e))
    try:
        with archivo:
            lector = csv.DictReader(archivo)
            columnas = ["requisito_id", "estado", "evidencia_citada", "justificacion"]
            faltan = [c for c in columnas if c not in (lector.fieldnames or [])]
            if faltan:
                sys.exit("evaluacion.csv no tiene las columnas: %s" % ", ".join(faltan))
            for numero, fila in enumerate(lector, start=2):
                cortas = [c for c in columnas if fila.get(c) is None]
                if cortas:
                    sys.exit("Linea %d: faltan valores para %s (fila corta o justificacion sin comillas)"
                             % (numero, ", ".join(cortas)))
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
    except UnicodeDecodeError as e:
        sys.exit("evaluacion.csv no se puede decodificar como UTF-8 (%s, byte en posicion %d)."
                 % (e.reason, e.start))
    return filas


def validar_config_requisitos(requisitos_cfg):
    """Chequea la forma de requisitos.json con errores claros (parametrizable)."""
    if "requisitos" not in requisitos_cfg or "prioridad" not in requisitos_cfg:
        sys.exit("requisitos.json debe tener las claves 'requisitos' y 'prioridad'.")
    orden = [str(n).strip().lower() for n in requisitos_cfg["prioridad"].get("orden_criticidad", [])]
    if not orden:
        sys.exit("requisitos.json: prioridad.orden_criticidad esta vacio o falta.")
    for req_id, req in requisitos_cfg["requisitos"].items():
        crit = str(req.get("criticidad", "")).strip().lower()
        if crit not in orden:
            sys.exit("%s: criticidad '%s' no esta en orden_criticidad %s." % (req_id, crit, orden))
    return orden


def prioridad_atencion(criticidad, estado, cfg_prioridad, orden):
    if estado == "CUBIERTO":
        return None
    nivel = orden.index(criticidad)
    if estado == "PARCIAL" and cfg_prioridad.get("bajar_un_nivel_si_parcial") and nivel > 0:
        nivel -= 1
    return orden[nivel]


def plazo_dias(prioridad, orden):
    if prioridad in PLAZO_DIAS_POR_PRIORIDAD:
        return PLAZO_DIAS_POR_PRIORIDAD[prioridad]
    # niveles personalizados: se asignan por posicion (el mas alto 30 dias)
    nivel = orden.index(prioridad)
    por_posicion = {len(orden) - 1: 30, 1: 60, 0: 90}
    return por_posicion.get(nivel, 30)


def parsear_fecha(texto, req_id):
    """Acepta ISO (yyyy-mm-dd) o dia/mes/anio; devuelve date o None con aviso."""
    texto = (texto or "").strip()
    if not texto:
        return None
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    print("ADVERTENCIA: %s: no se reconocio la fecha '%s' (use yyyy-mm-dd o dd/mm/aaaa); se omite el control de vigencia."
          % (req_id, texto))
    return None


def validar_citas_y_advertir(evaluacion, requisitos_cfg, mapa_chunks, hoy):
    """Errores duros (citas inventadas, veredicto sin cita) y advertencias
    informativas por requisito (vigencia, tipo de evidencia)."""
    errores = []
    advertencias = {}
    requisitos = requisitos_cfg["requisitos"]

    for req_id, ev in evaluacion.items():
        req = requisitos[req_id]
        avisos = []
        if ev["estado"] in ("CUBIERTO", "PARCIAL") and not ev["evidencia_citada"]:
            errores.append("%s (%s): el veredicto no cita ningun chunk_id. Toda decision CUBIERTO/PARCIAL "
                           "debe ser re-verificable releyendo el fragmento citado (SKILL.md, paso 4)." % (req_id, ev["estado"]))
        if ev["estado"] == "SIN_EVIDENCIA" and ev["evidencia_citada"]:
            avisos.append("Estado SIN_EVIDENCIA pero cita %s: si la evidencia existe y es relevante, reevalue el veredicto."
                          % ", ".join(ev["evidencia_citada"]))

        tipos_esperados = [str(t).strip().lower() for t in req.get("tipo_evidencia_esperada", [])]
        tipos_citados = set()
        for chunk_id in ev["evidencia_citada"]:
            if mapa_chunks is not None and chunk_id not in mapa_chunks:
                errores.append("%s: el chunk_id citado '%s' NO existe en el indice (las citas deben ser exactas, "
                               "copiadas de fragmentos_recuperados.json/indice_chunks.json)." % (req_id, chunk_id))
                continue
            chunk = mapa_chunks.get(chunk_id) if mapa_chunks is not None else None
            if chunk is None:
                continue
            tipos_citados.add(str(chunk["tipo"]).strip().lower())
            vigencia = req.get("vigencia_max_dias")
            if hoy is not None and isinstance(vigencia, (int, float)) and vigencia > 0:
                fecha = parsear_fecha(chunk.get("fecha_documento", ""), req_id)
                if fecha is not None:
                    dias = (hoy - fecha).days
                    if dias > vigencia:
                        avisos.append("%s fechado %s tiene %d dias y supera la vigencia maxima del requisito (%d): "
                                      "verifique si la evidencia sigue vigente." % (chunk_id, fecha.isoformat(), dias, int(vigencia)))
        if (ev["estado"] == "CUBIERTO" and tipos_esperados and mapa_chunks is not None
                and tipos_citados and not (tipos_citados & set(tipos_esperados))):
            avisos.append("Veredicto CUBIERTO pero ningun documento citado es del tipo esperado %s (citados: %s): "
                          "confirme que la evidencia del tipo correcto existe o explique la equivalencia."
                          % (", ".join(tipos_esperados), ", ".join(sorted(tipos_citados))))
        if avisos:
            advertencias[req_id] = avisos

    if errores:
        sys.exit("ERRORES de citacion en evaluacion.csv:\n  - " + "\n  - ".join(errores))
    return advertencias


def construir_resultados(evaluacion, requisitos_cfg, orden, advertencias):
    requisitos = requisitos_cfg["requisitos"]
    faltantes = sorted(set(requisitos) - set(evaluacion))
    if faltantes:
        sys.exit("evaluacion.csv no trae veredicto para: %s" % ", ".join(faltantes))
    sobrantes = sorted(set(evaluacion) - set(requisitos))
    if sobrantes:
        sys.exit("evaluacion.csv trae requisito_id que no existen en requisitos.json: %s" % ", ".join(sobrantes))

    resultados = []
    for req_id, req in requisitos.items():
        ev = evaluacion[req_id]
        criticidad = str(req["criticidad"]).strip().lower()
        prioridad = prioridad_atencion(criticidad, ev["estado"], requisitos_cfg["prioridad"], orden)
        resultados.append({
            "requisito_id": req_id, "nombre": req["nombre"], "clausula": req["clausula"],
            "descripcion": req["descripcion"], "tipo_evidencia_esperada": req["tipo_evidencia_esperada"],
            "criticidad": criticidad, "estado": ev["estado"],
            "evidencia_citada": ev["evidencia_citada"], "justificacion": ev["justificacion"],
            "prioridad_atencion": prioridad,
            "plazo_dias": plazo_dias(prioridad, orden) if prioridad else None,
            "advertencias": advertencias.get(req_id, []),
        })

    orden_estado = {"SIN_EVIDENCIA": 0, "PARCIAL": 1, "CUBIERTO": 2}
    por_criticidad = {nivel: i for i, nivel in enumerate(reversed(orden))}  # la mas critica primero
    resultados.sort(key=lambda r: (orden_estado[r["estado"]], por_criticidad[r["criticidad"]], r["requisito_id"]))
    return resultados


def documentos_no_citados(mapa_chunks, resultados):
    """Documentos del indice que ningun chunk citado pertenece a ellos. El mapa
    chunk_id->chunk es la fuente de verdad del id de documento (no se parte el
    chunk_id a mano). Devuelve None si no hay indice (validacion desactivada)."""
    if mapa_chunks is None:
        return None
    todos = sorted({c["id_documento"] for c in mapa_chunks.values()})
    citados = {mapa_chunks[ch]["id_documento"] for r in resultados for ch in r["evidencia_citada"] if ch in mapa_chunks}
    return [d for d in todos if d not in citados]


def cargar_plantilla():
    if os.path.exists(PLANTILLA_HALLAZGO):
        with open(PLANTILLA_HALLAZGO, encoding="utf-8") as f:
            return f.read()
    return None


def texto_acciones(r):
    plazo = r["plazo_dias"]
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


def imprimir_resumen(resultados, hallazgos, no_citados, citas_validadas):
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
    if not citas_validadas:
        print("ADVERTENCIA: no se paso --indice: las citas de evaluacion.csv NO fueron verificadas contra el indice.")
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

    con_avisos = [r for r in resultados if r["advertencias"]]
    if con_avisos:
        print("-" * 92)
        print("ADVERTENCIAS (informativas, no cambian el veredicto — revisar manualmente):")
        for r in con_avisos:
            for aviso in r["advertencias"]:
                print("  [%s] %s" % (r["requisito_id"], aviso))


def main():
    ap = argparse.ArgumentParser(description="Formatea la evaluacion de cumplimiento (hecha por el modelo) en matriz y hallazgos.")
    ap.add_argument("--evaluacion", required=True, help="CSV con el veredicto por requisito, escrito por el modelo")
    ap.add_argument("--requisitos", default=REQUISITOS_POR_DEFECTO, help="JSON de requisitos (por defecto: requisitos.json del skill)")
    ap.add_argument("--indice", default=None, help="indice_chunks.json: verifica las citas, reporta documentos no citados")
    ap.add_argument("--salida", default="salida", help="carpeta donde se escriben resumen.json y hallazgos")
    ap.add_argument("--fecha-revision", default=None, help="fecha de referencia para el control de vigencia (yyyy-mm-dd; por defecto hoy)")
    ap.add_argument("--sin-revision-vigencia", action="store_true", help="desactiva las advertencias por evidencia vencida")
    args = ap.parse_args()

    requisitos_cfg = cargar_json(args.requisitos, "requisitos.json")
    orden = validar_config_requisitos(requisitos_cfg)
    evaluacion = cargar_evaluacion(args.evaluacion)

    mapa_chunks = None
    if args.indice:
        if not os.path.exists(args.indice):
            sys.exit("No se pudo leer el indice '%s': no existe." % args.indice)
        indice = cargar_json(args.indice, "el indice")
        if "chunks" not in indice:
            sys.exit("El indice '%s' no tiene la clave 'chunks' (debio escribirlo indexar_documentos.py)." % args.indice)
        mapa_chunks = {c["chunk_id"]: c for c in indice["chunks"]}

    if args.fecha_revision:
        fecha = parsear_fecha(args.fecha_revision, "--fecha-revision")
        if fecha is None:
            sys.exit("--fecha-revision debe tener formato yyyy-mm-dd o dd/mm/aaaa.")
        hoy = fecha
    else:
        hoy = datetime.now().date()

    advertencias = validar_citas_y_advertir(evaluacion, requisitos_cfg, mapa_chunks,
                                           None if args.sin_revision_vigencia else hoy)
    resultados = construir_resultados(evaluacion, requisitos_cfg, orden, advertencias)
    no_citados = documentos_no_citados(mapa_chunks, resultados)

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
            "indice": os.path.basename(args.indice) if args.indice else None,
            "fecha_revision": hoy.isoformat(),
            "citas_validadas": mapa_chunks is not None,
            "requisitos_evaluados": len(resultados),
            "cubiertos": sum(1 for r in resultados if r["estado"] == "CUBIERTO"),
            "parciales": sum(1 for r in resultados if r["estado"] == "PARCIAL"),
            "sin_evidencia": sum(1 for r in resultados if r["estado"] == "SIN_EVIDENCIA"),
            "documentos_no_citados": no_citados,
            "resultados": resultados,
        }, fh, ensure_ascii=False, indent=2)

    imprimir_resumen(resultados, hallazgos, no_citados, mapa_chunks is not None)
    print("\nresumen.json escrito en %s" % os.path.relpath(args.salida))


if __name__ == "__main__":
    main()
