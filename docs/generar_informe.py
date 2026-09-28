# -*- coding: utf-8 -*-
"""
generar_informe.py
===============================================================================
Genera Informe_Entregable1_Grupo6.docx a partir de docx_builder.py y del
resultado real de la demo (entregable-1/demo/salida/resumen.json,
entregable-1/demo/documentos_empresa_demo.csv). No se edita el .docx a mano:
se edita este guion y se vuelve a ejecutar.

Requisito: python-docx, Pillow (para generar_figuras.py).

Uso:
    python generar_informe.py
===============================================================================
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ENTREGABLE1 = os.path.join(RAIZ, "entregable-1")
SKILL_DIR = os.path.join(RAIZ, ".claude", "skills", "verificador-cumplimiento-pims")
DEMO_DIR = os.path.join(ENTREGABLE1, "demo")
RESUMEN_DEMO = os.path.join(DEMO_DIR, "salida", "resumen.json")
FIGURAS = os.path.join(AQUI, "figuras")

sys.path.insert(0, r"C:\Users\jeanp\.claude\skills\informes-docx")
from docx_builder import Documento  # noqa: E402

ETIQUETAS_FIGURAS = ["arquitectura"]

# Documentos "trampa" de la demo que ilustran por que hay que leer el
# contenido y no confiar en el nombre/tipo del documento.
DOCUMENTOS_TRAMPA = [
    ("DOC-06", "Contrato con proveedor de nube", "REQ-12",
     "Vigente, define niveles de servicio, pero el propio texto dice que no incluye cláusula de confidencialidad ni de protección de datos."),
    ("DOC-04", "Manual de control de accesos", "REQ-07",
     "Exige contraseña robusta, pero el propio texto reconoce que no hay autenticación multifactor para datos sensibles."),
    ("DOC-01", "Política de privacidad", "REQ-05",
     "Declara los derechos ARCO de los titulares, pero no define el procedimiento operativo (plazos, forma de solicitud) para ejercerlos."),
    ("DOC-02", "Registro de Actividades de Tratamiento (RAT)", "REQ-03",
     "El propio registro reconoce que no incluye los convenios ni la plataforma de pagos de 2026: está desactualizado."),
    ("DOC-07", "Plan de capacitación en seguridad", "REQ-11",
     "Cubre contraseñas y phishing, pero el propio plan indica que no cubre protección de datos ni registra ejecución."),
]

PASOS = {
    # Figuras que serian captura de pantalla y no se pudieron tomar en esta
    # ejecucion (no hay una terminal grafica que capturar desde este entorno).
}

PROMPTS = {
    # El diagrama de arquitectura se genera con generar_figuras.py (Pillow),
    # no hace falta un prompt de imagen generativa.
}


def figura(doc, clave, leyenda, ruta=None):
    ruta = ruta or os.path.join(FIGURAS, "%s.png" % clave)
    if os.path.exists(ruta):
        doc.imagen(ruta, leyenda=leyenda, etiqueta=clave)
        return
    if clave in PASOS:
        doc.parrafo("[Figura pendiente — pasos para capturarla:]", rojo=True)
        doc.numerada(PASOS[clave], rojo=True)
    elif clave in PROMPTS:
        doc.parrafo("[Figura pendiente — prompt para generarla:]", rojo=True)
        doc.parrafo(PROMPTS[clave], rojo=True)
    else:
        doc.parrafo("[Falta la figura '%s']" % clave, rojo=True, centrado=True)


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    if not os.path.exists(RESUMEN_DEMO):
        sys.exit("No existe %s — ejecuta antes entregable-1/demo.ps1 (o demo.sh)." % RESUMEN_DEMO)

    resumen = cargar_json(RESUMEN_DEMO)
    requisitos_cfg = cargar_json(os.path.join(SKILL_DIR, "requisitos.json"))
    indice = cargar_json(os.path.join(DEMO_DIR, "indice_chunks.json"))
    n_documentos = indice["documentos_indexados"]
    n_chunks = len(indice["chunks"])

    doc = Documento(figuras=ETIQUETAS_FIGURAS)

    # ---------------------------------------------------------------- Portada
    doc.espacio(120)
    doc.titulo_portada("UNIVERSIDAD — AUDITORÍA DE SISTEMAS", negrita=False)
    doc.espacio(20)
    doc.titulo_portada("Trabajo de Investigación Formativa (TIF)")
    doc.espacio(40)
    doc.titulo_portada("**Agente de cumplimiento PIMS**", espacio_despues=10)
    doc.titulo_portada("Skill y asistente de IA para ISO/IEC 27701:2025, con RAG")
    doc.espacio(60)
    doc.titulo_portada("Entregable 1 — Skill funcional especializado")
    doc.espacio(80)
    doc.titulo_portada("Grupo 6")
    doc.salto_pagina()

    # ------------------------------------------------------------ Introducción
    doc.titulo(1, "1. Introducción")
    doc.parrafo(
        "Este informe documenta el primer entregable del TIF del curso Auditoría "
        "de Sistemas: un skill y un asistente de IA que soportan el Sistema de "
        "Gestión de Privacidad de la Información (PIMS) definido por "
        "**ISO/IEC 27701:2025**. El tema asignado al grupo es «Agente de "
        "cumplimiento PIMS»: dado el corpus documental de una organización, "
        "determinar qué requisitos del PIMS están respaldados por evidencia "
        "vigente y suficiente, y cuáles necesitan atención.")
    doc.parrafo(
        "El resultado no es un documento teórico sino una herramienta que se "
        "ejecuta: un skill de Claude Code (`verificador-cumplimiento-pims`) que "
        "indexa los documentos, recupera por **RAG** (retrieval-augmented "
        "generation) los fragmentos relevantes para cada requisito, y un "
        "asistente (`AuditorPIMS`) que **lee ese contenido** — no un campo "
        "declarado como \"vigente\" — para decidir, citando el texto, si cada "
        "requisito está cubierto. El respaldo normativo es ISO/IEC 27001:2022, "
        "27002:2022, 29100, ISO 19011 y la Ley N.° 29733 (Perú).")
    doc.titulo(2, "1.1 Estructura del entregable")
    doc.parrafo(
        "El enunciado del curso pide tres tareas: de prompt a skill, creación de "
        "skill, y construcción de asistente. Cada una se documenta en una "
        "sección de este informe y en un archivo `.md` independiente dentro de "
        "`entregable-1/`, para que este informe y la documentación de trabajo "
        "no se dupliquen.")
    doc.tabla([
        ["Tarea", "Resultado"],
        ["De Prompt a Skill", "Descomposición en recuperación determinista (RAG) + lectura y juicio del modelo (no determinista, a propósito)."],
        ["Creación de Skill", "Skill `verificador-cumplimiento-pims` (activación, estructura, 9 pasos)."],
        ["Construcción de Asistente", "Asistente `AuditorPIMS` (identidad, 9 instrucciones, conocimiento)."],
    ], anchos_cm=[5, 11])

    doc.salto_pagina()

    # ------------------------------------------------------ Tarea 1 (De Prompt)
    doc.titulo(1, "2. De Prompt a Skill: transformación de la tarea")
    doc.titulo(2, "2.1 El prompt de partida y por qué no basta")
    doc.parrafo(
        "Antes del skill, la tarea se resolvía con un prompt suelto: «Aquí "
        "tienes nuestras políticas, procedimientos y contratos. Revisa si eso "
        "alcanza para cumplir con la ISO 27701 y dime qué nos falta.» Un "
        "prompt así no fija contra qué checklist se compara, no cabe con "
        "decenas de documentos completos, y pide al modelo una decisión final "
        "que no le corresponde.")
    doc.titulo(2, "2.2 Un primer diseño que resultó insuficiente")
    doc.parrafo(
        "La primera versión de este skill pedía un inventario ya resumido, con "
        "un campo `estado` (vigente/vencida/borrador) declarado por la propia "
        "organización. Repetía el error del prompt original — confiar en lo "
        "que alguien dice sin mirar la evidencia real: un documento puede "
        "llamarse «procedimiento de incidentes de privacidad» sin mencionar "
        "datos personales, o una política puede declararse «vigente» sin "
        "incluir el procedimiento que el requisito exige. El rediseño hace que "
        "el modelo **lea el contenido real** de cada documento en vez de "
        "confiar en un campo declarado.")
    doc.titulo(2, "2.3 Descomposición de la tarea (versión con RAG)")
    doc.numerada([
        "**Corpus documental real, sin etiquetar.** Documentos con su "
        "contenido en párrafos (`id_documento, tipo, fecha_documento, "
        "responsable, ubicacion, contenido`), no un resumen ni una "
        "clasificación previa.",
        "**Conocimiento explícito.** El checklist de 15 requisitos en "
        "`requisitos.json`.",
        "**Recuperación (RAG), determinista pero aproximada.** Trocear los "
        "documentos, indexarlos y recuperar por coincidencia léxica (TF-IDF) "
        "los más relevantes para cada requisito.",
        "**Lectura y juicio, del modelo — el paso que decide.** Leer el "
        "contenido recuperado y decidir `CUBIERTO`/`PARCIAL`/`SIN_EVIDENCIA` "
        "citando la frase exacta. No es determinista a propósito: la "
        "suficiencia de un documento es un juicio, no un cálculo.",
        "**Salida estructurada.** Matriz, un hallazgo por requisito que "
        "necesita atención, y un tablero web con semáforos.",
    ])
    doc.titulo(2, "2.4 Los 15 requisitos del checklist")
    doc.parrafo(
        "Se eligieron 15 requisitos representativos de ISO/IEC 27701:2025 para "
        "una institución educativa controladora de datos de estudiantes, "
        "cubriendo tanto las cláusulas del sistema de gestión (5 a 10) como los "
        "controles del Anexo A (tablas A.1, A.2 y A.3):")

    filas_req = [["Requisito", "Nombre", "Cláusula / control 27701:2025", "Criticidad"]]
    for req_id, req in sorted(requisitos_cfg["requisitos"].items()):
        filas_req.append([req_id, req["nombre"], req["clausula"], req["criticidad"].upper()])
    doc.tabla(filas_req, anchos_cm=[2.2, 5.3, 6.5, 2.0])

    doc.salto_pagina()

    # ---------------------------------------------------------- Tarea 2 (Skill)
    doc.titulo(1, "3. Creación de Skill: activación, estructura y pasos")
    doc.titulo(2, "3.1 Activación")
    doc.parrafo(
        "Un skill de Claude Code se activa por su descripción, escrita en "
        "términos de lo que el usuario *dice*, no de lo que el skill *hace*:")
    doc.parrafo(
        "`name: verificador-cumplimiento-pims` — «Revisa el corpus documental "
        "de una organización real usando RAG y luego LEE esos fragmentos para "
        "decidir, con justificación citada, qué requisitos del PIMS están "
        "cubiertos, cuáles parcialmente y cuáles sin evidencia.»",
        sangria_izq=1.0)
    doc.tabla([
        ["El usuario dice…", "¿Se activa?"],
        ["Aquí están nuestras políticas y contratos, ¿cumplimos con la 27701?", "Sí"],
        ["¿Qué requisitos del PIMS nos faltan?", "Sí"],
        ["Genera el tablero de cumplimiento", "Sí (pasos 5–6)"],
        ["¿Qué exige el control A.3.25 de la 27701?", "No — responde el asistente con la base de conocimiento"],
    ], anchos_cm=[11, 5])

    doc.titulo(2, "3.2 Estructura y arquitectura")
    doc.imagen(os.path.join(FIGURAS, "arquitectura.png"),
               leyenda="Pipeline del skill: indexar → recuperar por RAG → el modelo lee y decide → formatear matriz y hallazgos → tablero → validación del DPO.",
               etiqueta="arquitectura")
    doc.parrafo(
        "`requisitos.json` separa el conocimiento del código y arma la consulta "
        "de cada requisito para la recuperación; `scripts/indexar_documentos.py` "
        "y `scripts/recuperar_fragmentos.py` implementan el RAG léxico (TF-IDF, "
        "solo librería estándar de Python, sin embeddings ni librerías "
        "externas); `scripts/generar_matriz_cumplimiento.py` y "
        "`scripts/generar_tablero.py` formatean el veredicto del modelo, sin "
        "decidir nada por su cuenta; `plantillas/hallazgo_cumplimiento.md` fija "
        "la salida con la forma de ISO 19011.")

    doc.titulo(2, "3.3 Dos problemas reales de RAG que encontramos al probarlo")
    doc.parrafo(
        "La primera versión recuperaba los 3 fragmentos sueltos con mayor "
        "puntaje, sin importar de qué documento venían. Eso perdía contexto: "
        "el párrafo que reconoce que un contrato «no incluye cláusula de "
        "confidencialidad» comparte menos palabras clave con la consulta que "
        "el párrafo introductorio del mismo contrato, así que no entraba en el "
        "top-3 y el hueco quedaba invisible. La solución fue recuperar por "
        "**documento completo** (rankear documentos por su mejor fragmento, "
        "devolver todos sus párrafos), para que el modelo siempre vea el "
        "documento entero, incluida la frase que revela el hueco.")
    doc.parrafo(
        "El segundo problema es estructural de TF-IDF: compara palabras, no "
        "significado. Si el requisito dice «consentimiento del titular» y un "
        "documento dice «autorización expresa del usuario», comparten cero "
        "palabras y el documento puede no recuperarse. Lo mitigamos con "
        "**expansión de consulta**: un glosario de ~16 grupos de equivalencias "
        "del dominio (consentimiento/autorización, titular/usuario, "
        "encargado/proveedor/tercero, multifactor/MFA…) que se suma a la "
        "consulta de cada requisito antes de calcular el TF-IDF — nunca a los "
        "documentos indexados, para que el efecto sea fácil de explicar y de "
        "desactivar (`--sin-sinonimos`) para comparar.")

    doc.titulo(2, "3.4 Los nueve pasos")
    doc.tabla([
        ["#", "Paso", "Quién lo hace"],
        ["1", "Ubicar el corpus (extraer texto si vienen PDFs sueltos)", "Modelo"],
        ["2", "Indexar en fragmentos (`indexar_documentos.py`)", "Script (determinista)"],
        ["3", "Recuperar por RAG (`recuperar_fragmentos.py`)", "Script (determinista, aproximado)"],
        ["4", "Leer los fragmentos y evaluar, citando el texto", "Modelo (no determinista)"],
        ["5", "Formatear matriz y hallazgos (`generar_matriz_cumplimiento.py`)", "Script (determinista)"],
        ["6", "Generar el tablero (`generar_tablero.py`)", "Script (determinista)"],
        ["7", "Interpretar para el usuario, por prioridad", "Modelo"],
        ["8", "Justificar con `conocimiento/iso27701.md`", "Modelo"],
        ["9", "Releer si el usuario corrige un documento", "Modelo"],
    ], anchos_cm=[1.2, 9.3, 5.5])

    doc.salto_pagina()

    # ----------------------------------------------------- Tarea 3 (Asistente)
    doc.titulo(1, "4. Construcción de Asistente: identidad, instrucciones, conocimiento")
    doc.titulo(2, "4.1 Identidad")
    doc.parrafo(
        "**AuditorPIMS** apoya al Oficial de Protección de Datos (DPO) y al "
        "equipo responsable del PIMS de una institución educativa. Su "
        "especialidad es verificar cumplimiento **leyendo evidencia real**, no "
        "metadatos declarados. Su tono es «primero el hecho, luego la cita "
        "textual, luego la norma, luego la recomendación».")
    doc.titulo(2, "4.2 Instrucciones (resumen)")
    doc.vinetas([
        "Con el corpus documental, indexar y recuperar por RAG.",
        "Leer cada fragmento recuperado y decidir citando el texto exacto; no "
        "fiarse del nombre o tipo del documento.",
        "Formatear la matriz, generar el tablero y presentarlos por prioridad.",
        "Justificar cada requisito citando `conocimiento/iso27701.md`.",
        "Completar hallazgos solo en la sección de seguimiento.",
        "Ante un documento nuevo o corregido, releer antes de cambiar un "
        "veredicto.",
        "Ajustar el checklist solo en copia, con confirmación del usuario.",
        "Minimización: citar el fragmento relevante, no el documento completo.",
        "No decidir si el PIMS está listo para certificación: esa decisión es "
        "del DPO y de la auditoría interna formal.",
    ])
    doc.titulo(2, "4.3 Conocimiento")
    doc.parrafo(
        "El asistente no lleva conocimiento en el prompt: apunta a "
        "`conocimiento/iso27701.md`, `requisitos.json` y `plantillas/"
        "hallazgo_cumplimiento.md`, que puede leer cuando los necesita. Esto "
        "mantiene el prompt corto y permite actualizar la base normativa sin "
        "reescribir al asistente.")

    doc.salto_pagina()

    # -------------------------------------------------------------- Demostración
    doc.titulo(1, "5. Demostración")
    doc.parrafo(
        "Se generó un corpus documental sintético y reproducible "
        "(`scripts/generar_documentos_empresa_demo.py`): %d documentos con "
        "contenido real, indexados en %d fragmentos. Se recuperaron por RAG "
        "los fragmentos relevantes para cada uno de los 15 requisitos y se "
        "aplicó una evaluación de referencia (la lectura que ya hizo el "
        "asistente sobre ese contenido, guardada para que la demo sea "
        "reproducible)." % (n_documentos, n_chunks))

    doc.titulo(2, "5.1 Huecos intencionales dentro de documentos reales")
    doc.parrafo(
        "Siguiendo la recomendación de la cátedra, los huecos de la demo no "
        "son documentos enteros ausentes o mal etiquetados, sino **carencias "
        "específicas dentro de documentos por lo demás sustanciales** — el "
        "patrón que hace que la demo sea convincente:")
    filas_trampa = [["Documento", "Requisito", "Qué falta, según el propio texto"]]
    for doc_id, nombre, req, motivo in DOCUMENTOS_TRAMPA:
        filas_trampa.append(["%s — %s" % (doc_id, nombre), req, motivo])
    doc.tabla(filas_trampa, anchos_cm=[4.5, 2.0, 9.5])

    doc.titulo(2, "5.2 Resultado de la evaluación")
    doc.tabla([
        ["Documentos analizados", str(n_documentos)],
        ["Fragmentos indexados", str(n_chunks)],
        ["Requisitos evaluados", str(resumen["requisitos_evaluados"])],
        ["Cubiertos", str(resumen["cubiertos"])],
        ["Parciales", str(resumen["parciales"])],
        ["Sin evidencia", str(resumen["sin_evidencia"])],
        ["Documentos no citados por ningún requisito", ", ".join(resumen.get("documentos_no_citados") or []) or "ninguno"],
    ], anchos_cm=[9, 7], encabezado=False)

    doc.titulo(2, "5.3 Matriz de cumplimiento")
    filas_matriz = [["Requisito", "Nombre", "Estado", "Prioridad", "Evidencia citada"]]
    for r in resumen["resultados"]:
        filas_matriz.append([
            r["requisito_id"], r["nombre"], r["estado"].replace("_", " "),
            (r["prioridad_atencion"] or "-").upper() if r["prioridad_atencion"] else "-",
            ", ".join(r["evidencia_citada"]) if r["evidencia_citada"] else "—",
        ])
    doc.tabla(filas_matriz, anchos_cm=[2.0, 5.3, 3.0, 2.2, 3.5])

    doc.titulo(2, "5.4 Ejemplo de hallazgo (con cita textual)")
    hallazgo_ejemplo = next((r for r in resumen["resultados"] if r["requisito_id"] == "REQ-12"), resumen["resultados"][0])
    doc.parrafo(
        "El requisito **%s — %s** quedó `%s` (prioridad %s). Cita textual del "
        "documento (%s): «%s»"
        % (hallazgo_ejemplo["requisito_id"], hallazgo_ejemplo["nombre"],
           hallazgo_ejemplo["estado"].replace("_", " "),
           (hallazgo_ejemplo["prioridad_atencion"] or "-").upper(),
           ", ".join(hallazgo_ejemplo["evidencia_citada"]),
           hallazgo_ejemplo["justificacion"]))
    doc.parrafo(
        "El skill genera para este requisito el archivo `hallazgo_%s.md`, con "
        "la forma de ISO 19011: criterio (qué exige el requisito), la cita "
        "textual que sustenta el veredicto, la brecha, acciones recomendadas "
        "con plazo según la prioridad, y una sección de seguimiento para que "
        "el DPO la complete." % hallazgo_ejemplo["requisito_id"])

    doc.titulo(1, "6. Conclusiones")
    doc.vinetas([
        "El skill separa lo que es aritmética determinista y reproducible "
        "(indexar, recuperar por TF-IDF, calcular prioridad, dar formato) de "
        "lo que exige entender lenguaje natural (leer un documento y juzgar si "
        "realmente satisface un requisito) — y deja lo segundo, a propósito, "
        "en manos del modelo, con la exigencia de citar el texto para que sea "
        "verificable.",
        "Los %d documentos del corpus produjeron, tras la recuperación por RAG "
        "y la lectura del modelo, %d requisitos cubiertos, %d parciales y %d "
        "sin evidencia — %d hallazgos, con 5 de los parciales revelando un "
        "hueco que un chequeo superficial (por nombre o tipo de documento) no "
        "habría detectado." % (
            n_documentos, resumen["cubiertos"], resumen["parciales"],
            resumen["sin_evidencia"], resumen["parciales"] + resumen["sin_evidencia"]),
        "El tablero web con semáforos (verde/amarillo/rojo), generado con "
        "solo la librería estándar de Python (HTML/CSS planos, sin "
        "frameworks), da una lectura rápida del estado del PIMS sin abrir "
        "cada hallazgo.",
        "Queda pendiente para el entregable 2 el diseño de agente (objetivo, "
        "datos, contexto, herramientas) y la orquestación con otros skills.",
    ])

    ruta_salida = os.path.join(ENTREGABLE1, "Informe_Entregable1_Grupo6.docx")
    doc.guardar(ruta_salida)
    print("Informe escrito en %s" % ruta_salida)


if __name__ == "__main__":
    main()
