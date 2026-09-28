# -*- coding: utf-8 -*-
"""
generar_tablero.py
===============================================================================
Genera un tablero web estatico (tablero.html) a partir de resumen.json: los
15 requisitos del PIMS en un semaforo verde (CUBIERTO) / amarillo (PARCIAL) /
rojo (SIN_EVIDENCIA), con la justificacion y la evidencia citada de cada uno.

Es HTML y CSS planos escritos por este script (sin frameworks ni librerias
externas): solo libreria estandar de Python (>= 3.8). Para verlo como una
"app web", sirvelo con servir_tablero.py; para verlo directo, abre el
archivo .html en el navegador.

Uso:
  python generar_tablero.py --resumen resumen.json --salida tablero.html
===============================================================================
"""

import argparse
import html
import json

COLOR_POR_ESTADO = {
    "CUBIERTO": "#1e7e34",
    "PARCIAL": "#8a6d00",
    "SIN_EVIDENCIA": "#a12622",
}
FONDO_POR_ESTADO = {
    "CUBIERTO": "#e6f4ea",
    "PARCIAL": "#fff6da",
    "SIN_EVIDENCIA": "#fbe7e6",
}
ETIQUETA_POR_ESTADO = {
    "CUBIERTO": "CUBIERTO",
    "PARCIAL": "PARCIAL",
    "SIN_EVIDENCIA": "SIN EVIDENCIA",
}

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Tablero de cumplimiento PIMS — Grupo 6</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; padding: 24px 32px; background: #f4f5f7; color: #1a1a1a; }}
  h1 {{ font-size: 20px; margin-bottom: 4px; }}
  .subtitulo {{ color: #555; margin-bottom: 20px; }}
  .resumen {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .tarjeta {{ background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 10px 16px; min-width: 120px; }}
  .tarjeta .n {{ font-size: 22px; font-weight: bold; }}
  .tarjeta .t {{ font-size: 12px; color: #555; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e2e2e2; vertical-align: top; font-size: 13px; }}
  th {{ background: #eceff3; font-size: 12px; text-transform: uppercase; letter-spacing: .03em; }}
  .semaforo {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; white-space: nowrap; }}
  .req {{ font-weight: bold; }}
  .justif {{ color: #333; }}
  .evidencia {{ color: #555; font-size: 12px; }}
  footer {{ margin-top: 20px; color: #777; font-size: 12px; }}
</style>
</head>
<body>
  <h1>Tablero de cumplimiento del PIMS — Agente de cumplimiento PIMS (Grupo 6)</h1>
  <div class="subtitulo">Generado {generado} a partir de {archivo_evaluacion}</div>

  <div class="resumen">
    <div class="tarjeta"><div class="n">{requisitos_evaluados}</div><div class="t">Requisitos evaluados</div></div>
    <div class="tarjeta" style="border-left:4px solid {color_cubierto}"><div class="n">{cubiertos}</div><div class="t">Cubiertos</div></div>
    <div class="tarjeta" style="border-left:4px solid {color_parcial}"><div class="n">{parciales}</div><div class="t">Parciales</div></div>
    <div class="tarjeta" style="border-left:4px solid {color_sin_evidencia}"><div class="n">{sin_evidencia}</div><div class="t">Sin evidencia</div></div>
  </div>

  <table>
    <thead>
      <tr><th>Requisito</th><th>Nombre</th><th>Estado</th><th>Prioridad</th><th>Justificación</th><th>Evidencia citada</th></tr>
    </thead>
    <tbody>
{filas}
    </tbody>
  </table>

  <footer>
    {nota_documentos_no_citados}
    Este tablero es preliminar: la validación de cada hallazgo corresponde al Oficial de Protección de Datos
    (ISO/IEC 27701:2025 §9.2; ISO 19011).
  </footer>
</body>
</html>
"""

FILA = """      <tr style="background:{fondo}">
        <td class="req">{requisito_id}</td>
        <td>{nombre}</td>
        <td><span class="semaforo" style="background:{color};color:#fff">{etiqueta}</span></td>
        <td>{prioridad}</td>
        <td class="justif">{justificacion}</td>
        <td class="evidencia">{evidencia}</td>
      </tr>"""


def main():
    ap = argparse.ArgumentParser(description="Genera un tablero web estatico (semaforo) a partir de resumen.json.")
    ap.add_argument("--resumen", required=True, help="resumen.json escrito por generar_matriz_cumplimiento.py")
    ap.add_argument("--salida", default="tablero.html", help="ruta del HTML a escribir")
    args = ap.parse_args()

    with open(args.resumen, encoding="utf-8") as f:
        resumen = json.load(f)

    filas_html = []
    for r in resumen["resultados"]:
        estado = r["estado"]
        evidencia = ", ".join(r["evidencia_citada"]) if r["evidencia_citada"] else "—"
        prioridad = (r["prioridad_atencion"] or "-").upper() if r["prioridad_atencion"] else "-"
        filas_html.append(FILA.format(
            fondo=FONDO_POR_ESTADO[estado],
            requisito_id=html.escape(r["requisito_id"]),
            nombre=html.escape(r["nombre"]),
            color=COLOR_POR_ESTADO[estado],
            etiqueta=ETIQUETA_POR_ESTADO[estado],
            prioridad=html.escape(prioridad),
            justificacion=html.escape(r["justificacion"]),
            evidencia=html.escape(evidencia),
        ))

    nota_no_citados = ""
    no_citados = resumen.get("documentos_no_citados")
    if no_citados:
        nota_no_citados = ("Documentos del inventario no citados como evidencia por ningún requisito: %s. "
                            % html.escape(", ".join(no_citados)))

    pagina = PLANTILLA.format(
        generado=html.escape(resumen["generado"]),
        archivo_evaluacion=html.escape(resumen["archivo_evaluacion"]),
        requisitos_evaluados=resumen["requisitos_evaluados"],
        cubiertos=resumen["cubiertos"], parciales=resumen["parciales"], sin_evidencia=resumen["sin_evidencia"],
        color_cubierto=COLOR_POR_ESTADO["CUBIERTO"], color_parcial=COLOR_POR_ESTADO["PARCIAL"],
        color_sin_evidencia=COLOR_POR_ESTADO["SIN_EVIDENCIA"],
        filas="\n".join(filas_html),
        nota_documentos_no_citados=nota_no_citados,
    )

    with open(args.salida, "w", encoding="utf-8") as f:
        f.write(pagina)

    print("Tablero escrito en %s" % args.salida)


if __name__ == "__main__":
    main()
