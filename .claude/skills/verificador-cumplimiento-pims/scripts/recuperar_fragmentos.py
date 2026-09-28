# -*- coding: utf-8 -*-
"""
recuperar_fragmentos.py
===============================================================================
Paso 2 del RAG del skill "verificador-cumplimiento-pims": para cada uno de
los 15 requisitos de requisitos.json, recupera los fragmentos (chunks) del
indice mas relevantes (TF-IDF + similitud coseno, sin embeddings ni
librerias externas — solo re, math, json de la libreria estandar).

La consulta de cada requisito se arma con su nombre, descripcion y tipo de
evidencia esperada (son las palabras que un auditor usaria para buscar esa
evidencia). El resultado (fragmentos_recuperados.json) es lo que despues LEE
el modelo (no el corpus completo) para decidir si el requisito esta
cubierto — eso es lo que hace de esto un RAG: se recupera antes de generar.

La recuperacion es por DOCUMENTO, no por chunk suelto: se puntua cada chunk,
pero el ranking usa el mejor puntaje de cada documento y luego se devuelven
TODOS los chunks de los documentos mejor rankeados. Esto evita perder el
parrafo que revela un hueco (p. ej. "este registro no incluye los convenios
de 2026") solo porque ese parrafo comparte menos palabras clave con la
consulta que el parrafo introductorio del mismo documento.

La consulta tambien se expande con un glosario de equivalencias del dominio
(GRUPOS_SINONIMOS): TF-IDF falla cuando el requisito dice "consentimiento del
titular" y el documento dice "autorizacion expresa del usuario" (comparten
cero palabras). La expansion se aplica SOLO a la consulta de cada requisito,
nunca a los documentos indexados: el indice queda intacto, el efecto es facil
de explicar y se puede desactivar con --sin-sinonimos para comparar.

Uso:
  python recuperar_fragmentos.py --indice indice_chunks.json --requisitos requisitos.json --salida fragmentos_recuperados.json
  python recuperar_fragmentos.py --indice indice_chunks.json --requisitos requisitos.json --top-k 3 --umbral 0.05
===============================================================================
"""

import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict

PATRON_PALABRA = re.compile(r"[a-zA-ZÀ-ÿ0-9]+")

# Palabras sin valor discriminante para la busqueda (stopwords minimas en español).
PALABRAS_VACIAS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "u",
    "a", "al", "del", "en", "por", "para", "con", "sin", "que", "se", "su",
    "sus", "es", "son", "no", "ni", "lo", "le", "les", "como", "mas", "muy",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "ser",
    "haber", "hay", "sobre", "entre", "cada", "dentro", "fuera", "segun",
}

# Glosario de equivalencias del dominio (privacidad / PIMS), normalizado (sin
# tildes). Un auditor tambien maneja un glosario asi: el lenguaje de la norma
# no siempre es el lenguaje de la empresa. Grupos pequenos y especificos a
# proposito — palabras genericas meterian ruido y harian que todo se parezca
# a todo. Se usa solo para expandir la CONSULTA de cada requisito, nunca los
# documentos indexados.
GRUPOS_SINONIMOS = [
    ["consentimiento", "autorizacion", "aceptacion"],
    ["titular", "usuario", "interesado", "cliente"],
    ["supresion", "eliminacion", "borrado"],
    ["encargado", "proveedor", "tercero", "procesador", "subencargado"],
    ["brecha", "incidente", "violacion"],
    ["capacitacion", "formacion", "entrenamiento"],
    ["auditoria", "revision", "verificacion"],
    ["registro", "bitacora", "log"],
    ["contrato", "acuerdo", "convenio"],
    ["vigente", "aprobado", "actualizado"],
    ["clausula", "disposicion", "estipulacion"],
    ["retencion", "conservacion", "almacenamiento"],
    ["multifactor", "mfa"],
    ["confidencialidad", "reserva", "secreto"],
    ["procedimiento", "proceso", "protocolo"],
    ["acceso", "ingreso"],
]


def _construir_mapa_sinonimos():
    mapa = defaultdict(set)
    for grupo in GRUPOS_SINONIMOS:
        for termino in grupo:
            mapa[termino].update(t for t in grupo if t != termino)
    return mapa


MAPA_SINONIMOS = _construir_mapa_sinonimos()


def expandir_consulta(tokens):
    """Agrega, una vez por termino distinto, los sinonimos del glosario del
    dominio. No repite un sinonimo por cada ocurrencia del termino original,
    para no inflar artificialmente su peso en el TF-IDF."""
    expandidos = list(tokens)
    for termino in set(tokens):
        expandidos.extend(sorted(MAPA_SINONIMOS.get(termino, ())))
    return expandidos


def normalizar(texto):
    """minusculas y sin tildes, para que 'proteccion' y 'protección' coincidan."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def tokenizar(texto):
    crudo = PATRON_PALABRA.findall(normalizar(texto))
    return [t for t in crudo if t not in PALABRAS_VACIAS and len(t) > 1]


def construir_idf(documentos_tokenizados):
    n = len(documentos_tokenizados)
    df = Counter()
    for tokens in documentos_tokenizados:
        for termino in set(tokens):
            df[termino] += 1
    return {termino: math.log((n + 1) / (freq + 1)) + 1 for termino, freq in df.items()}


def vector_tfidf(tokens, idf):
    tf = Counter(tokens)
    total = len(tokens) or 1
    return {termino: (freq / total) * idf.get(termino, 0.0) for termino, freq in tf.items()}


def similitud_coseno(v1, v2):
    terminos_comunes = set(v1) & set(v2)
    producto = sum(v1[t] * v2[t] for t in terminos_comunes)
    norma1 = math.sqrt(sum(p * p for p in v1.values()))
    norma2 = math.sqrt(sum(p * p for p in v2.values()))
    if norma1 == 0 or norma2 == 0:
        return 0.0
    return producto / (norma1 * norma2)


def construir_consulta(req_id, requisito):
    partes = [requisito["nombre"], requisito["descripcion"]] + requisito.get("tipo_evidencia_esperada", [])
    return " ".join(partes)


def recuperar(chunks, requisitos, top_k, umbral, usar_sinonimos=True):
    tokens_chunks = [tokenizar(c["texto"]) for c in chunks]
    idf = construir_idf(tokens_chunks)
    vectores_chunks = [vector_tfidf(t, idf) for t in tokens_chunks]

    chunks_por_documento = defaultdict(list)
    for chunk in chunks:
        chunks_por_documento[chunk["id_documento"]].append(chunk)

    resultados = {}
    for req_id, requisito in requisitos.items():
        consulta = construir_consulta(req_id, requisito)
        tokens_consulta = tokenizar(consulta)
        if usar_sinonimos:
            tokens_consulta = expandir_consulta(tokens_consulta)
        vector_consulta = vector_tfidf(tokens_consulta, idf)

        puntaje_chunk = {}
        for chunk, vector_chunk in zip(chunks, vectores_chunks):
            puntaje_chunk[chunk["chunk_id"]] = similitud_coseno(vector_consulta, vector_chunk)

        # Rankear documentos por su mejor chunk, no chunk por chunk suelto.
        mejor_por_documento = defaultdict(float)
        for chunk in chunks:
            score = puntaje_chunk[chunk["chunk_id"]]
            if score > mejor_por_documento[chunk["id_documento"]]:
                mejor_por_documento[chunk["id_documento"]] = score

        documentos_relevantes = [d for d, s in mejor_por_documento.items() if s >= umbral]
        documentos_relevantes.sort(key=lambda d: -mejor_por_documento[d])
        documentos_relevantes = documentos_relevantes[:top_k]

        fragmentos = []
        for id_doc in documentos_relevantes:
            for chunk in sorted(chunks_por_documento[id_doc], key=lambda c: c["chunk_id"]):
                fragmentos.append({
                    "chunk_id": chunk["chunk_id"], "id_documento": chunk["id_documento"],
                    "tipo": chunk["tipo"], "fecha_documento": chunk["fecha_documento"],
                    "responsable": chunk["responsable"], "ubicacion": chunk["ubicacion"],
                    "texto": chunk["texto"], "score": round(puntaje_chunk[chunk["chunk_id"]], 4),
                    "score_documento": round(mejor_por_documento[id_doc], 4),
                })
        resultados[req_id] = fragmentos
    return resultados


def main():
    ap = argparse.ArgumentParser(description="Recupera (RAG lexico) los fragmentos mas relevantes por requisito.")
    ap.add_argument("--indice", required=True, help="JSON escrito por indexar_documentos.py")
    ap.add_argument("--requisitos", required=True, help="requisitos.json del skill")
    ap.add_argument("--salida", default="fragmentos_recuperados.json", help="ruta del JSON de salida")
    ap.add_argument("--top-k", type=int, default=4, help="maximo de DOCUMENTOS relevantes a devolver por requisito (se incluyen todos sus chunks)")
    ap.add_argument("--umbral", type=float, default=0.08, help="similitud minima (del mejor chunk del documento) para considerarlo relevante")
    ap.add_argument("--sin-sinonimos", action="store_true", help="desactiva la expansion de consulta con el glosario del dominio (para comparar)")
    args = ap.parse_args()

    with open(args.indice, encoding="utf-8") as f:
        chunks = json.load(f)["chunks"]
    with open(args.requisitos, encoding="utf-8") as f:
        requisitos = json.load(f)["requisitos"]

    resultados = recuperar(chunks, requisitos, args.top_k, args.umbral, usar_sinonimos=not args.sin_sinonimos)

    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("Fragmentos recuperados para %d requisitos (top-%d, umbral %.2f, sinonimos %s) -> %s"
          % (len(resultados), args.top_k, args.umbral, "NO" if args.sin_sinonimos else "si", args.salida))
    sin_fragmentos = [r for r, frags in resultados.items() if not frags]
    if sin_fragmentos:
        print("Sin fragmentos relevantes (candidatos a SIN_EVIDENCIA): %s" % ", ".join(sorted(sin_fragmentos)))


if __name__ == "__main__":
    main()
