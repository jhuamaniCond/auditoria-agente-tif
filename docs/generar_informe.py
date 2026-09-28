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
        "skill, y construcción de asistente. Cada una se desarrolla en una "
        "sección de este informe (secciones 2, 3 y 4), seguida de la "
        "demostración sobre un corpus documental (sección 5).")
    doc.tabla([
        ["Tarea", "Resultado"],
        ["De Prompt a Skill", "Descomposición en recuperación determinista (RAG) + lectura y juicio del modelo (no determinista, a propósito)."],
        ["Creación de Skill", "Skill `verificador-cumplimiento-pims` (activación, estructura, 9 pasos)."],
        ["Construcción de Asistente", "Asistente `AuditorPIMS` (identidad, 9 instrucciones, conocimiento)."],
    ], anchos_cm=[5, 11])

    doc.salto_pagina()

    # ------------------------------------------------------ Tarea 1 (De Prompt)
    doc.titulo(1, "2. De Prompt a Skill: transformación de la tarea")
    doc.titulo(2, "2.1 El prompt de partida")
    doc.parrafo(
        "Sin un skill, la tarea se resuelve con un prompt suelto, escrito cada "
        "vez que hace falta:")
    doc.parrafo(
        "«Aquí tienes nuestras políticas, procedimientos y contratos. Revisa si "
        "eso alcanza para cumplir con la ISO 27701 y dime qué nos falta.»",
        sangria_izq=1.0)
    doc.titulo(2, "2.2 Por qué ese prompt no sirve como proceso")
    doc.tabla([
        ["Problema del prompt", "Consecuencia"],
        ["No dice contra qué checklist se compara.",
         "El modelo inventa o adapta de memoria qué requisitos existen, sin fijar cuántos ni cuáles."],
        ["Con decenas de documentos completos, el prompt no cabe o cuesta caro en cada consulta.",
         "No es viable repetir la evaluación cada vez que cambia un documento."],
        ["No fija cómo decidir «cumple»: ¿basta con que el documento exista? ¿con que el nombre coincida?",
         "Dos ejecuciones pueden llegar a conclusiones distintas sin que quede registro de por qué."],
        ["No fija la salida.",
         "A veces devuelve una lista, a veces un párrafo; nada que se pueda archivar como papel de trabajo de auditoría."],
        ["«Dime qué nos falta» pide una decisión final que no le corresponde a la herramienta.",
         "Se salta el proceso de auditoría interna (§9.2): la evaluación definitiva la hace el Oficial de Protección de Datos."],
        ["No es repetible ni verificable.",
         "No hay forma de demostrar a un auditor externo cómo se llegó a la conclusión de «cubierto» o «falta»."],
    ], anchos_cm=[7.5, 8.5])
    doc.parrafo(
        "Hay además un riesgo de fondo: confiar en lo que la organización "
        "declara sin mirar la evidencia real. Un documento puede llamarse "
        "«procedimiento de respuesta a incidentes de privacidad» y no mencionar "
        "datos personales en ningún párrafo; una política puede figurar como "
        "«vigente» y no incluir el procedimiento que el requisito exige. Por eso "
        "el skill hace que el modelo **lea el contenido real** de cada "
        "documento, en lugar de apoyarse en su nombre, tipo o estado declarado.")
    doc.titulo(2, "2.3 Descomposición de la tarea")
    doc.numerada([
        "**Corpus documental real, sin etiquetar.** Los documentos de la "
        "organización (`id_documento, tipo, fecha_documento, responsable, "
        "ubicacion, contenido`), con el contenido real en párrafos, no un "
        "resumen ni una clasificación previa.",
        "**Conocimiento explícito.** El checklist de 15 requisitos del PIMS "
        "(`requisitos.json`): qué exige cada uno y qué evidencia lo "
        "satisfaría.",
        "**Recuperación (RAG), determinista.** Trocear los documentos e "
        "indexar los fragmentos; para cada requisito, recuperar por "
        "coincidencia léxica (TF-IDF) los documentos más relevantes. Es "
        "mecánico y reproducible, pero aproximado: puede traer un documento "
        "irrelevante o dejar fuera uno relevante con vocabulario distinto.",
        "**Lectura y juicio, del modelo — el paso que decide.** Leer el "
        "contenido de los fragmentos recuperados y decidir si cada requisito "
        "está `CUBIERTO`, `PARCIAL` (hay algo, pero el propio texto revela un "
        "hueco) o `SIN_EVIDENCIA`, citando la frase exacta que sustenta el "
        "veredicto. No es determinista a propósito: la calidad y suficiencia "
        "de un documento es un juicio, no un cálculo, y forzarlo a ser "
        "determinista ocultaría justamente los huecos reales.",
        "**Salida estructurada.** `resumen.json` (matriz completa), un "
        "`hallazgo_<REQ-ID>.md` por requisito que necesita atención, y un "
        "tablero web con semáforos (verde/amarillo/rojo) para una lectura "
        "rápida.",
    ])
    doc.titulo(2, "2.4 Criterios para decidir qué va al skill y qué queda en el prompt")
    doc.vinetas([
        "Si algo debe ser **igual en todas las ejecuciones** (los 15 "
        "requisitos, la forma de indexar y recuperar, el formato del hallazgo "
        "y del tablero), va al skill, en scripts deterministas.",
        "Si algo requiere **entender el contenido de un documento en lenguaje "
        "natural** (¿esta cláusula alcanza?, ¿este procedimiento es operativo "
        "o solo declarativo?), es tarea del modelo, documentada como tal en el "
        "`SKILL.md`, con la exigencia de citar la evidencia textual para que "
        "sea revisable.",
        "Si algo es una **decisión de la organización** (¿el PIMS está listo "
        "para certificación?), no va a ninguno de los dos; se deja como "
        "pendiente en la sección de seguimiento del hallazgo.",
    ])
    doc.titulo(2, "2.5 El prompt, después")
    doc.parrafo(
        "Lo que era un párrafo ambiguo se convierte en una invocación:")
    doc.parrafo(
        "«Evalúa el cumplimiento del PIMS con nuestros documentos "
        "(`documentos_empresa_demo.csv`).»", sangria_izq=1.0)
    doc.parrafo(
        "El skill sabe qué checklist aplicar, cómo recuperar lo relevante de "
        "cada documento y qué archivos producir. Lo que sigue dependiendo del "
        "criterio del modelo — y así queda documentado, no oculto — es la "
        "lectura de si el contenido realmente cumple.")
    doc.titulo(2, "2.6 Los 15 requisitos del checklist")
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
    doc.parrafo(
        "El skill está implementado en `.claude/skills/verificador-cumplimiento-pims/` "
        "con el formato de skills de Claude Code: una carpeta con `SKILL.md` "
        "más los archivos que el skill necesita. Esta sección explica las tres "
        "decisiones de diseño que pide la tarea.")
    doc.titulo(2, "3.1 Activación")
    doc.parrafo(
        "Un skill se activa por su **descripción**: el asistente la lee en cada "
        "turno y decide si la tarea del usuario encaja. Por eso la descripción "
        "está escrita en términos de lo que el usuario *dice*, no de lo que el "
        "skill *hace*:")
    doc.parrafo(
        "`name: verificador-cumplimiento-pims` — «Revisa el corpus documental "
        "de una organización real (políticas, procedimientos, registros, "
        "contratos, capacitaciones — sin etiquetar contra la norma) usando RAG "
        "(indexa los documentos, recupera los fragmentos más relevantes por "
        "requisito) y luego LEE esos fragmentos para decidir, con "
        "justificación citada, qué requisitos del PIMS están cubiertos, cuáles "
        "parcialmente y cuáles sin evidencia, generando un hallazgo por cada "
        "brecha y un tablero web con semáforos.»",
        sangria_izq=1.0)
    doc.parrafo("Disparadores cubiertos (frases reales que usaría un auditor):")
    doc.tabla([
        ["El usuario dice…", "¿Se activa?"],
        ["Aquí están nuestras políticas y contratos, ¿cumplimos con la 27701?", "Sí"],
        ["¿Qué requisitos del PIMS nos faltan?", "Sí"],
        ["Genera el tablero de cumplimiento", "Sí (pasos 5–6)"],
        ["¿Qué exige el control A.3.25 de la 27701?", "No — responde el asistente con la base de conocimiento, sin ejecutar el pipeline"],
        ["Revisa estos logs de acceso a fichas de estudiantes", "No — son registros de actividad, no evidencia documental de cumplimiento"],
    ], anchos_cm=[9, 7])
    doc.parrafo(
        "También se puede invocar de forma explícita con "
        "`/verificador-cumplimiento-pims`.")

    doc.titulo(2, "3.2 Estructura")
    doc.tabla([
        ["Archivo", "Propósito"],
        ["`SKILL.md`", "Activación, formato de entrada, pasos y límites."],
        ["`requisitos.json`", "Conocimiento parametrizable: 15 requisitos, evidencia esperada, vigencia y criticidad."],
        ["`scripts/indexar_documentos.py`", "RAG, paso 1: trocea los documentos en fragmentos (chunks)."],
        ["`scripts/recuperar_fragmentos.py`", "RAG, paso 2: TF-IDF léxico, recupera por documento completo."],
        ["`scripts/generar_matriz_cumplimiento.py`", "Formatea el veredicto del modelo en matriz + hallazgos, valida citas y vigencia."],
        ["`scripts/generar_tablero.py`", "Tablero web con semáforos (HTML/CSS planos)."],
        ["`scripts/servir_tablero.py`", "Sirve el tablero como aplicación web local (`http.server`)."],
        ["`scripts/generar_documentos_empresa_demo.py`", "Corpus documental sintético para la demo."],
        ["`scripts/generar_evaluacion_demo.py`", "Veredicto de referencia (lectura ya hecha) para la demo."],
        ["`plantillas/hallazgo_cumplimiento.md`", "Formato del hallazgo con marcadores {{campo}}."],
        ["`conocimiento/iso27701.md`", "15 requisitos → controles 27701:2025/27002:2022, normas relacionadas y proceso de auditoría."],
    ], anchos_cm=[7, 9])
    doc.parrafo("Por qué está separado así:")
    doc.vinetas([
        "**`SKILL.md` es corto y solo tiene proceso.** Nada de código ni de "
        "teoría.",
        "**`requisitos.json` separa el conocimiento del código.** También arma "
        "la consulta de cada requisito para la recuperación RAG (su nombre, "
        "descripción y tipo de evidencia esperada).",
        "**`scripts/` solo hace lo mecánico y reproducible: indexar, "
        "recuperar, formatear y publicar.** Ningún script decide si un "
        "requisito está cubierto — eso exige entender lenguaje natural y, por "
        "diseño, no está en el código (sección 2.3). Todos usan solo librería "
        "estándar de Python (>= 3.8): `re`, `math`, `csv`, `json`, "
        "`unicodedata`, `http.server`; sin embeddings ni librerías externas.",
        "**`plantillas/` fija la salida.** El hallazgo tiene siempre las mismas "
        "secciones (criterio, evidencia, hallazgo, conclusión, seguimiento), "
        "con la forma de ISO 19011.",
        "**`conocimiento/` es lo que consulta el modelo para explicar** la "
        "norma detrás de cada hallazgo.",
    ])

    doc.titulo(2, "3.3 Definición de pasos")
    doc.parrafo(
        "Los nueve pasos del `SKILL.md`, quién los ejecuta y qué problema "
        "resuelve cada uno:")
    doc.tabla([
        ["#", "Paso", "Quién lo hace", "Qué evita"],
        ["1", "Ubicar el corpus (convertir a CSV si vienen PDFs sueltos)", "Modelo", "Trabajar sobre datos sin extraer"],
        ["2", "Indexar (`indexar_documentos.py`)", "Script (determinista)", "Perder la trazabilidad de qué párrafo viene de qué documento"],
        ["3", "Recuperar por RAG (`recuperar_fragmentos.py`)", "Script (determinista, aproximado)", "Que el modelo tenga que leer el corpus completo por cada requisito"],
        ["4", "**Leer los fragmentos y evaluar** (`evaluacion.csv`)", "**Modelo (no determinista)**", "Confiar en el nombre o tipo del documento sin leer si el contenido realmente cumple"],
        ["5", "Formatear matriz y hallazgos (`generar_matriz_cumplimiento.py`)", "Script (determinista)", "Hallazgos con formato inconsistente"],
        ["6", "Generar el tablero (`generar_tablero.py`)", "Script (determinista)", "Tener que leer JSON para ver el estado general"],
        ["7", "Interpretar para el usuario, por prioridad", "Modelo", "Respuestas desordenadas o veredictos anticipados"],
        ["8", "Justificar con `conocimiento/iso27701.md`", "Modelo", "Inventar números de cláusula"],
        ["9", "Releer si el usuario corrige un documento", "Modelo", "Asumir que un documento nuevo corrige el hueco sin leerlo"],
    ], anchos_cm=[0.8, 6.0, 3.7, 5.5])

    doc.titulo(2, "3.4 Flujo completo")
    doc.parrafo("La %s muestra el pipeline de extremo a extremo; cada paso produce un archivo que consume el siguiente:" % doc.fig("arquitectura"))
    doc.imagen(os.path.join(FIGURAS, "arquitectura.png"),
               leyenda="Pipeline del skill: indexar → recuperar por RAG → el modelo lee y decide → formatear matriz y hallazgos → tablero → validación del DPO.",
               etiqueta="arquitectura")
    doc.tabla([
        ["Paso", "Entrada", "Salida"],
        ["2 — `indexar_documentos.py` (determinista)", "`documentos_empresa_demo.csv` (contenido real, sin etiquetar)", "`indice_chunks.json` (%d fragmentos de %d documentos)" % (n_chunks, n_documentos)],
        ["3 — `recuperar_fragmentos.py` (determinista, TF-IDF, aproximado)", "`indice_chunks.json` + `requisitos.json`", "`fragmentos_recuperados.json` (hasta 4 documentos por requisito)"],
        ["4 — el modelo lee el contenido y decide (no determinista)", "`fragmentos_recuperados.json`", "`evaluacion.csv` (CUBIERTO / PARCIAL / SIN_EVIDENCIA + cita textual)"],
        ["5 — `generar_matriz_cumplimiento.py` (determinista)", "`evaluacion.csv` + `requisitos.json` + índice", "`resumen.json` + `hallazgo_<REQ-ID>.md` + documentos no citados"],
        ["6 — `generar_tablero.py` (determinista)", "`resumen.json`", "`tablero.html` (semáforo verde/amarillo/rojo)"],
    ], anchos_cm=[5.5, 5.0, 5.5])

    doc.titulo(2, "3.5 Decisiones de diseño de la recuperación")
    doc.parrafo(
        "**Recuperación por documento completo.** El recuperador rankea los "
        "documentos por su mejor fragmento y devuelve todos los párrafos de "
        "cada documento seleccionado, no fragmentos sueltos. La razón: el "
        "párrafo que revela un hueco suele compartir pocas palabras con la "
        "consulta. En el contrato con el proveedor de nube, el párrafo que "
        "reconoce que «no incluye cláusula de confidencialidad» puntúa menos "
        "que el párrafo introductorio del mismo contrato; si se recuperaran "
        "solo los fragmentos de mayor puntaje, ese párrafo quedaría fuera y el "
        "hueco sería invisible. Al recibir el documento entero, el modelo "
        "siempre ve la frase que revela la carencia, en su contexto.")
    doc.parrafo(
        "**Expansión de consulta con sinónimos del dominio.** TF-IDF compara "
        "palabras, no significado: si el requisito dice «consentimiento del "
        "titular» y un documento dice «autorización expresa del usuario», "
        "comparten cero palabras y el documento podría no recuperarse aunque "
        "sea justo la evidencia que hace falta. El skill lo mitiga con un "
        "glosario de ~16 grupos de equivalencias (`GRUPOS_SINONIMOS` en "
        "`recuperar_fragmentos.py`: consentimiento/autorización, "
        "titular/usuario/interesado, encargado/proveedor/tercero, "
        "brecha/incidente, multifactor/MFA, etc.) que se suma a la consulta de "
        "cada requisito antes de calcular el TF-IDF. Es la misma idea que usa "
        "un auditor cuando entiende que el lenguaje de la norma no siempre es "
        "el lenguaje de la empresa. Dos reglas, siguiendo la práctica estándar "
        "de esta técnica:")
    doc.vinetas([
        "**Se expande solo la consulta, nunca los documentos indexados**: el "
        "índice queda intacto, el efecto es fácil de explicar y se puede "
        "desactivar con `--sin-sinonimos` para comparar con y sin glosario.",
        "**Grupos pequeños y específicos del dominio**, no palabras genéricas: "
        "con el corpus de la demo, el glosario cambia qué documentos se "
        "recuperan en 4 de los 15 requisitos, sin alterar el veredicto final "
        "(los 5 casos `PARCIAL` se recuperan igual con o sin sinónimos, porque "
        "ya comparten vocabulario suficiente con la consulta).",
    ])

    doc.titulo(2, "3.6 Reglas de calidad")
    doc.vinetas([
        "Solo librería estándar de Python en todos los scripts.",
        "Los scripts nunca escriben dentro de la carpeta del skill, y el "
        "corpus de entrada nunca se modifica.",
        "`evaluacion.csv` exige una fila por cada uno de los 15 requisitos "
        "(`generar_matriz_cumplimiento.py` falla si falta alguno) y cita el "
        "`chunk_id` exacto, para que cualquier hallazgo sea verificable "
        "releyendo el fragmento. El script lo hace cumplir: si un `chunk_id` "
        "citado no existe en el índice, o un veredicto CUBIERTO/PARCIAL no cita "
        "ningún fragmento, la matriz no se genera y el error indica qué fila "
        "corregir.",
        "Control de vigencia (`vigencia_max_dias` de `requisitos.json`): la "
        "matriz advierte, sin alterar el veredicto del modelo, cuando la fecha "
        "de un documento citado supera la vigencia máxima del requisito, y "
        "cuando un CUBIERTO no cita ningún tipo de evidencia esperada.",
        "Los documentos del corpus que ningún requisito citó como evidencia se "
        "reportan aparte (no se descartan en silencio): pueden ser "
        "irrelevantes o evidencia que el modelo pasó por alto.",
        "El generador de demo produce siempre el mismo corpus de %d "
        "documentos: el jurado puede regenerarlo y obtener la misma "
        "recuperación." % n_documentos,
        "`python -m unittest discover -s tests` ejecuta 24 pruebas (solo "
        "librería estándar) que cubren el troceo con saltos de línea CRLF y "
        "BOM, errores claros de entrada, validación de citas, vigencia, "
        "prioridad parametrizable y la demo completa de extremo a extremo.",
    ])

    doc.titulo(2, "3.7 Verificación realizada")
    doc.parrafo(
        "Ejecución del pipeline completo sobre el corpus de la demo, con la "
        "salida real de cada script:")
    doc.tabla([
        ["Script", "Salida"],
        ["`generar_documentos_empresa_demo.py`", "11 documentos escritos (2 de ellos, DOC-10 y DOC-11, no tratan protección de datos personales)"],
        ["`indexar_documentos.py`", "11 documentos → 29 fragmentos indexados"],
        ["`recuperar_fragmentos.py`", "Fragmentos recuperados para 15 requisitos (top-4, umbral 0.08)"],
        ["`generar_evaluacion_demo.py`", "Evaluación de referencia (15 requisitos) escrita"],
        ["`generar_matriz_cumplimiento.py` (`--fecha-revision 2026-07-01`)", "15 evaluados: 7 cubiertos, 5 parciales, 3 sin evidencia, 8 hallazgos; documentos no citados: DOC-10, DOC-11; las 21 citas de `chunk_id` existen en el índice"],
    ], anchos_cm=[6.5, 9.5])

    doc.titulo(2, "3.8 Calidad de la recuperación: recall y precisión")
    doc.parrafo(
        "Se midió la recuperación léxica de la demo contra un *ground truth* "
        "de referencia: el documento (o documentos) que realmente trata cada "
        "requisito, obtenido de las citas de `evaluacion_demo.csv` y "
        "verificado a mano.")
    doc.tabla([
        ["Métrica", "Valor", "Lectura"],
        ["Recall (12 requisitos con documento relevante en el corpus)", "100% (12/12)",
         "El documento que hace falta nunca se pierde: siempre está entre los hasta 4 documentos recuperados por el requisito."],
        ["Precisión (documentos recuperados que son relevantes)", "29% (12/42)",
         "Se recupera ruido a propósito: léxico + sinónimos trae documentos que comparten palabras sueltas."],
        ["Requisitos sin documento relevante (REQ-02, REQ-08, REQ-13)", "3",
         "La recuperación trajo 12 documentos irrelevantes en total; la lectura del modelo los descartó y el veredicto fue `SIN_EVIDENCIA` correcto en los 3."],
    ], anchos_cm=[5.5, 2.5, 8.0])
    doc.parrafo(
        "Es el intercambio deliberado de este diseño: el paso determinista "
        "(TF-IDF) prioriza **no perder evidencia** (recall alto) y el paso no "
        "determinista (lectura del modelo) filtra el ruido (precisión baja "
        "tolerada). Recuperar de más cuesta solo unos párrafos extra de "
        "lectura; recuperar de menos ocultaría una brecha real. El tablero y "
        "`resumen.json` dejan además constancia de los documentos que nadie "
        "citó (DOC-10, DOC-11) para que se revisen a mano.")

    doc.salto_pagina()

    # ----------------------------------------------------- Tarea 3 (Asistente)
    doc.titulo(1, "4. Construcción de Asistente: identidad, instrucciones, conocimiento")
    doc.parrafo(
        "El asistente está definido en `.claude/agents/auditor-cumplimiento-pims.md`. "
        "Claude Code guarda estas definiciones en la carpeta `agents/`, pero "
        "aquí solo se usa para lo que pide esta tarea: identidad, "
        "instrucciones y conocimiento; el diseño de agente (objetivo, datos, "
        "contexto, herramientas) y la orquestación corresponden al segundo "
        "entregable. AuditorPIMS es quien *usa* el skill: el skill indexa, "
        "recupera y da formato; el asistente **lee y decide**, y sabe a quién "
        "le habla, qué puede decidir y qué no.")
    doc.titulo(2, "4.1 Identidad")
    doc.tabla([
        ["Elemento", "Decisión", "Razón"],
        ["Nombre", "**AuditorPIMS**", "Deja claro el rol (auditor) y el objeto (el sistema de gestión de privacidad, PIMS)."],
        ["A quién sirve", "Oficial de Protección de Datos (DPO) y equipo responsable del PIMS de una institución educativa",
         "Es el usuario real de la función de auditoría interna (§9.2); define el nivel técnico de las respuestas."],
        ["Especialidad", "Verificación de cumplimiento **leyendo evidencia real** (no metadatos declarados), con las normas que la respaldan (27001, 27002, 29100, 27005, 19011, Ley 29733)",
         "Acota el alcance y deja explícito que la decisión exige leer, no solo consultar un campo."],
        ["Tono", "Profesional, directo: «primero el hecho, luego la cita textual, luego la norma, luego la recomendación»",
         "Es el orden en que un auditor presenta un hallazgo verificable."],
        ["Idioma", "Español", "El de la organización y de los documentos."],
    ], anchos_cm=[2.8, 7.0, 6.2])
    doc.titulo(2, "4.2 Instrucciones")
    doc.parrafo(
        "Las nueve instrucciones del prompt de sistema, y qué comportamiento "
        "fija cada una:")
    doc.tabla([
        ["#", "Instrucción", "Comportamiento que garantiza"],
        ["1", "Con el corpus documental, indexar y recuperar por RAG (pasos 2–3 del skill)", "No lee el corpus completo para cada requisito; usa la recuperación como primer filtro"],
        ["2", "Leer cada fragmento recuperado y decidir citando el texto exacto", "No se fía del nombre o tipo del documento; el veredicto queda verificable"],
        ["3", "Formatear la matriz, generar el tablero y presentarlos por prioridad", "Salida uniforme; hallazgos siempre ordenados por urgencia"],
        ["4", "Explicar requisitos y controles citando `conocimiento/iso27701.md`", "Trazabilidad de cada afirmación normativa"],
        ["5", "Completar hallazgos solo en la sección de seguimiento", "No altera la evidencia citada; separa lo detectado de lo decidido"],
        ["6", "Ante un documento nuevo o corregido, releer antes de cambiar el veredicto", "Nunca asume que algo se corrigió sin leer el texto corregido"],
        ["7", "Ajustar el checklist solo en copia, con confirmación", "Los requisitos del PIMS no cambian por accidente"],
        ["8", "Minimización: citar el fragmento relevante, no el documento completo", "Cumple el principio de minimización de la propia norma que audita"],
        ["9", "No decidir si el PIMS está listo para certificación", "Respeta la cadena de responsabilidad de la auditoría interna formal"],
    ], anchos_cm=[0.8, 8.0, 7.2])
    doc.parrafo(
        "Además fija un **formato de respuesta** (encabezado con totales, una "
        "sección por hallazgo con la cita textual, «Siguientes pasos» con "
        "prioridades y rutas, incluida la del tablero) para que dos consultas "
        "distintas produzcan salidas comparables.")
    doc.titulo(2, "4.3 Conocimiento")
    doc.parrafo(
        "El asistente no lleva conocimiento dentro del prompt: apunta a "
        "archivos que puede leer cuando los necesita. Esto mantiene el prompt "
        "corto y permite actualizar la base normativa sin reescribir al "
        "asistente.")
    doc.tabla([
        ["Fuente", "Contenido", "Cuándo la lee"],
        ["`conocimiento/iso27701.md`",
         "Los 15 requisitos y qué controles de 27701:2025 y 27002:2022 respalda cada uno; qué aporta cada norma relacionada; proceso de auditoría por fases (ISO 19011) con responsables; principios (29100); Ley 29733 y ANPD; glosario",
         "Antes de justificar cualquier hallazgo con la norma, o cuando le preguntan teoría o proceso"],
        ["`requisitos.json`",
         "Los 15 requisitos con su descripción, evidencia esperada, vigencia y criticidad; también arma la consulta de recuperación de cada uno",
         "Al recuperar por RAG y al explicar por qué un requisito quedó `PARCIAL` o `SIN_EVIDENCIA`"],
        ["`plantillas/hallazgo_cumplimiento.md`", "Estructura del hallazgo", "Cuando completa o revisa un hallazgo"],
        ["`fragmentos_recuperados.json`, `resumen.json`, `hallazgo_*.md`, `tablero.html`",
         "Resultado de la corrida en curso", "Después de ejecutar el pipeline del skill"],
    ], anchos_cm=[4.5, 7.0, 4.5])
    doc.parrafo(
        "Regla de honestidad: si la pregunta cae fuera de esas fuentes (otra "
        "cláusula, otra norma), el asistente lo dice en lugar de inventar un "
        "número.")

    doc.titulo(2, "4.4 Cómo se relacionan asistente y skill")
    doc.numerada([
        "El usuario pide «evalúa nuestros documentos» a AuditorPIMS "
        "(identidad + instrucciones), que activa el skill "
        "`verificador-cumplimiento-pims`.",
        "`indexar_documentos.py` produce `indice_chunks.json`.",
        "`recuperar_fragmentos.py` produce `fragmentos_recuperados.json` (RAG, "
        "determinista).",
        "AuditorPIMS **lee el contenido**, decide y cita: `evaluacion.csv`.",
        "`generar_matriz_cumplimiento.py` produce `resumen.json` y un "
        "`hallazgo_<REQ-ID>.md` por requisito que necesita atención.",
        "`generar_tablero.py` produce `tablero.html`.",
        "AuditorPIMS interpreta el resultado con `conocimiento/iso27701.md` y "
        "entrega al usuario los hallazgos priorizados.",
    ])
    doc.parrafo(
        "El skill es reutilizable por cualquier asistente; AuditorPIMS es quien "
        "lee, decide y da contexto organizacional (a quién reporta, qué no "
        "decide, cómo prioriza).")

    doc.titulo(2, "4.5 Proceso de auditoría en el que trabaja el asistente")
    doc.parrafo(
        "El asistente no sustituye la auditoría interna formal de la "
        "organización: ocupa la fase de evaluación y prepara las siguientes. "
        "Fases según ISO 19011 y el ciclo PDCA de ISO/IEC 27701:2025, con el "
        "responsable de cada una:")
    doc.tabla([
        ["#", "Fase", "Qué ocurre", "Responsable", "Papel del asistente"],
        ["1", "Planificación de la revisión", "Definir el checklist de requisitos y la evidencia esperada", "DPO + auditor interno", "Explica el checklist vigente y propone ajustes en copia"],
        ["2", "Recolección de evidencia", "Cada área aporta sus documentos reales, sin clasificar", "Dueños de proceso", "Ninguno: recibe el corpus tal cual"],
        ["3", "Recuperación y lectura", "Indexar, recuperar por RAG y leer el contenido", "Auditor/analista", "**Ejecuta el skill y lee** los fragmentos, cita el texto"],
        ["4", "Comunicación de hallazgos", "Matriz, tablero y un hallazgo por requisito que necesita atención", "Auditor", "Presenta los hallazgos priorizados con su cita textual"],
        ["5", "Plan de tratamiento", "Asignar responsable y plazo a cada hallazgo", "DPO + responsables de área", "Propone el plazo sugerido (30/60/90 días); no decide por la organización"],
        ["6", "Seguimiento y cierre", "Verificar el documento corregido; cerrar el hallazgo", "DPO + auditor interno", "Relee el documento corregido antes de cerrar"],
    ], anchos_cm=[0.7, 3.0, 4.3, 3.0, 5.0])
    doc.parrafo(
        "Este reparto justifica las instrucciones 5, 6 y 9 del asistente: el "
        "skill produce la matriz y el tablero, el asistente lee y prioriza, y "
        "las decisiones de fondo (fases 5 y 6, y la validación de cada "
        "lectura) quedan siempre en manos del DPO.")

    doc.titulo(2, "4.6 Ejemplo de interacción")
    doc.parrafo(
        "**Usuario:** «Aquí están nuestros documentos "
        "(`entregable-1/demo/documentos_empresa_demo.csv`). ¿Cumplimos con la "
        "27701?»")
    doc.parrafo("**AuditorPIMS:**")
    for texto in [
        "Indexé %d documentos (%d fragmentos) y recuperé, por RAG, los más "
        "relevantes para cada uno de los 15 requisitos. Leí el contenido de "
        "cada uno — no solo el nombre — y esto es lo que encontré:" % (n_documentos, n_chunks),
        "%d requisitos cubiertos, %d parciales, %d sin evidencia. 2 documentos "
        "(política de teletrabajo, reporte de satisfacción del cliente) no "
        "corresponden a ningún requisito de privacidad."
        % (resumen["cubiertos"], resumen["parciales"], resumen["sin_evidencia"]),
        "**REQ-12 — Cláusulas con terceros — PRIORIDAD BAJA.** El contrato con "
        "el proveedor de nube (`DOC-06`) está vigente y define niveles de "
        "servicio, pero el propio texto dice: «El contrato no incluye una "
        "cláusula específica de confidencialidad ni de protección de datos "
        "personales para el personal del proveedor...» Control: A.2.1, "
        "A.1.5.5. Acción: agregar la cláusula faltante y firmar la adenda, "
        "plazo 90 días.",
        "**REQ-05 — Derechos ARCO — PRIORIDAD BAJA.** La política de "
        "privacidad (`DOC-01`) reconoce los derechos de acceso, rectificación, "
        "cancelación y oposición, pero solo los enuncia: no define plazos ni "
        "forma de solicitud. Acción: redactar el procedimiento operativo, "
        "plazo 90 días.",
        "**REQ-02, REQ-08, REQ-13** — sin evidencia; ver hallazgos "
        "correspondientes.",
        "Estos hallazgos son preliminares; la validación corresponde al "
        "Oficial de Protección de Datos. Tablero: `demo/salida/tablero.html`. "
        "Archivos: `demo/salida/resumen.json`, "
        "`demo/salida/hallazgo_REQ-12.md`, …",
    ]:
        doc.parrafo(texto, sangria_izq=1.0)

    doc.titulo(2, "4.7 Alternativas de despliegue del mismo asistente")
    doc.parrafo(
        "La identidad, las instrucciones y el conocimiento son independientes "
        "de la plataforma. El mismo diseño se traslada a:")
    doc.vinetas([
        "**Claude.ai (Proyecto):** instrucciones del proyecto = identidad + "
        "instrucciones; conocimiento del proyecto = `iso27701.md`, "
        "`requisitos.json`, `hallazgo_cumplimiento.md`; el usuario adjunta el "
        "corpus y el `resumen.json`/`tablero.html` producidos por los scripts.",
        "**Copilot Studio / GPT personalizado:** mismo esquema (instrucciones "
        "+ archivos de conocimiento + acción que ejecuta los scripts).",
    ])
    doc.parrafo(
        "Se eligió Claude Code porque permite que el asistente **ejecute** el "
        "skill y **lea** el contenido recuperado (no solo lo describa), que es "
        "lo que exige el resultado «skill funcional».")

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
    doc.parrafo(
        "Los 3 requisitos `SIN_EVIDENCIA` (REQ-02 PIA, REQ-08 análisis de "
        "accesos, REQ-13 auditoría interna) son aquellos para los que ningún "
        "documento del corpus trata el tema, aunque la recuperación haya "
        "traído algo por coincidencia de palabras sueltas: el modelo lo "
        "reconoce al leer el contenido.")

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
    ])

    doc.titulo(1, "7. Trabajo futuro")
    doc.vinetas([
        "Segundo entregable del curso: diseño formal del agente (objetivo, "
        "datos, contexto y herramientas), orquestación de skills y asistentes "
        "en flujos, y proyecto agéntico integrado.",
        "Evaluar la estabilidad del juicio del modelo: N lecturas del mismo "
        "corpus y medición del acuerdo entre ellas (hoy la trazabilidad es "
        "cualitativa: cada veredicto cita el `chunk_id` exacto y la matriz "
        "rechaza citas inexistentes).",
        "Re-validar el recall y la precisión de la recuperación (sección 3.8) "
        "cada vez que cambie el glosario de sinónimos.",
        "Extracción automática de texto desde PDF/Word para construir el CSV "
        "de entrada sin paso manual.",
        "Reutilizar el proceso (prompt → skill → pasos) para otros checklists: "
        "otra copia de `requisitos.json` parametriza el skill sin tocar los "
        "scripts.",
    ])

    ruta_salida = os.path.join(ENTREGABLE1, "Informe_Entregable1_Grupo6.docx")
    doc.guardar(ruta_salida)
    print("Informe escrito en %s" % ruta_salida)


if __name__ == "__main__":
    main()
