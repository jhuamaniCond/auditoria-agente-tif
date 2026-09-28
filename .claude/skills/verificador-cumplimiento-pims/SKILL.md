---
name: verificador-cumplimiento-pims
description: Revisa el corpus documental de una organización real (políticas, procedimientos, registros, contratos, capacitaciones — sin etiquetar contra la norma) usando RAG (indexa los documentos, recupera los fragmentos más relevantes por requisito) y luego LEE esos fragmentos para decidir, con justificación citada, qué requisitos del PIMS (ISO/IEC 27701:2025) están cubiertos, cuáles parcialmente y cuáles sin evidencia, generando un hallazgo por cada brecha y un tablero web con semáforos. Úsala cuando alguien pida evaluar, auditar o hacer un gap analysis del cumplimiento de privacidad/PIMS, entregue documentos o políticas y pregunte si cubren la 27701, o pida preparar una auditoría interna o de certificación del PIMS.
---

# Verificador de cumplimiento PIMS

Skill del Grupo 6 – Auditoría de Sistemas. Soporta el PIMS (ISO/IEC 27701:2025)
como función de **auditoría de cumplimiento** (equivalente a §9.2 auditoría
interna, con la forma de hallazgo de ISO 19011), con el respaldo de ISO/IEC
27001:2022, 27002:2022, 29100 (principios) y la Ley 29733; ver
`conocimiento/iso27701.md`. Recibe el corpus documental de una organización,
recupera con RAG los fragmentos relevantes para cada uno de los 15 requisitos
del PIMS y **lee ese contenido** (no un campo declarado como "vigente") para
decidir si el requisito está cubierto.

Este skill lee **el contenido real** de las evidencias (políticas,
procedimientos, registros, contratos, capacitaciones), no registros de
actividad ni logs de acceso. La decisión de si un requisito está cubierto no
es un cálculo determinista: es un juicio del modelo sobre lo que dice el
texto, citando la evidencia concreta que lo sustenta.

## Cuándo se activa

- El usuario entrega o menciona documentos, políticas, contratos o registros
  de la organización y pregunta si cumplen con la 27701 / el PIMS.
- Pide "haz un gap analysis del PIMS", "qué controles de la 27701 nos
  faltan", "audita el cumplimiento de privacidad", "prepara la checklist
  para la auditoría/certificación", "genera el tablero de cumplimiento".
- Pregunta qué requisitos del PIMS están cubiertos y cuáles no, o pide
  priorizar qué atender primero.

No se activa para: analizar registros de actividad/acceso a datos
personales, ni cuando el usuario solo quiere teoría de la norma sin
documentos que evaluar (ahí responde el asistente
`auditor-cumplimiento-pims` con la base de conocimiento).

## Estructura del skill

```
verificador-cumplimiento-pims/
├── SKILL.md                             <- este archivo: activación y pasos
├── requisitos.json                      <- 15 requisitos del PIMS, evidencia esperada, vigencia, criticidad (parametrizable)
├── scripts/
│   ├── indexar_documentos.py            <- RAG paso 1: trocea documentos en fragmentos (solo stdlib)
│   ├── recuperar_fragmentos.py          <- RAG paso 2: TF-IDF lexico, recupera por documento (solo stdlib)
│   ├── generar_matriz_cumplimiento.py   <- formatea el veredicto del modelo en matriz + hallazgos (solo stdlib)
│   ├── generar_tablero.py               <- tablero web con semaforos verde/amarillo/rojo (HTML/CSS planos, solo stdlib)
│   ├── servir_tablero.py                <- sirve el tablero como app web local (http.server, solo stdlib)
│   ├── generar_documentos_empresa_demo.py  <- corpus documental sintetico para la demo
│   └── generar_evaluacion_demo.py          <- veredicto de referencia (lo que decidio el asistente) para la demo
├── plantillas/
│   └── hallazgo_cumplimiento.md         <- formato del hallazgo (ISO 19011: criterio, evidencia, hallazgo, conclusión)
└── conocimiento/
    └── iso27701.md                      <- mapeo requisito -> control 27701/27002, normas relacionadas, proceso de auditoría
```

## Formato de entrada

CSV con el corpus documental (en cualquier orden de columnas):

`id_documento, tipo, fecha_documento, responsable, ubicacion, contenido`

- `contenido`: el texto real del documento, con **párrafos separados por una
  línea en blanco** (cada párrafo se indexa como un fragmento independiente).
  Es lo único que importa para decidir cobertura: no hay columna `estado`
  declarada — la vigencia y suficiencia se leen del propio texto.
- No hace falta indicar a qué requisito corresponde cada documento: eso lo
  decide la recuperación (RAG) más la lectura del modelo, no el usuario.
- Un documento puede cubrir varios requisitos (y hacerlo bien en unos y mal
  en otros): no lo trates como "un documento = un requisito".

## Pasos

1. **Ubicar el corpus.** Identifica la ruta del CSV de documentos. Si el
   usuario entrega documentos sueltos (PDF, Word) en vez de un CSV, extrae su
   texto y arma el CSV con las mismas columnas antes de seguir.

2. **Indexar.**
   ```
   python <ruta_skill>/scripts/indexar_documentos.py --documentos <archivo.csv> --salida <carpeta>/indice_chunks.json
   ```

3. **Recuperar fragmentos por requisito (RAG).**
   ```
   python <ruta_skill>/scripts/recuperar_fragmentos.py --indice <carpeta>/indice_chunks.json --requisitos <ruta_skill>/requisitos.json --salida <carpeta>/fragmentos_recuperados.json
   ```
   Esto NO decide nada: solo acerca, por requisito, los documentos más
   relevantes por coincidencia léxica (TF-IDF), con la consulta expandida
   por un glosario de sinónimos del dominio (para que "consentimiento" y
   "autorización" se relacionen, por ejemplo). Es aproximado — puede traer
   documentos irrelevantes (comparten alguna palabra común) y, más raro,
   dejar fuera alguno relevante si usa vocabulario que ni el glosario cubre.
   Por eso el siguiente paso es indispensable y no un formalismo.

4. **Leer y evaluar (el paso central — lo hace el modelo, no un script).**
   Abre `fragmentos_recuperados.json`. Para cada uno de los 15 requisitos,
   **lee el texto completo de los fragmentos recuperados** (no solo el
   título o el `tipo` del documento) y decide:
   - `CUBIERTO`: el contenido demuestra que el requisito está satisfecho
     (aprobado, vigente, completo, específico — no solo que "existe algo con
     un nombre parecido").
   - `PARCIAL`: hay evidencia relacionada, pero el propio texto revela un
     hueco (falta una cláusula, no hay procedimiento operativo aunque se
     declaren los derechos, el documento reconoce que está desactualizado o
     incompleto, cubre el tema en general pero no el punto específico que
     pide el requisito).
   - `SIN_EVIDENCIA`: ningún fragmento recuperado trata realmente el
     requisito (aunque haya sido recuperado por compartir alguna palabra).
   No te fíes de que un documento se llame o esté etiquetado como lo que el
   requisito pide: lee si el contenido realmente lo cumple. Escribe el
   veredicto en `evaluacion.csv` (`requisito_id, estado, evidencia_citada,
   justificacion`), citando el `chunk_id` exacto y explicando en la
   justificación **qué dice el texto** que sustenta la decisión. Esta
   evaluación no es determinista: dos lecturas podrían diferir en casos
   límite, por eso cada justificación debe ser verificable releyendo el
   fragmento citado.

5. **Formatear la matriz y los hallazgos.**
   ```
   python <ruta_skill>/scripts/generar_matriz_cumplimiento.py --evaluacion <carpeta>/evaluacion.csv --requisitos <ruta_skill>/requisitos.json --indice <carpeta>/indice_chunks.json --salida <carpeta>/salida
   ```
   Produce `salida/resumen.json` y un `salida/hallazgo_<REQ>.md` por cada
   requisito `PARCIAL` o `SIN_EVIDENCIA`, y reporta qué documentos del
   corpus no fueron citados como evidencia por ningún requisito (pueden ser
   irrelevantes, o evidencia real que el modelo pasó por alto — revísalos).

6. **Generar el tablero.**
   ```
   python <ruta_skill>/scripts/generar_tablero.py --resumen <carpeta>/salida/resumen.json --salida <carpeta>/salida/tablero.html
   ```
   Para verlo como una app (no solo un archivo), ofrece:
   `python <ruta_skill>/scripts/servir_tablero.py --carpeta <carpeta>/salida` y abrir `http://localhost:8000/tablero.html`.

7. **Interpretar para el usuario.** Presenta, en este orden: totales
   (cubiertos/parciales/sin evidencia) y documentos no citados; luego cada
   hallazgo por prioridad de atención (alta primero) con la cita textual que
   sustenta el veredicto; recuerda que la lectura es preliminar y que el
   Oficial de Protección de Datos debe validarla.

8. **Justificar con la norma.** Para cada requisito, relaciona con la
   cláusula o control de ISO/IEC 27701:2025 y, si aplica, con ISO/IEC
   27002:2022 o la Ley 29733, usando `conocimiento/iso27701.md`. No inventes
   números de cláusula.

9. **Si el usuario aporta un documento corregido**, vuelve a indexar (paso 2)
   solo si cambió el corpus, recupera de nuevo (paso 3) y relee (paso 4) — no
   asumas que corrige el hueco sin leer el nuevo contenido.

## Demostración rápida

```
python <ruta_skill>/scripts/generar_documentos_empresa_demo.py --salida documentos_empresa_demo.csv
python <ruta_skill>/scripts/indexar_documentos.py --documentos documentos_empresa_demo.csv --salida indice_chunks.json
python <ruta_skill>/scripts/recuperar_fragmentos.py --indice indice_chunks.json --requisitos <ruta_skill>/requisitos.json --salida fragmentos_recuperados.json
python <ruta_skill>/scripts/generar_evaluacion_demo.py --salida evaluacion_demo.csv
python <ruta_skill>/scripts/generar_matriz_cumplimiento.py --evaluacion evaluacion_demo.csv --requisitos <ruta_skill>/requisitos.json --indice indice_chunks.json --salida salida
python <ruta_skill>/scripts/generar_tablero.py --resumen salida/resumen.json --salida salida/tablero.html
```

Resultado esperado: 11 documentos, 15 requisitos evaluados — 7 `CUBIERTO`,
5 `PARCIAL` (REQ-03 RAT desactualizado, REQ-05 política sin procedimiento
ARCO operativo, REQ-07 sin autenticación multifactor, REQ-11 capacitación
que no cubre privacidad, REQ-12 contrato sin cláusula de confidencialidad),
3 `SIN_EVIDENCIA` (REQ-02 PIA, REQ-08 análisis de accesos, REQ-13 auditoría
interna) y 2 documentos no citados por ningún requisito (política de
teletrabajo, reporte de satisfacción del cliente — no tratan privacidad).

`generar_evaluacion_demo.py` escribe una evaluación de referencia (una
lectura real ya hecha) para que la demo sea reproducible sin volver a invocar
al modelo; para una lectura nueva, sigue el paso 4 sobre
`fragmentos_recuperados.json`.

## Límites

- La recuperación (RAG léxico, paso 3) es aproximada: TF-IDF compara palabras,
  no significado, así que puede traer documentos irrelevantes y, sobre todo,
  no traer uno relevante que use otra palabra para lo mismo (el requisito
  dice "consentimiento del titular", el documento dice "autorización expresa
  del usuario" — comparten cero palabras). Se mitiga con dos cosas: se
  recuperan varios documentos por requisito (no solo el mejor), y la consulta
  se expande con un glosario de ~16 grupos de equivalencias del dominio
  (`GRUPOS_SINONIMOS` en `recuperar_fragmentos.py`: consentimiento/
  autorización, titular/usuario, encargado/proveedor/tercero, etc. — solo se
  expande la consulta, nunca los documentos indexados). No lo elimina — si un
  requisito importante queda `SIN_EVIDENCIA`, vale la pena revisar el corpus
  a mano antes de darlo por cerrado, o ejecutar con `--sin-sinonimos` para
  comparar.
- La lectura y el juicio de suficiencia (paso 4) los hace el modelo: no es
  determinista, dos ejecuciones podrían diferir en casos límite. Por eso
  cada hallazgo cita el fragmento exacto (`chunk_id`) que sustenta el
  veredicto — es revisable aunque no sea reproducible bit a bit.
- No accede a sistemas ni repositorios documentales: trabaja sobre el CSV que
  se le entrega. Si el usuario da PDFs u otros formatos, hay que extraer el
  texto primero (paso 1).
- No decide si un requisito está realmente cumplido ni si el PIMS está listo
  para certificación; eso corresponde al Oficial de Protección de Datos y a
  la auditoría interna formal.
