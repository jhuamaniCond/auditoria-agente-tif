# Demostracion del skill verificador-cumplimiento-pims (Grupo 6): RAG sobre
# el corpus documental de la empresa demo + lectura y evaluacion + tablero.
# La evaluacion (paso 4 del SKILL.md) la hace el modelo leyendo
# fragmentos_recuperados.json; generar_evaluacion_demo.py transcribe una
# lectura real ya hecha, para que la demo sea reproducible sin invocar de
# nuevo al modelo cada vez.
$ErrorActionPreference = "Stop"
$skill = Join-Path $PSScriptRoot "..\.claude\skills\verificador-cumplimiento-pims"
$demo  = Join-Path $PSScriptRoot "demo"
$salida = Join-Path $demo "salida"
New-Item -ItemType Directory -Force $salida | Out-Null

python (Join-Path $skill "scripts\generar_documentos_empresa_demo.py") --salida (Join-Path $demo "documentos_empresa_demo.csv")
python (Join-Path $skill "scripts\indexar_documentos.py") --documentos (Join-Path $demo "documentos_empresa_demo.csv") --salida (Join-Path $demo "indice_chunks.json")
python (Join-Path $skill "scripts\recuperar_fragmentos.py") --indice (Join-Path $demo "indice_chunks.json") --requisitos (Join-Path $skill "requisitos.json") --salida (Join-Path $demo "fragmentos_recuperados.json")
python (Join-Path $skill "scripts\generar_evaluacion_demo.py") --salida (Join-Path $demo "evaluacion_demo.csv")
python (Join-Path $skill "scripts\generar_matriz_cumplimiento.py") --evaluacion (Join-Path $demo "evaluacion_demo.csv") --requisitos (Join-Path $skill "requisitos.json") --indice (Join-Path $demo "indice_chunks.json") --salida $salida
python (Join-Path $skill "scripts\generar_tablero.py") --resumen (Join-Path $salida "resumen.json") --salida (Join-Path $salida "tablero.html")

Write-Host "`nTablero generado en $salida\tablero.html"
Write-Host "Para verlo como app web: python `"$skill\scripts\servir_tablero.py`" --carpeta `"$salida`""
