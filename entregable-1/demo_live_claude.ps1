# Demostracion EN VIVO del skill verificador-cumplimiento-pims (Grupo 6).
# Igual que demo.ps1, pero el paso 4 (leer y evaluar) lo hace Claude en el
# momento via Claude Code, en vez de transcribir una evaluacion ya guardada.
# Requiere tener Claude Code instalado y con sesion iniciada (comando
# `claude`). Como la lectura del modelo no es determinista, los veredictos
# pueden variar entre corridas.
#
# Modos del paso 4:
#   .\demo_live.ps1              abre la interfaz normal de Claude Code: se ve
#                                el razonamiento, cada archivo que lee y lo que
#                                escribe. Al terminar, escribe /exit y el
#                                script sigue con la matriz y el tablero.
#   .\demo_live.ps1 -Automatico  sin interaccion: muestra en la terminal, a
#                                medida que ocurre, el pensamiento, las
#                                herramientas que usa y sus respuestas.
param([switch]$Automatico)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$raiz  = Resolve-Path (Join-Path $PSScriptRoot "..")
$skill = Join-Path $raiz ".claude\skills\verificador-cumplimiento-pims"
$demo  = Join-Path $PSScriptRoot "demo"
$vivo  = Join-Path $demo "en_vivo"
$salida = Join-Path $vivo "salida"
New-Item -ItemType Directory -Force $salida | Out-Null

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    throw "No se encontro el comando 'claude'. Instala Claude Code o usa demo.ps1."
}

Write-Host "`n[1/6] Generando el corpus documental de la empresa demo..."
python (Join-Path $skill "scripts\generar_documentos_empresa_demo.py") --salida (Join-Path $vivo "documentos_empresa_demo.csv")
Write-Host "[2/6] Indexando documentos..."
python (Join-Path $skill "scripts\indexar_documentos.py") --documentos (Join-Path $vivo "documentos_empresa_demo.csv") --salida (Join-Path $vivo "indice_chunks.json")
Write-Host "[3/6] Recuperando fragmentos por requisito (RAG TF-IDF)..."
python (Join-Path $skill "scripts\recuperar_fragmentos.py") --indice (Join-Path $vivo "indice_chunks.json") --requisitos (Join-Path $skill "requisitos.json") --salida (Join-Path $vivo "fragmentos_recuperados.json")

$evaluacion = Join-Path $vivo "evaluacion.csv"
if (Test-Path $evaluacion) { Remove-Item $evaluacion }

# Sin comillas dobles dentro del prompt: PowerShell 5.1 corta el argumento
# que se pasa a un ejecutable nativo en la primera comilla doble interna.
$prompt = @"
Eres el auditor del PIMS. Sigue EXACTAMENTE el paso 4 (Leer y evaluar) de
.claude/skills/verificador-cumplimiento-pims/SKILL.md (leelo primero).
Lee el texto completo de los fragmentos en
entregable-1/demo/en_vivo/fragmentos_recuperados.json y, para cada uno de los
15 requisitos de .claude/skills/verificador-cumplimiento-pims/requisitos.json,
decide CUBIERTO, PARCIAL o SIN_EVIDENCIA.
Escribe entregable-1/demo/en_vivo/evaluacion.csv en UTF-8 con la cabecera
exacta: requisito_id,estado,evidencia_citada,justificacion
- evidencia_citada: chunk_id exactos separados por ';' (vacio solo si SIN_EVIDENCIA).
- justificacion: que dice el texto que sustenta la decision, entre comillas dobles.
Para juzgar la vigencia de los documentos usa como fecha de referencia
2026-07-01 (la misma que usa la matriz en el paso siguiente), no la fecha de hoy.
No ejecutes scripts ni modifiques otros archivos.
Al terminar, responde en espanol con una tabla breve: requisito, estado y
el motivo en una linea.
"@

Write-Host "[4/6] Claude esta leyendo los fragmentos y evaluando cada requisito (puede tardar unos minutos)...`n"
Push-Location $raiz
try {
    if ($Automatico) {
        # stream-json emite un evento JSON por linea mientras Claude trabaja;
        # se muestran el pensamiento, las herramientas y el texto al vuelo.
        claude -p $prompt --allowedTools "Read,Write" --output-format stream-json --verbose |
            ForEach-Object {
                try { $evento = $_ | ConvertFrom-Json } catch { return }
                if ($evento.type -eq "assistant") {
                    foreach ($bloque in $evento.message.content) {
                        switch ($bloque.type) {
                            "thinking" { if ($bloque.thinking) { Write-Host "  (pensando) $($bloque.thinking)" -ForegroundColor DarkGray } }
                            "text"     { Write-Host "`n$($bloque.text)`n" -ForegroundColor White }
                            "tool_use" {
                                $objetivo = $bloque.input.file_path
                                if (-not $objetivo) { $objetivo = ($bloque.input | ConvertTo-Json -Compress) }
                                Write-Host "  > $($bloque.name): $objetivo" -ForegroundColor Cyan
                            }
                        }
                    }
                } elseif ($evento.type -eq "result") {
                    Write-Host "`n[Claude termino en $([math]::Round($evento.duration_ms / 1000)) s]" -ForegroundColor Green
                }
            }
    } else {
        Write-Host "Se abrira Claude Code. Cuando termine de evaluar, escribe /exit para continuar con la matriz y el tablero.`n" -ForegroundColor Yellow
        claude $prompt --allowedTools "Read,Write"
    }
} finally {
    Pop-Location
}
if (-not (Test-Path $evaluacion)) {
    throw "Claude no genero $evaluacion. Revisa la sesion de Claude Code o usa demo.ps1 como respaldo."
}

# --indice hace cumplir el paso 4: aborta si Claude cita un chunk_id que no
# existe en el corpus, asi que la IA no puede inventar evidencia.
Write-Host "`n[5/6] Validando citas y generando matriz y hallazgos..."
python (Join-Path $skill "scripts\generar_matriz_cumplimiento.py") --evaluacion $evaluacion --requisitos (Join-Path $skill "requisitos.json") --indice (Join-Path $vivo "indice_chunks.json") --salida $salida --fecha-revision 2026-07-01
if ($LASTEXITCODE -ne 0) { throw "La validacion de la evaluacion fallo (ver mensaje arriba)." }
Write-Host "[6/6] Generando tablero..."
python (Join-Path $skill "scripts\generar_tablero.py") --resumen (Join-Path $salida "resumen.json") --salida (Join-Path $salida "tablero.html")

Write-Host "`nTablero generado en $salida\tablero.html"
Write-Host "Para verlo como app web: python `"$skill\scripts\servir_tablero.py`" --carpeta `"$salida`""
