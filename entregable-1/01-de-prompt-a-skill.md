# Tarea 1 — De Prompt a Skill: transformación de la tarea en un proceso reutilizable

**Grupo 6 · Agente de cumplimiento PIMS · ISO/IEC 27701:2025**

## 1. El prompt de partida

Sin un skill, la tarea se resuelve con un prompt suelto, escrito cada vez
que hace falta:

> "Aquí tienes nuestras políticas, procedimientos y contratos. Revisa si eso
> alcanza para cumplir con la ISO 27701 y dime qué nos falta."

## 2. Por qué ese prompt no sirve como proceso

| Problema del prompt | Consecuencia |
|---|---|
| No dice contra qué checklist se compara. | El modelo inventa o adapta de memoria qué requisitos existen, sin fijar cuántos ni cuáles. |
| Con decenas de documentos completos, el prompt no cabe o cuesta caro en cada consulta. | No es viable repetir la evaluación cada vez que cambia un documento. |
| No fija cómo decidir "cumple" — ¿basta con que el documento exista? ¿con que el nombre coincida? | Dos ejecuciones pueden llegar a conclusiones distintas sin que quede registro de por qué. |
| No fija la salida. | A veces devuelve una lista, a veces un párrafo; nada que se pueda archivar como papel de trabajo de auditoría. |
| "Dime qué nos falta" pide una decisión final que no le corresponde a la herramienta. | Se salta el proceso de auditoría interna (§9.2): la evaluación definitiva la hace el Oficial de Protección de Datos. |
| No es repetible ni verificable. | No hay forma de demostrar a un auditor externo cómo se llegó a la conclusión de "cubierto" o "falta". |

## 3. El riesgo de fondo: confiar en lo declarado

Además de esos problemas, hay un riesgo de fondo: **confiar en lo que la
organización declara sin mirar la evidencia real**. Un documento puede
llamarse "procedimiento de respuesta a incidentes de privacidad" y no
mencionar datos personales en ningún párrafo; una política puede figurar
como "vigente" y no incluir el procedimiento que el requisito exige. Si la
herramienta solo mira nombres, tipos o estados declarados, no detecta nada
de eso — y es exactamente el hueco que un agente de cumplimiento debe
encontrar. Por eso el skill hace que el modelo lea el contenido real de cada
documento.

## 4. Descomposición de la tarea

1. **Corpus documental real, sin etiquetar.** Los documentos de la
   organización (`id_documento, tipo, fecha_documento, responsable,
   ubicacion, contenido`), con el **contenido real** en párrafos, no un
   resumen ni una clasificación previa.
2. **Conocimiento explícito.** El checklist de 15 requisitos del PIMS
   (`requisitos.json`): qué exige cada uno y qué evidencia lo satisfaría.
3. **Recuperación (RAG), determinista.** Trocear los documentos e indexar los
   fragmentos; para cada requisito, recuperar por coincidencia léxica
   (TF-IDF) los documentos más relevantes. Esto es mecánico y reproducible,
   pero **aproximado**: puede traer un documento irrelevante o dejar fuera
   uno relevante con vocabulario distinto.
4. **Lectura y juicio, del modelo — el paso que de verdad decide.** Leer el
   contenido de los fragmentos recuperados y decidir si cada requisito está
   `CUBIERTO`, `PARCIAL` (hay algo, pero el propio texto revela un hueco) o
   `SIN_EVIDENCIA`, citando la frase exacta que sustenta el veredicto. Esto
   ya no es determinista a propósito: la calidad y suficiencia de un
   documento es un juicio, no un cálculo, y forzarlo a ser determinista
   ocultaría justamente los huecos reales.
5. **Salida estructurada.** `resumen.json` (matriz completa), un
   `hallazgo_<REQ-ID>.md` por requisito que necesita atención, y un tablero
   web con semáforos (verde/amarillo/rojo) para una lectura rápida.

## 5. Los 15 requisitos del checklist

Se eligieron 15 requisitos representativos de ISO/IEC 27701:2025 para una
institución educativa controladora de datos de estudiantes, cubriendo tanto
las cláusulas del sistema de gestión (5 a 10) como los controles del Anexo A
(tablas A.1, A.2 y A.3). El detalle completo está en `requisitos.json` y en
`conocimiento/iso27701.md`.

## 6. El prompt, después

Lo que era un párrafo ambiguo se convierte en una invocación:

> "Evalúa el cumplimiento del PIMS con nuestros documentos
> (`documentos_empresa_demo.csv`)."

El skill sabe qué checklist aplicar, cómo recuperar lo relevante de cada
documento, y qué archivos producir. Lo que sigue dependiendo del criterio del
modelo — y así queda documentado, no oculto — es la lectura de si el
contenido realmente cumple.

## 7. Criterios que usamos para decidir qué va al skill y qué queda en el prompt

- Si algo debe ser **igual en todas las ejecuciones** (los 15 requisitos, la
  forma de indexar y recuperar, el formato del hallazgo y del tablero) → va
  al skill, en scripts deterministas.
- Si algo requiere **entender el contenido de un documento en lenguaje
  natural** (¿esta cláusula alcanza?, ¿este procedimiento es operativo o solo
  declarativo?) → es tarea del modelo, documentada como tal en el `SKILL.md`,
  con la exigencia de citar la evidencia textual para que sea revisable.
- Si algo es una **decisión de la organización** (¿el PIMS está listo para
  certificación?) → no va a ninguno de los dos; se deja como pendiente en la
  sección de seguimiento del hallazgo.

## Trabajo futuro

- Medir la calidad de recuperación con recall/precisión sobre un ground truth
  (hecho en `02-creacion-de-skill.md`, sección 4.1: recall 100%, precisión 29%
  en la demo) y re-validar al cambiar el glosario de sinónimos.
- Endurecer el pipeline con validación automática de citas y control de
  vigencia (`generar_matriz_cumplimiento.py`), con suite de pruebas en
  `tests/`.
- Reutilizar el proceso (prompt → skill → pasos) para otros checklists: otra
  copia de `requisitos.json` parametriza el skill sin tocar los scripts.
