# TIF Auditoría de Sistemas – Grupo 6

Proyecto del curso: skill y asistente de IA para el PIMS (ISO/IEC 27701:2025),
tema "Agente de cumplimiento PIMS" (revisa evidencias y determina qué
requisitos del PIMS tienen evidencia y cuáles necesitan atención; normas de
apoyo 27001, 27002, 29100, ISO 19011, Ley 29733).

- Skill: `.claude/skills/verificador-cumplimiento-pims/` (leer su `SKILL.md`).
  Pipeline: indexar el corpus documental → recuperar por RAG (léxico,
  TF-IDF, solo stdlib) los fragmentos relevantes por requisito → el modelo
  LEE ese contenido y decide CUBIERTO/PARCIAL/SIN_EVIDENCIA citando el texto
  (no es determinista, a propósito) → formatear matriz + hallazgos + tablero
  web con semáforos (todo con solo librería estándar de Python).
- Asistente: `.claude/agents/auditor-cumplimiento-pims.md`.
- Enunciado y tema: `instrucciones/`.
- Entregable 1: `entregable-1/` (documentación por tarea + demo);
  `docs/` (en la raíz) genera el informe `.docx` del entregable 1.

Cuando el usuario entregue documentos/políticas/contratos o pregunte qué
requisitos del PIMS están cubiertos, usa el skill; para preguntas normativas
sin evidencia que evaluar, usa el asistente. Todo en español. Python solo con
librería estándar (incluida la recuperación RAG: sin embeddings ni librerías
externas, TF-IDF léxico a mano).

## Convención de commits

- Un commit simple y corto por cada cambio lógico; NUNCA agrupar archivos
  distintos en un solo commit salvo que formen parte del mismo cambio.
- Mensaje en un solo modo imperativo + qué se hizo:
  - `Fix <archivo>: <qué se corrigió>` (bugs)
  - `Add <archivo o función>: <qué se agregó>` (funcionalidad/archivos nuevos)
  - `Update <archivo>: <qué y por qué>` (cambios de contenido/config)
  - `Delete <archivo>: <motivo>` (eliminaciones)
- No tocar el `.pptx` ni los entregables en formato oficina sin que el
  usuario lo pida explícitamente.
- Probar con `python -m unittest discover -s tests` antes de commitear.
