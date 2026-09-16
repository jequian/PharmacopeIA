#!/usr/bin/env python3
"""
Validador del grafo de convergencia farmacológica.

Uso:
    python3 validar.py ontologia.yaml seed-*.yaml
    python3 validar.py ontologia.yaml seed-*.yaml --matriz
    python3 validar.py ontologia.yaml seed-*.yaml --auditoria

Comprueba que cada nodo y cada arista se ajusten a la ontología, que no
haya referencias colgantes, y reporta el estado de la evidencia.
"""

import sys
import glob
from collections import defaultdict

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML:  pip install pyyaml --break-system-packages")

NODE_SECTIONS = {
    "drugs": "drug", "molecules": "mol", "cells": "cell",
    "circuits": "circuit", "domains": "domain", "phenotypes": "pheno",
    "biomarkers": "bmk", "trials": "trial",
}

SIGNS = {1, -1, 0, "+1", "-1", "bidireccional", "desconocido"}
STRENGTHS = {"A", "B", "C", "D"}
STATUSES = {"establecido", "probable", "propuesto", "contestado", "refutado",
            "no_probado", "probado_sin_efecto"}
PROVENANCES = {"sourced", "inferred"}

# Aristas donde 'sign: 0' es una afirmación sobre el efecto y por tanto
# debe declarar si nadie lo probó o si se probó y no hubo efecto.
# En expressed_in / resides_in / indexes el signo cero solo significa
# "esta relación no tiene dirección", y no aplica el chequeo.
EFECTO = {"treats", "induces", "acts_on", "signals_to", "modulates_circuit"}


def cargar(paths):
    onto, datos = None, []
    for p in paths:
        with open(p) as f:
            doc = yaml.safe_load(f)
        if doc and "node_types" in doc:
            onto = doc
        elif doc:
            datos.append((p, doc))
    if onto is None:
        sys.exit("No se encontró la ontología entre los archivos dados.")
    return onto, datos


def indexar(datos):
    nodos, aristas, contrastes = {}, [], []
    for path, doc in datos:
        for sec, tipo in NODE_SECTIONS.items():
            for n in doc.get(sec) or []:
                nodos[n["id"]] = {**n, "_tipo": tipo, "_archivo": path}
        for e in doc.get("edges") or []:
            aristas.append({**e, "_archivo": path})
        for c in doc.get("contrasts") or []:
            contrastes.append({**c, "_archivo": path})
    return nodos, aristas, contrastes


def validar(onto, nodos, aristas):
    errores, avisos = [], []
    tipos_arista = onto["edge_types"]

    for nid, n in nodos.items():
        prefijo = nid.split(":")[0]
        if prefijo != n["_tipo"]:
            errores.append(f"[{n['_archivo']}] id '{nid}' no coincide con su sección")
        for campo in onto["node_types"][n["_tipo"]].get("required", []):
            if campo not in n and campo != "id":
                errores.append(f"[{n['_archivo']}] {nid}: falta campo obligatorio '{campo}'")

    for i, e in enumerate(aristas):
        et = e.get("type")
        marca = f"[{e['_archivo']}] arista #{i} ({e.get('from')} -> {e.get('to')})"

        if et not in tipos_arista:
            errores.append(f"{marca}: tipo de arista desconocido '{et}'")
            continue

        spec = tipos_arista[et]
        for extremo, campo in (("from", "from"), ("to", "to")):
            nid = e.get(campo)
            if nid not in nodos:
                errores.append(f"{marca}: nodo '{nid}' no existe")
            else:
                permitidos = spec.get(extremo, [])
                if permitidos and nodos[nid]["_tipo"] not in permitidos:
                    errores.append(
                        f"{marca}: {campo}='{nid}' es tipo '{nodos[nid]['_tipo']}', "
                        f"se esperaba uno de {permitidos}")

        if e.get("sign") not in SIGNS:
            errores.append(f"{marca}: sign inválido o ausente")
        if e.get("provenance") not in PROVENANCES:
            errores.append(f"{marca}: provenance inválido o ausente")

        ev = e.get("evidence")
        if not ev:
            errores.append(f"{marca}: falta bloque 'evidence'")
        else:
            if ev.get("strength") not in STRENGTHS:
                errores.append(f"{marca}: evidence.strength inválido")
            if ev.get("status") not in STATUSES:
                errores.append(f"{marca}: evidence.status inválido")
            refs = ev.get("refs") or []
            if not refs and e.get("provenance") == "sourced":
                errores.append(f"{marca}: arista 'sourced' SIN referencias")
            if any("PENDIENTE" in str(r) for r in refs):
                avisos.append(f"{marca}: referencia PENDIENTE de verificar")
            if e.get("provenance") == "inferred" and ev.get("strength") != "D":
                avisos.append(f"{marca}: inferida pero con strength != D")
            if (e.get("sign") in (0, "0") and et in EFECTO
                    and ev.get("status") not in {"no_probado", "probado_sin_efecto"}):
                errores.append(
                    f"{marca}: sign 0 sin declarar si es 'no_probado' "
                    f"(nadie lo estudió) o 'probado_sin_efecto' (se estudió, "
                    f"nulo real). Estado actual: '{ev.get('status')}'")
            if ev.get("status") == "no_probado" and (ev.get("refs") or []):
                avisos.append(f"{marca}: marcada no_probado pero trae referencias")

    return errores, avisos


def matriz(nodos, aristas):
    farmacos = sorted(n for n, v in nodos.items() if v["_tipo"] == "drug")
    celdas = defaultdict(dict)
    blancos = set()
    for e in aristas:
        if e.get("type") == "acts_on":
            celdas[e["from"]][e["to"]] = e.get("action", "?")
            blancos.add(e["to"])
    blancos = sorted(blancos)

    print("\n=== MATRIZ FÁRMACO × BLANCO ===\n")
    print("Columnas:")
    for j, b in enumerate(blancos, 1):
        print(f"  {j:>2}. {nodos[b].get('name', b)}")
    print()

    ancho = max((len(nodos[f].get("name", f)) for f in farmacos), default=10)
    cab = "  ".join(f"{j:>2}" for j in range(1, len(blancos) + 1))
    print(" " * ancho + "  " + cab)
    print(" " * ancho + "  " + "-" * len(cab))
    for f in farmacos:
        fila = [(" X" if b in celdas[f] else " .") for b in blancos]
        print(f"{nodos[f].get('name', f):<{ancho}}  " + "  ".join(fila))

    print("\nDetalle de acciones:")
    for f in farmacos:
        if celdas[f]:
            acciones = ", ".join(
                f"{nodos[b].get('name', b)} [{a}]" for b, a in sorted(celdas[f].items()))
            print(f"  {nodos[f].get('name', f)}: {acciones}")
    print()


def auditoria(nodos, aristas, contrastes):
    print("\n=== AUDITORÍA DE EVIDENCIA ===\n")
    por_fuerza = defaultdict(int)
    por_estado = defaultdict(int)
    inferidas, sin_ref = [], []
    for e in aristas:
        ev = e.get("evidence") or {}
        por_fuerza[ev.get("strength", "?")] += 1
        por_estado[ev.get("status", "?")] += 1
        if e.get("provenance") == "inferred":
            inferidas.append(e)
        if not (ev.get("refs") or []):
            sin_ref.append(e)

    print(f"Nodos: {len(nodos)}   Aristas: {len(aristas)}   Contrastes: {len(contrastes)}")
    print("\nPor fuerza de evidencia:")
    for k in ("A", "B", "C", "D", "?"):
        if por_fuerza[k]:
            print(f"  {k}: {por_fuerza[k]}")
    print("\nPor estado:")
    for k, v in sorted(por_estado.items()):
        print(f"  {k}: {v}")

    if inferidas:
        print(f"\nAristas INFERIDAS ({len(inferidas)}) — razonamiento, no hallazgos:")
        for e in inferidas:
            print(f"  {e['from']} -> {e['to']}  ({e['type']})")

    if sin_ref:
        print(f"\nAristas SIN REFERENCIA ({len(sin_ref)}):")
        for e in sin_ref:
            print(f"  {e['from']} -> {e['to']}")

    no_resueltos = [c for c in contrastes if c.get("resolved") != "si"]
    if no_resueltos:
        print(f"\nContrastes ABIERTOS ({len(no_resueltos)}):")
        for c in no_resueltos:
            n_exp = len(c.get("candidate_explanations") or [])
            print(f"  {c['id']}: {len(c.get('members', []))} miembros, "
                  f"{n_exp} explicaciones candidatas")
    print()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    paths = []
    for a in args:
        paths.extend(glob.glob(a) or [a])
    if not paths:
        sys.exit(__doc__)

    onto, datos = cargar(paths)
    nodos, aristas, contrastes = indexar(datos)
    errores, avisos = validar(onto, nodos, aristas)

    if errores:
        print(f"\n✗ {len(errores)} ERROR(ES):")
        for x in errores:
            print("  " + x)
    else:
        print("\n✓ Estructura válida.")
    if avisos:
        print(f"\n! {len(avisos)} aviso(s):")
        for x in avisos:
            print("  " + x)

    if "--matriz" in flags:
        matriz(nodos, aristas)
    if "--auditoria" in flags:
        auditoria(nodos, aristas, contrastes)
    if not flags:
        print("\n(usa --matriz o --auditoria para más)")

    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
