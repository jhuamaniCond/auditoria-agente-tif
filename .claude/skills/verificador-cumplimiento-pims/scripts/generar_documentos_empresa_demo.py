# -*- coding: utf-8 -*-
"""
generar_documentos_empresa_demo.py
===============================================================================
Genera el corpus documental de una institucion educativa ficticia, para
demostrar el skill "verificador-cumplimiento-pims" con RAG. No usa datos
reales de ninguna institucion. Solo libreria estandar de Python (>= 3.8).

A diferencia de un inventario de evidencias ya resumido, esto es lo que
realmente tendria una organizacion: un puñado de documentos largos (no uno
por requisito), cada uno con varios parrafos (separados por linea en blanco,
que son los "chunks" que indexa indexar_documentos.py). Varios documentos
cubren un requisito con huecos intencionales dentro del propio texto (una
politica que declara derechos ARCO pero no define el procedimiento, un
contrato sin clausula de confidencialidad, un manual de accesos sin
autenticacion multifactor) en vez de que falte el documento completo — es el
patron que pidio la catedra para que la demo sea convincente.

Uso:
  python generar_documentos_empresa_demo.py --salida documentos_empresa_demo.csv
===============================================================================
"""

import argparse
import csv

COLUMNAS = ["id_documento", "tipo", "fecha_documento", "responsable", "ubicacion", "contenido"]

DOCUMENTOS = [
    ("DOC-01", "politica", "2026-03-10", "Oficial de Protección de Datos",
     "intranet/politicas/privacidad_v3.pdf",
     "Política de Privacidad de la Información, versión 3.0, aprobada por Resolución Rectoral N.º 045-2026 el 10 de marzo de 2026. Aplica a todo el personal, estudiantes y terceros que traten datos personales en nombre de la institución.\n\n"
     "Principios rectores: legalidad, consentimiento informado, finalidad, proporcionalidad, calidad, seguridad y disponibilidad de los datos, conforme a la Ley N.º 29733 y su reglamento.\n\n"
     "La institución reconoce a los titulares los derechos de acceso, rectificación, cancelación y oposición sobre sus datos personales, ejercibles mediante solicitud a la Oficina de Protección de Datos.\n\n"
     "Los datos personales de estudiantes se conservarán durante la relación académica y hasta cinco años después de concluida, salvo obligación legal de conservación mayor.\n\n"
     "Toda modificación a la presente política requiere aprobación del Comité de Privacidad y se comunica a la comunidad universitaria dentro de los 30 días siguientes."),

    ("DOC-02", "registro", "2025-12-01", "Oficial de Protección de Datos",
     "drive/pims/rat_2025.xlsx",
     "Registro de Actividades de Tratamiento de Datos Personales (RAT), versión de diciembre de 2025. Documenta doce actividades de tratamiento: matrícula, gestión académica, bienestar universitario, tesorería, biblioteca, egresados, admisión, becas, convenios, movilidad estudiantil, investigación y comunicaciones institucionales.\n\n"
     "Para cada actividad se registra: finalidad, categorías de datos, base legal, plazo de conservación y áreas responsables.\n\n"
     "Nota de la Oficina de Protección de Datos: este registro no incluye los tres convenios interinstitucionales firmados en el primer semestre de 2026 ni la nueva plataforma de pagos en línea; se recomienda actualizarlo antes del cierre del año."),

    ("DOC-03", "registro", "2026-01-15", "Asesoría Legal",
     "drive/pims/bases_legales.xlsx",
     "Matriz de bases legales por finalidad de tratamiento, elaborada por Asesoría Legal el 15 de enero de 2026, vigente para el periodo 2026.\n\n"
     "Matrícula y gestión académica: base legal de ejecución de contrato educativo. Becas y bienestar: consentimiento expreso del titular o representante legal. Tesorería y cobranza: ejecución contractual y obligación legal tributaria. Investigación con datos de egresados: consentimiento informado y específico.\n\n"
     "La matriz se revisa anualmente o cuando se incorpore una nueva finalidad de tratamiento no contemplada."),

    ("DOC-04", "procedimiento", "2026-02-01", "Seguridad TI",
     "drive/pims/manual_acceso.pdf",
     "Manual de control de accesos y gestión de identidad, aprobado el 1 de febrero de 2026 por Seguridad TI. Define la matriz de acceso por rol a los recursos de datos personales: ficha de estudiante, expediente académico, expediente médico, notas y datos de pago, bajo el principio de mínimo privilegio.\n\n"
     "Los roles docente, administrativo, bienestar y tesorería tienen acceso restringido a los recursos que su función requiere. El rol oficial de privacidad y el rol sistema tienen acceso completo para fines de administración y auditoría.\n\n"
     "Requisitos de contraseña: longitud mínima de 10 caracteres, combinación de mayúsculas, minúsculas y números, cambio obligatorio cada 90 días. El manual no contempla, a la fecha, un mecanismo de autenticación multifactor para las cuentas con acceso a datos sensibles (expediente médico, datos de pago)."),

    ("DOC-05", "procedimiento", "2025-09-01", "Oficial de Protección de Datos",
     "intranet/procedimientos/incidentes_v2.pdf",
     "Procedimiento de gestión de incidentes de seguridad de la información, versión 2, del 1 de septiembre de 2025. Aplica a incidentes que afecten la confidencialidad, integridad o disponibilidad de los sistemas institucionales.\n\n"
     "Fases del procedimiento: detección y reporte, contención, erradicación, recuperación y lecciones aprendidas. El responsable de cada fase es el equipo de Seguridad TI, con escalamiento a la Dirección de Sistemas.\n\n"
     "Cuando el incidente involucre datos personales, se debe informar a la Oficina de Protección de Datos dentro de las 24 horas de detectado, para que esta evalúe si corresponde notificar a la Autoridad Nacional de Protección de Datos Personales dentro del plazo legal.\n\n"
     "Registro de incidentes 2026 (primer semestre): 2 incidentes menores relacionados con datos personales, ambos evaluados por el DPO; uno de ellos fue notificado a la ANPD dentro del plazo, con constancia adjunta."),

    ("DOC-06", "contrato", "2025-06-01", "Seguridad TI",
     "drive/pims/contrato_nube.pdf",
     "Contrato de prestación de servicios de almacenamiento en la nube y respaldo de información (backups institucionales), suscrito el 1 de junio de 2025 con el proveedor CloudSeguro S.A.\n\n"
     "El proveedor se compromete a mantener la disponibilidad del servicio conforme al Anexo de Niveles de Servicio (SLA), y a notificar cualquier interrupción mayor a 4 horas dentro de las 24 horas siguientes.\n\n"
     "El contrato no incluye una cláusula específica de confidencialidad ni de protección de datos personales para el personal del proveedor que tenga acceso a la información institucional; tampoco define el tratamiento en caso de subcontratación (subencargados)."),

    ("DOC-07", "capacitacion", "2025-11-10", "Recursos Humanos",
     "drive/pims/plan_capacitacion.docx",
     "Plan de capacitación en seguridad de la información 2026, elaborado por Recursos Humanos el 10 de noviembre de 2025. Contempla sesiones sobre uso seguro de contraseñas, phishing y manejo de equipos institucionales, dirigidas a todo el personal administrativo y docente.\n\n"
     "El plan no incluye, a la fecha de este documento, un módulo específico sobre protección de datos personales ni sobre las obligaciones del personal frente a la Ley N.º 29733; tampoco registra fechas de ejecución ni asistencia."),

    ("DOC-08", "reporte", "2026-07-01", "Oficial de Protección de Datos",
     "drive/pims/revision_retencion_2026.pdf",
     "Reporte de revisión de campos de datos personales recogidos en los formularios institucionales y de los plazos de retención aplicados, del 1 de julio de 2026.\n\n"
     "Se identificaron 4 campos innecesarios en el formulario de matrícula (estado civil de los padres, religión, tipo de sangre, redes sociales) que se eliminarán en la siguiente actualización. Se confirmaron los plazos de retención: 5 años para expedientes académicos, 2 años para datos de postulantes no admitidos."),

    ("DOC-09", "registro", "2026-04-10", "Oficial de Protección de Datos",
     "drive/pims/acciones_correctivas.xlsx",
     "Registro de acciones correctivas del Sistema de Gestión de Privacidad de la Información, actualizado el 10 de abril de 2026.\n\n"
     "Incluye 3 no conformidades detectadas en la revisión de 2025: (1) falta de registro de capacitaciones, (2) matriz de acceso desactualizada, (3) ausencia de plazos de retención documentados. Para cada una se registra causa raíz, acción correctiva, responsable y verificación de eficacia; las tres están cerradas y verificadas."),

    # Documentos reales de la institucion, sin relacion con el checklist de privacidad
    # (sirven para comprobar que el RAG no cita evidencia irrelevante solo porque
    # comparte alguna palabra suelta, como "politica" o "reporte").
    ("DOC-10", "politica", "2026-02-01", "Recursos Humanos",
     "intranet/politicas/teletrabajo.pdf",
     "Política de teletrabajo y trabajo remoto, aprobada el 1 de febrero de 2026 por Recursos Humanos. Regula horarios flexibles, uso de equipos institucionales fuera de las instalaciones y evaluación de desempeño remoto. No hace referencia al tratamiento de datos personales ni a la Ley N.º 29733."),

    ("DOC-11", "reporte", "2026-06-01", "Marketing",
     "drive/marketing/satisfaccion_2026.pdf",
     "Reporte de satisfacción del cliente 2026, elaborado por el área de Marketing a partir de encuestas a estudiantes y padres de familia sobre la calidad percibida del servicio académico y administrativo. No aborda aspectos de protección de datos personales."),
]


def main():
    ap = argparse.ArgumentParser(description="Genera el corpus documental de la empresa demo (sin clasificar, sin RAG aplicado).")
    ap.add_argument("--salida", default="documentos_empresa_demo.csv", help="ruta del CSV a escribir")
    args = ap.parse_args()

    with open(args.salida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUMNAS)
        for fila in DOCUMENTOS:
            escritor.writerow(fila)

    print("%d documentos escritos en %s (2 de ellos, DOC-10 y DOC-11, no tratan protección de datos personales)"
          % (len(DOCUMENTOS), args.salida))


if __name__ == "__main__":
    main()
