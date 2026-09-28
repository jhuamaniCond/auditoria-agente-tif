# -*- coding: utf-8 -*-
"""
generar_evaluacion_demo.py
===============================================================================
Escribe evaluacion_demo.csv: el veredicto que produjo el asistente al LEER
los fragmentos recuperados por RAG sobre documentos_empresa_demo.csv (ver
recuperar_fragmentos.py). Es una foto congelada de un juicio real hecho una
vez, no un calculo — por eso este script solo transcribe el resultado en vez
de "recalcularlo": la lectura y el juicio de suficiencia no son deterministas
(ver SKILL.md, paso 4), y guardarlos aparte permite que la demostracion sea
reproducible sin volver a invocar al modelo cada vez.

Para una evaluacion nueva (con otro corpus, u otra pasada sobre el mismo),
pide al asistente que lea entregable-1/demo/fragmentos_recuperados.json y
escriba su propio evaluacion.csv siguiendo el paso 4 del SKILL.md.

Uso:
  python generar_evaluacion_demo.py --salida evaluacion_demo.csv
===============================================================================
"""

import argparse
import csv

COLUMNAS = ["requisito_id", "estado", "evidencia_citada", "justificacion"]

EVALUACION = [
    ("REQ-01", "CUBIERTO", "DOC-01-01",
     "La Política de Privacidad v3.0 está aprobada por Resolución Rectoral N.º 045-2026 (10/03/2026), vigente y con alcance a personal, estudiantes y terceros."),
    ("REQ-02", "SIN_EVIDENCIA", "",
     "Ninguno de los documentos recuperados (política de privacidad, política de teletrabajo, procedimiento de incidentes) trata una evaluación de impacto en la privacidad; no hay evidencia de una PIA para ningún proceso."),
    ("REQ-03", "PARCIAL", "DOC-02-01;DOC-02-02;DOC-02-03",
     "El RAT (dic. 2025) documenta 12 actividades de tratamiento con finalidad, base legal y plazo de conservación, pero el propio documento (DOC-02-03) reconoce que no incluye los convenios interinstitucionales ni la plataforma de pagos de 2026: está desactualizado respecto a la operación actual."),
    ("REQ-04", "CUBIERTO", "DOC-03-02",
     "La matriz de bases legales (15/01/2026) documenta la base legal por finalidad (contrato educativo, consentimiento, obligación tributaria) conforme al Reglamento de la Ley 29733."),
    ("REQ-05", "PARCIAL", "DOC-01-03",
     "La política de privacidad reconoce los derechos ARCO de los titulares, pero solo los enuncia: no define un procedimiento operativo (plazos, forma de solicitud, responsable de trámite) para atenderlos, que es lo que exige el requisito."),
    ("REQ-06", "CUBIERTO", "DOC-04-01;DOC-04-02",
     "El manual de control de accesos (01/02/2026) define la matriz de acceso por rol a los recursos con datos personales bajo mínimo privilegio, con roles y recursos explícitos."),
    ("REQ-07", "PARCIAL", "DOC-04-03",
     "El manual exige contraseñas de al menos 10 caracteres con cambio cada 90 días, pero el propio texto indica que no contempla autenticación multifactor para las cuentas con acceso a datos sensibles (expediente médico, datos de pago)."),
    ("REQ-08", "SIN_EVIDENCIA", "",
     "Ninguno de los documentos recuperados corresponde a un reporte de análisis periódico de accesos a datos personales; el manual de accesos define permisos, pero no describe una revisión periódica de logs."),
    ("REQ-09", "CUBIERTO", "DOC-05-01;DOC-05-02;DOC-05-03",
     "El procedimiento de gestión de incidentes (v2, 01/09/2025) define fases, responsables, y exige informar a la Oficina de Protección de Datos dentro de 24 horas cuando el incidente involucre datos personales."),
    ("REQ-10", "CUBIERTO", "DOC-05-04",
     "El mismo procedimiento registra 2 incidentes de privacidad en el primer semestre de 2026, evaluados por el DPO, con uno notificado a la ANPD dentro del plazo legal."),
    ("REQ-11", "PARCIAL", "DOC-07-01;DOC-07-02",
     "Existe un plan de capacitación en seguridad de la información 2026, pero el propio plan indica que no incluye un módulo específico de protección de datos personales ni registra fechas de ejecución o asistencia."),
    ("REQ-12", "PARCIAL", "DOC-06-01;DOC-06-03",
     "El contrato con el proveedor de nube (backups) está vigente y define niveles de servicio, pero el propio contrato indica que no incluye cláusula de confidencialidad ni de protección de datos personales para el personal del proveedor, ni trata la subcontratación."),
    ("REQ-13", "SIN_EVIDENCIA", "",
     "Ninguno de los documentos recuperados corresponde a un informe o acta de auditoría interna del PIMS."),
    ("REQ-14", "CUBIERTO", "DOC-09-01;DOC-09-02",
     "El registro de acciones correctivas (10/04/2026) documenta 3 no conformidades de la revisión 2025 con causa raíz, acción, responsable y verificación de eficacia, las tres cerradas."),
    ("REQ-15", "CUBIERTO", "DOC-08-01;DOC-08-02",
     "El reporte de revisión de retención (01/07/2026) identifica campos innecesarios a eliminar del formulario de matrícula y confirma los plazos de retención vigentes."),
]


def main():
    ap = argparse.ArgumentParser(description="Escribe la evaluacion de referencia (juicio del asistente) para la demo.")
    ap.add_argument("--salida", default="evaluacion_demo.csv", help="ruta del CSV a escribir")
    args = ap.parse_args()

    with open(args.salida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUMNAS)
        for fila in EVALUACION:
            escritor.writerow(fila)

    print("Evaluacion de referencia (%d requisitos) escrita en %s" % (len(EVALUACION), args.salida))


if __name__ == "__main__":
    main()
