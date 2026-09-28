# -*- coding: utf-8 -*-
"""
generar_figuras.py
===============================================================================
Genera las figuras del informe del entregable 1 (Grupo 6) que no son captura
de pantalla: el diagrama de arquitectura/flujo del skill
`verificador-cumplimiento-pims`. Se dibuja con Pillow (cajas y flechas
simples, sin sombras ni degradados) en vez de dejar un prompt para una
herramienta externa, porque es reproducible y no depende de un servicio de
generación de imágenes.

Requisito: Pillow (`pip install pillow`).

Uso:
    python generar_figuras.py
===============================================================================
"""

import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "figuras")

NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)

FUENTES_CANDIDATAS = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _fuente(tamano, negrita=False):
    candidatos = [f for f in FUENTES_CANDIDATAS if ("bd" in f) == negrita]
    candidatos += FUENTES_CANDIDATAS
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tamano)
    return ImageFont.load_default()


F_TEXTO = _fuente(22)
F_TEXTO_CHICO = _fuente(18)


def _texto_multilinea(draw, centro_x, centro_y, texto, fuente):
    lineas = texto.split("\n")
    alto_linea = fuente.size + 6
    alto_total = alto_linea * len(lineas)
    y = centro_y - alto_total / 2
    for linea in lineas:
        bbox = draw.textbbox((0, 0), linea, font=fuente)
        ancho = bbox[2] - bbox[0]
        draw.text((centro_x - ancho / 2, y), linea, font=fuente, fill=NEGRO)
        y += alto_linea


def _caja(draw, centro_x, centro_y, ancho, alto, texto, fuente=None, grosor=2):
    x0, y0 = centro_x - ancho / 2, centro_y - alto / 2
    x1, y1 = centro_x + ancho / 2, centro_y + alto / 2
    draw.rectangle([x0, y0, x1, y1], outline=NEGRO, width=grosor, fill=BLANCO)
    _texto_multilinea(draw, centro_x, centro_y, texto, fuente or F_TEXTO)
    return (centro_x, centro_y, ancho, alto)


def _punto_borde(caja, hacia):
    cx, cy, ancho, alto = caja
    hx, hy = hacia
    if abs(hx - cx) * alto > abs(hy - cy) * ancho:
        x = cx + (ancho / 2 if hx > cx else -ancho / 2)
        y = cy
    else:
        y = cy + (alto / 2 if hy > cy else -alto / 2)
        x = cx
    return (x, y)


def _flecha(draw, caja_origen, caja_destino, grosor=2, tam_punta=10):
    origen = _punto_borde(caja_origen, (caja_destino[0], caja_destino[1]))
    destino = _punto_borde(caja_destino, (caja_origen[0], caja_origen[1]))
    draw.line([origen, destino], fill=NEGRO, width=grosor)

    import math
    angulo = math.atan2(destino[1] - origen[1], destino[0] - origen[0])
    x, y = destino
    izq = (x - tam_punta * math.cos(angulo - 0.5), y - tam_punta * math.sin(angulo - 0.5))
    der = (x - tam_punta * math.cos(angulo + 0.5), y - tam_punta * math.sin(angulo + 0.5))
    draw.polygon([destino, izq, der], fill=NEGRO)


def figura_arquitectura():
    ancho_lienzo, alto_lienzo = 1600, 1180
    img = Image.new("RGB", (ancho_lienzo, alto_lienzo), BLANCO)
    draw = ImageDraw.Draw(img)

    c1 = _caja(draw, 740, 60, 660, 80, "Usuario / DPO aporta\ndocumentos_empresa_demo.csv (contenido real)")
    c2 = _caja(draw, 740, 190, 620, 90, "indexar_documentos.py\nRAG paso 1: trocea en fragmentos (chunks)")
    c3req = _caja(draw, 1330, 320, 380, 90, "requisitos.json\n(checklist, arma la consulta)")
    c3 = _caja(draw, 740, 320, 620, 90, "recuperar_fragmentos.py\nRAG paso 2: TF-IDF léxico, por documento")
    c4 = _caja(draw, 740, 460, 620, 100, "AuditorPIMS LEE el contenido y decide\n(paso 4 — modelo, no determinista)")
    c5 = _caja(draw, 740, 600, 620, 90, "generar_matriz_cumplimiento.py\n(formatea, determinista)")
    c6a = _caja(draw, 460, 740, 460, 90, "resumen.json +\nhallazgo_<REQ-ID>.md")
    c6b = _caja(draw, 1020, 740, 460, 90, "generar_tablero.py\ntablero.html (semáforo)")
    c7iso = _caja(draw, 1330, 890, 380, 100, "conocimiento/iso27701.md\n(controles 27701/27002,\nLey 29733)")
    c7 = _caja(draw, 740, 890, 620, 100, "AuditorPIMS interpreta\ny prioriza los hallazgos")
    c8 = _caja(draw, 740, 1050, 680, 90, "Oficial de Protección de Datos\nvalida la lectura y decide el tratamiento")

    _flecha(draw, c1, c2)
    _flecha(draw, c2, c3)
    _flecha(draw, c3req, c3)
    _flecha(draw, c3, c4)
    _flecha(draw, c4, c5)
    _flecha(draw, c5, c6a)
    _flecha(draw, c5, c6b)
    _flecha(draw, c6a, c7)
    _flecha(draw, c6b, c7)
    _flecha(draw, c7iso, c7)
    _flecha(draw, c7, c8)

    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, "arquitectura.png")
    img.save(ruta)
    print("Figura escrita en %s" % ruta)


if __name__ == "__main__":
    figura_arquitectura()
