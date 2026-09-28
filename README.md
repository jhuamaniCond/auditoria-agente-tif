# TIF – Auditoría de Sistemas · Grupo 6

**Agente de cumplimiento PIMS** — skill y asistente de IA que reciben el
corpus documental real de una organización (políticas, procedimientos,
registros, contratos, capacitaciones — sin etiquetar contra la norma),
recuperan por **RAG** (indexado + recuperación léxica) los fragmentos
relevantes para cada requisito y **leen su contenido** para decidir qué
requisitos del PIMS (ISO/IEC 27701:2025) están cubiertos, cuáles
parcialmente y cuáles sin evidencia, con el respaldo de ISO/IEC 27001:2022,
27002:2022, 29100, ISO 19011 y la Ley N.° 29733. El checklist de requisitos,
el mapeo de controles y el proceso de auditoría por fases están en
`.claude/skills/verificador-cumplimiento-pims/conocimiento/iso27701.md`.

## Primer entregable: skill funcional especializado

| Tarea del entregable | Dónde está |
|---|---|
| De Prompt a Skill — transformación de la tarea en un proceso reutilizable | `entregable-1/01-de-prompt-a-skill.md` |
| Creación de Skill — activación, estructura y pasos | `entregable-1/02-creacion-de-skill.md` y el skill en `.claude/skills/verificador-cumplimiento-pims/` |
| Construcción de Asistente — identidad, instrucciones y conocimiento | `entregable-1/03-construccion-de-asistente.md` y el asistente en `.claude/agents/auditor-cumplimiento-pims.md` |
| Resultado: skill funcional | `entregable-1/demo/` (datos de prueba, tablero y salida generada) e `entregable-1/Informe_Entregable1_Grupo6.docx` |

## Estructura

```
TIF/
├── .claude/
│   ├── skills/verificador-cumplimiento-pims/  <- el skill (SKILL.md, requisitos.json, scripts/, plantillas/, conocimiento/)
│   └── agents/auditor-cumplimiento-pims.md    <- el asistente AuditorPIMS
├── docs/                                      <- generar_informe.py, generar_figuras.py, figuras/ (arma el .docx del entregable 1)
├── entregable-1/
│   ├── 01-de-prompt-a-skill.md
│   ├── 02-creacion-de-skill.md
│   ├── 03-construccion-de-asistente.md
│   ├── demo.ps1 / demo.sh                     <- reproduce la demostración (RAG + tablero)
│   ├── Informe_Entregable1_Grupo6.docx        <- informe del entregable (salida de docs/generar_informe.py)
│   └── demo/
│       ├── documentos_empresa_demo.csv        <- 11 documentos reales de la empresa demo (sin clasificar)
│       ├── indice_chunks.json                 <- 29 fragmentos indexados (RAG paso 1)
│       ├── fragmentos_recuperados.json        <- fragmentos recuperados por requisito (RAG paso 2)
│       ├── evaluacion_demo.csv                <- veredicto de referencia (lectura ya hecha por el asistente)
│       └── salida/                            <- resumen.json + hallazgo_<REQ-ID>.md + tablero.html
├── instrucciones/                             <- enunciado del TIF y tema asignado
└── README.md
```

## Cómo demostrarlo

Requisito: Python 3.8 o superior (sin dependencias externas).

```powershell
cd entregable-1
.\demo.ps1          # Windows
# ./demo.sh         # Linux / macOS
```

Esto genera el corpus de 11 documentos, lo indexa, recupera por RAG los
fragmentos relevantes para cada uno de los 15 requisitos, aplica la
evaluación de referencia (la lectura que ya hizo el asistente sobre ese
contenido) y genera la matriz, los hallazgos y el tablero web. Abrir
`entregable-1/demo/salida/tablero.html` en el navegador para ver el semáforo,
o servirlo como app local:

```powershell
python .claude/skills/verificador-cumplimiento-pims/scripts/servir_tablero.py --carpeta entregable-1/demo/salida
```

Resultado esperado: 11 documentos, 15 requisitos evaluados — **7 CUBIERTO**,
**5 PARCIAL**, **3 SIN_EVIDENCIA** — y 2 documentos no citados por ningún
requisito (no tratan protección de datos personales).

**Con el asistente (Claude Code) sobre documentos nuevos:** abrir Claude Code
en la carpeta `TIF/` y escribir, por ejemplo:

```
Aquí están nuestros documentos (ruta al CSV). ¿Cumplimos con la 27701?
```

El asistente `auditor-cumplimiento-pims` indexa, recupera por RAG, **lee el
contenido real** de cada documento recuperado y decide — citando el texto —
si cada requisito está cubierto. También se puede invocar directamente con
`/verificador-cumplimiento-pims`.

**Con documentos propios:** arma un CSV con columnas
`id_documento, tipo, fecha_documento, responsable, ubicacion, contenido`
(párrafos separados por línea en blanco; ver `SKILL.md`). Para otra
institución o checklist, copiar `requisitos.json`, ajustar requisitos,
vigencias y criticidad, y pasar la copia con `--requisitos`.

## Escenario sembrado en la demo

Huecos intencionales **dentro de documentos reales** (no documentos enteros
ausentes o mal etiquetados) — el patrón que pidió la cátedra para que la
demo sea convincente:

| Requisito | Documento | Estado | Por qué |
|---|---|---|---|
| REQ-03 | RAT (`DOC-02`) | PARCIAL | El propio registro reconoce que no incluye los convenios de 2026 |
| REQ-05 | Política de privacidad (`DOC-01`) | PARCIAL | Declara los derechos ARCO pero no define el procedimiento operativo |
| REQ-07 | Manual de accesos (`DOC-04`) | PARCIAL | Exige contraseña robusta pero no contempla autenticación multifactor |
| REQ-11 | Plan de capacitación (`DOC-07`) | PARCIAL | No cubre protección de datos ni registra ejecución |
| REQ-12 | Contrato con proveedor de nube (`DOC-06`) | PARCIAL | No incluye cláusula de confidencialidad ni de protección de datos |
| REQ-02, REQ-08, REQ-13 | — | SIN EVIDENCIA | Ningún documento del corpus trata PIA, análisis de accesos ni auditoría interna |

Los 7 requisitos restantes tienen evidencia que, al leerla, sí satisface lo
exigido. Además, 2 documentos reales de la institución (política de
teletrabajo, reporte de satisfacción del cliente) no son citados por ningún
requisito — el asistente verifica que no corresponden a privacidad en vez de
forzarlos a encajar en algo.

## Alcance

Esta carpeta contiene el primer entregable completo (De Prompt a Skill,
Creación de Skill, Construcción de Asistente), con su informe. El segundo
entregable (diseño de agente, orquestación, proyecto agéntico) aún no se ha
trabajado.
