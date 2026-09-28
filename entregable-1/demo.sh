#!/usr/bin/env sh
# Demostracion del skill verificador-cumplimiento-pims (Grupo 6): RAG sobre
# el corpus documental de la empresa demo + lectura y evaluacion + tablero.
# La evaluacion (paso 4 del SKILL.md) la hace el modelo leyendo
# fragmentos_recuperados.json; generar_evaluacion_demo.py transcribe una
# lectura real ya hecha, para que la demo sea reproducible sin invocar de
# nuevo al modelo cada vez.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
SKILL="$AQUI/../.claude/skills/verificador-cumplimiento-pims"
DEMO="$AQUI/demo"
SALIDA="$DEMO/salida"
mkdir -p "$SALIDA"

python "$SKILL/scripts/generar_documentos_empresa_demo.py" --salida "$DEMO/documentos_empresa_demo.csv"
python "$SKILL/scripts/indexar_documentos.py" --documentos "$DEMO/documentos_empresa_demo.csv" --salida "$DEMO/indice_chunks.json"
python "$SKILL/scripts/recuperar_fragmentos.py" --indice "$DEMO/indice_chunks.json" --requisitos "$SKILL/requisitos.json" --salida "$DEMO/fragmentos_recuperados.json"
python "$SKILL/scripts/generar_evaluacion_demo.py" --salida "$DEMO/evaluacion_demo.csv"
python "$SKILL/scripts/generar_matriz_cumplimiento.py" --evaluacion "$DEMO/evaluacion_demo.csv" --requisitos "$SKILL/requisitos.json" --indice "$DEMO/indice_chunks.json" --salida "$SALIDA"
python "$SKILL/scripts/generar_tablero.py" --resumen "$SALIDA/resumen.json" --salida "$SALIDA/tablero.html"

echo ""
echo "Tablero generado en $SALIDA/tablero.html"
echo "Para verlo como app web: python \"$SKILL/scripts/servir_tablero.py\" --carpeta \"$SALIDA\""
