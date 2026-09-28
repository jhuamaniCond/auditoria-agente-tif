# -*- coding: utf-8 -*-
"""
Pruebas del pipeline del skill "verificador-cumplimiento-pims" (solo libreria
estandar: unittest, sin pytest ni dependencias externas).

Ejecutar desde la raiz del repositorio:
    python -m unittest discover -s tests -v
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(RAIZ, ".claude", "skills", "verificador-cumplimiento-pims")
SCRIPTS = os.path.join(SKILL, "scripts")
REQUISITOS = os.path.join(SKILL, "requisitos.json")


def cargar_modulo(nombre):
    ruta = os.path.join(SCRIPTS, nombre + ".py")
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


indexar_mod = cargar_modulo("indexar_documentos")
recuperar_mod = cargar_modulo("recuperar_fragmentos")
matriz_mod = cargar_modulo("generar_matriz_cumplimiento")
tablero_mod = cargar_modulo("generar_tablero")


def run_script(nombre, *args):
    cmd = [sys.executable, os.path.join(SCRIPTS, nombre + ".py")] + list(args)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)


class TestTroceo(unittest.TestCase):
    def test_linea_en_blanco_unix(self):
        self.assertEqual(indexar_mod.trocear("uno\n\ndos"), ["uno", "dos"])

    def test_linea_en_blanco_windows(self):
        self.assertEqual(indexar_mod.trocear("uno\r\n\r\ndos"), ["uno", "dos"])

    def test_linea_en_blanco_con_espacios(self):
        self.assertEqual(indexar_mod.trocear("uno\n \t \ndos"), ["uno", "dos"])

    def test_vacio(self):
        self.assertEqual(indexar_mod.trocear("   "), [])


class TestCargarDocumentos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _escribir(self, nombre, texto, encoding="utf-8"):
        ruta = os.path.join(self.tmp.name, nombre)
        with open(ruta, "w", encoding=encoding, newline="") as f:
            f.write(texto)
        return ruta

    def test_bom_no_rompe_columnas(self):
        ruta = self._escribir(
            "bom.csv",
            "id_documento,tipo,fecha_documento,responsable,ubicacion,contenido\n"
            'DOC-01,politica,2026-01-01,DPO,x,"parrafo uno\n\nparrafo dos"\n',
            encoding="utf-8-sig",
        )
        docs = indexar_mod.cargar_documentos(ruta)
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(indexar_mod.indexar(docs)), 2)

    def test_crlf_no_colapsa_parrafos(self):
        ruta = self._escribir(
            "crlf.csv",
            "id_documento,tipo,fecha_documento,responsable,ubicacion,contenido\r\n"
            'DOC-01,politica,2026-01-01,DPO,x,"parrafo uno\r\n\r\nparrafo dos\r\n"\r\n',
        )
        docs = indexar_mod.cargar_documentos(ruta)
        self.assertEqual(len(indexar_mod.indexar(docs)), 2)

    def test_fila_corta_error_claro(self):
        ruta = self._escribir(
            "corta.csv",
            "id_documento,tipo,fecha_documento,responsable,ubicacion,contenido\nDOC-01,politica\n",
        )
        with self.assertRaises(SystemExit) as cm:
            indexar_mod.cargar_documentos(ruta)
        self.assertIn("faltan valores", str(cm.exception))

    def test_archivo_inexistente_error_claro(self):
        with self.assertRaises(SystemExit) as cm:
            indexar_mod.cargar_documentos(os.path.join(self.tmp.name, "noexiste.csv"))
        self.assertIn("No se pudo abrir", str(cm.exception))


class TestRecuperacion(unittest.TestCase):
    CHUNKS = [{
        "id_documento": "DOC-01", "chunk_id": "DOC-01-01", "tipo": "registro",
        "fecha_documento": "2026-01-01", "responsable": "DPO", "ubicacion": "x",
        "texto": "Autorizacion expresa del usuario registrada al momento de la matricula.",
    }]
    REQUISITO = {
        "nombre": "Consentimiento del titular",
        "descripcion": "Evidencia del consentimiento informado del titular para el tratamiento de datos",
        "tipo_evidencia_esperada": ["registro"],
    }

    def test_sinonimos_recuperan_el_documento(self):
        res = recuperar_mod.recuperar(self.CHUNKS, {"REQ-01": self.REQUISITO}, 2, 0.08, usar_sinonimos=True)
        self.assertTrue(res["REQ-01"], "con expansion de sinonimos el documento deberia recuperarse")

    def test_sin_expansion_no_recupera_nada(self):
        res = recuperar_mod.recuperar(self.CHUNKS, {"REQ-01": self.REQUISITO}, 2, 0.08, usar_sinonimos=False)
        self.assertEqual(res["REQ-01"], [])

    def test_consulta_tolera_requisito_incompleto(self):
        q = recuperar_mod.construir_consulta("REQ-01", {"nombre": "Politica"})
        self.assertEqual(q, "Politica")


class TestMatrizValidaciones(unittest.TestCase):
    CFG = {
        "requisitos": {
            "REQ-01": {
                "nombre": "Politica de privacidad", "clausula": "ISO/IEC 27701:2025 5.2",
                "descripcion": "Politica aprobada", "tipo_evidencia_esperada": ["politica"],
                "vigencia_max_dias": 365, "criticidad": "alta",
            },
            "REQ-02": {
                "nombre": "Auditoria interna", "clausula": "ISO/IEC 27701:2025 9.2",
                "descripcion": "Auditoria interna del PIMS", "tipo_evidencia_esperada": ["reporte"],
                "vigencia_max_dias": 365, "criticidad": "media",
            },
        },
        "prioridad": {"orden_criticidad": ["baja", "media", "alta"], "bajar_un_nivel_si_parcial": True},
    }
    MAPA = {
        "DOC-01-01": {"id_documento": "DOC-01", "tipo": "politica", "fecha_documento": "2020-01-01"},
        "DOC-02-01": {"id_documento": "DOC-02", "tipo": "reporte", "fecha_documento": "2026-01-01"},
    }

    def _eval(self, req_id, estado, citas):
        return {req_id: {"requisito_id": req_id, "estado": estado,
                         "evidencia_citada": citas, "justificacion": "j"}}

    def test_chunk_id_inventado_es_error(self):
        ev = self._eval("REQ-01", "CUBIERTO", ["DOC-99-01"])
        with self.assertRaises(SystemExit) as cm:
            matriz_mod.validar_citas_y_advertir(ev, self.CFG, self.MAPA, date(2026, 1, 1))
        self.assertIn("NO existe en el indice", str(cm.exception))

    def test_veredicto_sin_cita_es_error(self):
        ev = self._eval("REQ-01", "CUBIERTO", [])
        with self.assertRaises(SystemExit) as cm:
            matriz_mod.validar_citas_y_advertir(ev, self.CFG, self.MAPA, date(2026, 1, 1))
        self.assertIn("no cita ningun chunk_id", str(cm.exception))

    def test_vigencia_vencida_es_advertencia_no_error(self):
        ev = self._eval("REQ-01", "CUBIERTO", ["DOC-01-01"])
        avisos = matriz_mod.validar_citas_y_advertir(ev, self.CFG, self.MAPA, date(2026, 1, 1))
        self.assertEqual(len(avisos["REQ-01"]), 1)
        self.assertIn("supera la vigencia maxima", avisos["REQ-01"][0])

    def test_sin_indice_no_valida_pero_advierte_tipo_no(self):
        ev = self._eval("REQ-01", "CUBIERTO", ["DOC-99-01"])
        avisos = matriz_mod.validar_citas_y_advertir(ev, self.CFG, None, date(2026, 1, 1))
        self.assertEqual(avisos, {})

    def test_prioridad_usa_orden_del_json(self):
        orden = matriz_mod.validar_config_requisitos(self.CFG)
        self.assertEqual(matriz_mod.prioridad_atencion("alta", "PARCIAL", self.CFG["prioridad"], orden), "media")
        self.assertEqual(matriz_mod.prioridad_atencion("media", "SIN_EVIDENCIA", self.CFG["prioridad"], orden), "media")
        self.assertIsNone(matriz_mod.prioridad_atencion("alta", "CUBIERTO", self.CFG["prioridad"], orden))

    def test_criticidad_desconocida_es_error(self):
        cfg = json.loads(json.dumps(self.CFG))
        cfg["requisitos"]["REQ-01"]["criticidad"] = "critica"
        with self.assertRaises(SystemExit) as cm:
            matriz_mod.validar_config_requisitos(cfg)
        self.assertIn("no esta en orden_criticidad", str(cm.exception))

    def test_documentos_no_citados(self):
        res = [{"evidencia_citada": ["DOC-02-01"]}]
        self.assertEqual(matriz_mod.documentos_no_citados(self.MAPA, res), ["DOC-01"])
        self.assertIsNone(matriz_mod.documentos_no_citados(None, res))


class TestTablero(unittest.TestCase):
    def test_estado_inesperado_es_error(self):
        with self.assertRaises(SystemExit) as cm:
            tablero_mod.fila_html({"requisito_id": "REQ-01", "nombre": "x", "estado": "MAS_O_MENOS",
                                   "justificacion": "j"})
        self.assertIn("estado inesperado", str(cm.exception))


class TestDemoExtremoADosExtremos(unittest.TestCase):
    """Reproduce la demo completa (pipeline CLI) y verifica el resultado prometido."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t = cls.tmp.name
        p = lambda n: os.path.join(t, n)
        r = run_script("generar_documentos_empresa_demo", "--salida", p("docs.csv"))
        assert r.returncode == 0, r.stderr
        r = run_script("indexar_documentos", "--documentos", p("docs.csv"), "--salida", p("indice.json"))
        assert r.returncode == 0, r.stderr
        cls.indice = r
        r = run_script("recuperar_fragmentos", "--indice", p("indice.json"),
                       "--requisitos", REQUISITOS, "--salida", p("frag.json"))
        assert r.returncode == 0, r.stderr
        r = run_script("generar_evaluacion_demo", "--salida", p("eval.csv"))
        assert r.returncode == 0, r.stderr
        cls.matriz = run_script("generar_matriz_cumplimiento", "--evaluacion", p("eval.csv"),
                                "--requisitos", REQUISITOS, "--indice", p("indice.json"),
                                "--salida", p("salida"), "--fecha-revision", "2026-07-01")
        cls.resumen_ruta = p(os.path.join("salida", "resumen.json"))
        cls.tablero = run_script("generar_tablero", "--resumen", cls.resumen_ruta,
                                 "--salida", p("tablero.html"))
        cls.tablero_html = p("tablero.html")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_matriz_ok(self):
        self.assertEqual(self.matriz.returncode, 0, self.matriz.stdout + self.matriz.stderr)

    def test_resultados_prometidos(self):
        with open(self.resumen_ruta, encoding="utf-8") as f:
            resumen = json.load(f)
        self.assertEqual(resumen["requisitos_evaluados"], 15)
        self.assertEqual((resumen["cubiertos"], resumen["parciales"], resumen["sin_evidencia"]), (7, 5, 3))
        self.assertEqual(resumen["documentos_no_citados"], ["DOC-10", "DOC-11"])
        self.assertTrue(resumen["citas_validadas"])

    def test_29_fragmentos_indexados(self):
        with open(os.path.join(self.tmp.name, "indice.json"), encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["chunks"]), 29)

    def test_hallazgos_por_brecha(self):
        esperados = {"REQ-02", "REQ-03", "REQ-05", "REQ-07", "REQ-08", "REQ-11", "REQ-12", "REQ-13"}
        generados = {n for n in os.listdir(os.path.join(self.tmp.name, "salida")) if n.startswith("hallazgo_")}
        self.assertEqual(generados, {"hallazgo_%s.md" % r for r in esperados})

    def test_tablero_responsive(self):
        self.assertEqual(self.tablero.returncode, 0, self.tablero.stdout + self.tablero.stderr)
        with open(self.tablero_html, encoding="utf-8") as f:
            html = f.read()
        self.assertIn('name="viewport"', html)
        self.assertIn("overflow-x: auto", html)
        self.assertIn("SIN EVIDENCIA", html)


if __name__ == "__main__":
    unittest.main()
