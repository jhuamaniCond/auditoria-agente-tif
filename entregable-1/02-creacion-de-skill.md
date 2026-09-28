# Tarea 2 — Creación de Skill: activación, estructura y definición de pasos

**Grupo 6 · Skill `verificador-cumplimiento-pims`**

El skill está implementado en `.claude/skills/verificador-cumplimiento-pims/`
(formato de skills de Claude Code: una carpeta con `SKILL.md` más los
archivos que el skill necesita). Este documento explica las tres decisiones
de diseño que pide la tarea.

## 1. Activación

Un skill se activa por su **descripción**: el asistente la lee en cada turno
y decide si la tarea del usuario encaja. Por eso la descripción está escrita
en términos de lo que el usuario *dice*, no de lo que el skill *hace*:

```yaml
name: verificador-cumplimiento-pims
description: Revisa el corpus documental de una organización real (políticas,
  procedimientos, registros, contratos, capacitaciones — sin etiquetar contra
  la norma) usando RAG (indexa los documentos, recupera los fragmentos más
  relevantes por requisito) y luego LEE esos fragmentos para decidir, con
  justificación citada, qué requisitos del PIMS están cubiertos, cuáles
  parcialmente y cuáles sin evidencia, generando un hallazgo por cada brecha
  y un tablero web con semáforos.
```

Disparadores cubiertos (frases reales que usaría un auditor):

| El usuario dice… | Se activa |
|---|---|
| "Aquí están nuestras políticas y contratos, ¿cumplimos con la 27701?" | Sí |
| "¿Qué requisitos del PIMS nos faltan?" | Sí |
| "Genera el tablero de cumplimiento" | Sí (pasos 5–6) |
| "¿Qué exige el control A.3.25 de la 27701?" | No → responde el asistente con la base de conocimiento, sin ejecutar el pipeline |
| "Revisa estos logs de acceso a fichas de estudiantes" | No → son registros de actividad, no evidencia documental de cumplimiento |

También se puede invocar de forma explícita con `/verificador-cumplimiento-pims`.

## 2. Estructura

```
.claude/skills/verificador-cumplimiento-pims/
├── SKILL.md                                  activación, formato de entrada, pasos, límites
├── requisitos.json                           conocimiento parametrizable: 15 requisitos, evidencia esperada, vigencia, criticidad
├── scripts/
│   ├── indexar_documentos.py                 RAG paso 1: trocea documentos en fragmentos (chunks)
│   ├── recuperar_fragmentos.py               RAG paso 2: TF-IDF léxico, recupera por documento completo
│   ├── generar_matriz_cumplimiento.py        formatea el veredicto del modelo en matriz + hallazgos
│   ├── generar_tablero.py                    tablero web con semáforos (HTML/CSS planos)
│   ├── servir_tablero.py                     sirve el tablero como app web local (http.server)
│   ├── generar_documentos_empresa_demo.py    corpus documental sintético para la demo
│   └── generar_evaluacion_demo.py            veredicto de referencia (lectura ya hecha) para la demo
├── plantillas/
│   └── hallazgo_cumplimiento.md              formato del hallazgo con marcadores {{campo}}
└── conocimiento/
    └── iso27701.md                           15 requisitos -> controles 27701:2025/27002:2022, normas relacionadas, proceso de auditoría
```

Por qué está separado así:

- **`SKILL.md` es corto y solo tiene proceso.** Nada de código ni de teoría.
- **`requisitos.json` separa el conocimiento del código.** También es lo que
  arma la *consulta* de cada requisito para la recuperación RAG (su nombre,
  descripción y tipo de evidencia esperada).
- **`scripts/` solo hace lo mecánico y reproducible: indexar, recuperar,
  formatear y publicar.** Ningún script decide si un requisito está cubierto
  — eso exige entender lenguaje natural, y por diseño **no** está en el
  código (ver Tarea 1, sección 4). Todos usan solo librería estándar de
  Python (>= 3.8): `re`, `math`, `csv`, `json`, `unicodedata`,
  `http.server`.
- **`plantillas/` fija la salida.** El hallazgo tiene siempre las mismas
  secciones (criterio, evidencia, hallazgo, conclusión, seguimiento — ISO
  19011).
- **`conocimiento/` es lo que consulta el modelo para explicar** la norma
  detrás de cada hallazgo.

## 3. Definición de pasos

Los nueve pasos del `SKILL.md`, y qué problema resuelve cada uno:

| # | Paso | Quién lo hace | Qué evita |
|---|---|---|---|
| 1 | Ubicar el corpus (convertir a CSV si vienen PDFs sueltos) | Modelo | Trabajar sobre datos sin extraer |
| 2 | Indexar (`indexar_documentos.py`) | Script (determinista) | Perder la trazabilidad de qué párrafo viene de qué documento |
| 3 | Recuperar por RAG (`recuperar_fragmentos.py`) | Script (determinista, aproximado) | Que el modelo tenga que leer el corpus completo por cada requisito |
| 4 | **Leer los fragmentos y evaluar** (`evaluacion.csv`) | **Modelo (no determinista)** | Confiar en el nombre o tipo del documento sin leer si el contenido realmente cumple |
| 5 | Formatear matriz y hallazgos (`generar_matriz_cumplimiento.py`) | Script (determinista) | Hallazgos con formato inconsistente |
| 6 | Generar el tablero (`generar_tablero.py`) | Script (determinista) | Tener que leer JSON para ver el estado general |
| 7 | Interpretar para el usuario, por prioridad | Modelo | Respuestas desordenadas o veredictos anticipados |
| 8 | Justificar con `conocimiento/iso27701.md` | Modelo | Inventar números de cláusula |
| 9 | Releer si el usuario corrige un documento | Modelo | Asumir que un documento nuevo corrige el hueco sin leerlo |

### Flujo completo (RAG + lectura del modelo)

```
documentos_empresa_demo.csv (contenido real, sin etiquetar)
        │
        ▼  PASO 2 — indexar_documentos.py (determinista)
   indice_chunks.json (29 fragmentos de 11 documentos)
        │
        ▼  PASO 3 — recuperar_fragmentos.py (determinista, TF-IDF, aproximado)
   fragmentos_recuperados.json (hasta 4 documentos por requisito)
        │
        ▼  PASO 4 — el modelo LEE el contenido y decide (no determinista)
   evaluacion.csv (CUBIERTO / PARCIAL / SIN_EVIDENCIA + cita textual)
        │
        ▼  PASO 5 — generar_matriz_cumplimiento.py (determinista)
   resumen.json + hallazgo_<REQ-ID>.md + documentos no citados
        │
        ▼  PASO 6 — generar_tablero.py (determinista)
   tablero.html (semáforo verde/amarillo/rojo)
```

### Recuperación por documento completo

El recuperador rankea los documentos por su mejor fragmento y devuelve
**todos los párrafos** de cada documento seleccionado, no fragmentos sueltos.
La razón: el párrafo que revela un hueco suele compartir pocas palabras con
la consulta. En el contrato con el proveedor de nube, el párrafo que
reconoce que "no incluye cláusula de confidencialidad" puntúa menos que el
párrafo introductorio del mismo contrato; si se recuperaran solo los
fragmentos de mayor puntaje, ese párrafo quedaría fuera y el hueco sería
invisible. Al recibir el documento entero, el modelo siempre ve la frase que
revela la carencia, en su contexto.

### Límite de TF-IDF con sinónimos, y cómo se mitiga

TF-IDF compara **palabras**, no significado: si el requisito dice
"consentimiento del titular" y un documento dice "autorización expresa del
usuario", comparten cero palabras y el documento puede no recuperarse aunque
sea justo la evidencia que hace falta. Lo mitigamos con **expansión de
consulta** (query expansion): un glosario de ~16 grupos de equivalencias del
dominio (`GRUPOS_SINONIMOS` en `recuperar_fragmentos.py` — consentimiento/
autorización, titular/usuario/interesado, encargado/proveedor/tercero,
brecha/incidente, multifactor/MFA, etc.) que se suma a la consulta de cada
requisito **antes** de calcular el TF-IDF. Es la misma idea que usa un
auditor cuando entiende que el lenguaje de la norma no siempre es el
lenguaje de la empresa.

Dos decisiones de diseño, siguiendo la práctica estándar de esta técnica:

- **Se expande solo la consulta, nunca los documentos indexados** — el índice
  queda intacto, el efecto es fácil de explicar y se puede desactivar con
  `--sin-sinonimos` para comparar con/sin glosario.
- **Grupos pequeños y específicos del dominio** (no palabras genéricas): con
  el corpus de la demo, activar el glosario cambió a qué documentos se
  recupera en 4 de los 15 requisitos, sin alterar el veredicto final (los 5
  casos `PARCIAL` con hueco real se recuperan igual con o sin sinónimos,
  porque ya comparten vocabulario suficiente con la consulta).

### Reglas de calidad que nos impusimos

- Solo librería estándar de Python en todos los scripts.
- Los scripts nunca escriben dentro de la carpeta del skill.
- `evaluacion.csv` exige una fila por cada uno de los 15 requisitos
  (`generar_matriz_cumplimiento.py` falla si falta alguno) y cita el
  `chunk_id` exacto, para que cualquier hallazgo sea verificable releyendo el
  fragmento. **El script lo hace cumplir**: si un
  `chunk_id` citado no existe en el índice, o un veredicto CUBIERTO/PARCIAL
  no cita ningún fragmento, la matriz no se genera y el error dice exactamente
  qué fila corregir.
- El control de vigencia (`vigencia_max_dias` de `requisitos.json`) también
  se ejecuta: la matriz advierte (sin alterar el veredicto, que sigue siendo
  del modelo) cuando la fecha de un documento citado supera la vigencia
  máxima del requisito, y cuando un CUBIERTO no cita ningún tipo de evidencia
  esperada.
- `python -m unittest discover -s tests` (raíz del repo) ejecuta 24 pruebas
  de stdlib que cubren troceo CRLF/BOM, errores claros de entrada, validación
  de citas, vigencia, prioridad parametrizable y la demo completa end-to-end.
- Los documentos del corpus que ningún requisito citó como evidencia se
  reportan aparte (no se descartan en silencio): pueden ser irrelevantes o
  evidencia que el modelo pasó por alto.
- El generador de demo produce siempre el mismo corpus de 11 documentos: el
  jurado puede regenerarlo y obtener la misma recuperación.
- El corpus de entrada nunca se modifica.

## 4. Verificación realizada

```
$ python scripts/generar_documentos_empresa_demo.py --salida documentos_empresa_demo.csv
11 documentos escritos (2 de ellos, DOC-10 y DOC-11, no tratan protección de datos personales)

$ python scripts/indexar_documentos.py --documentos documentos_empresa_demo.csv --salida indice_chunks.json
11 documentos -> 29 fragmentos indexados

$ python scripts/recuperar_fragmentos.py --indice indice_chunks.json --requisitos ../requisitos.json --salida fragmentos_recuperados.json
Fragmentos recuperados para 15 requisitos (top-4, umbral 0.08)

$ python scripts/generar_evaluacion_demo.py --salida evaluacion_demo.csv
Evaluacion de referencia (15 requisitos) escrita

$ python scripts/generar_matriz_cumplimiento.py --evaluacion evaluacion_demo.csv --requisitos ../requisitos.json --indice indice_chunks.json --salida salida --fecha-revision 2026-07-01
Requisitos evaluados : 15   Cubiertos: 7   Parciales: 5   Sin evidencia: 3   Hallazgos: 8
Documentos no citados por ningun requisito: DOC-10, DOC-11
Citas verificadas: las 21 citas de chunk_id existen en el indice (29 fragmentos); sin --indice el script lo advierte
```

### 4.1 Calidad de la recuperación: recall y precisión

Medimos la recuperación léxica de la demo contra un *ground truth* de
referencia: el documento (o documentos) que realmente trata cada requisito,
obtenido de las citas de `evaluacion_demo.csv` y verificado a mano.

| Métrica | Valor | Lectura |
|---|---|---|
| **Recall** (12 requisitos con documento relevante en el corpus) | **100%** (12/12) | El documento que hace falta **nunca se pierde**: siempre está entre los hasta 4 documentos recuperados por el requisito. |
| **Precisión** (documentos recuperados que son relevantes) | **29%** (12/42) | Se recupera ruido a propósito: léxico + sinónimos trae documentos que comparten palabras sueltas. |
| Requisitos sin documento relevante (REQ-02, REQ-08, REQ-13) | 3 | La recuperación trajo 12 documentos irrelevantes en total; la lectura del modelo los descartó y el veredicto fue `SIN_EVIDENCIA` correcto en los 3. |

Es el intercambio deliberado de este diseño: el paso determinista (TF-IDF)
prioriza **no perder evidencia** (recall alto), y el paso no determinista
(lectura del modelo) filtra el ruido (precisión baja tolerada). Recuperar de
más cuesta solo unos párrafos extra en la lectura del requisito; recuperar de
menos ocultaría una brecha real. El tablero y `resumen.json` dejan además
constancia de los documentos que nadie citó (DOC-10, DOC-11) para que el
recuerdo "no recuperado" se revise a mano.

Los 5 casos `PARCIAL` son los que muestran el valor de leer el contenido en
vez de confiar en el nombre del documento:

| Requisito | Documento | Por qué es PARCIAL |
|---|---|---|
| REQ-03 RAT | DOC-02 | El propio registro reconoce que no incluye los convenios de 2026 |
| REQ-05 derechos ARCO | DOC-01 | La política declara los derechos pero no define el procedimiento operativo |
| REQ-07 autenticación segura | DOC-04 | Exige contraseña robusta pero el texto dice que no hay autenticación multifactor |
| REQ-11 capacitación | DOC-07 | El plan de capacitación en seguridad no cubre protección de datos ni tiene registro de ejecución |
| REQ-12 cláusulas con terceros | DOC-06 | El contrato con el proveedor de nube no incluye cláusula de confidencialidad ni de protección de datos |

Los 3 `SIN_EVIDENCIA` (REQ-02 PIA, REQ-08 análisis de accesos, REQ-13
auditoría interna) son requisitos para los que ningún documento del corpus
trata el tema, aunque la recuperación haya traído algo por coincidencia de
palabras sueltas — el modelo lo reconoce al leer el contenido.
