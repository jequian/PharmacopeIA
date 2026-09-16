#!/usr/bin/env python3
"""
Genera el visor HTML autocontenido a partir de los YAML del grafo.

Uso:
    python3 construir_visor.py

Lee ontologia.yaml, cat-*.yaml, seed-*.yaml y PENDIENTES.md del directorio
actual, y escribe visor.html. El HTML resultante no necesita servidor ni
conexión salvo para las tipografías: se abre con doble clic.

Vuelve a correrlo cada vez que edites un YAML.
"""

import json
import glob
import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML:  pip install pyyaml --break-system-packages")

NODE_SECTIONS = {
    "drugs": "drug", "molecules": "mol", "cells": "cell",
    "circuits": "circuit", "domains": "domain", "phenotypes": "pheno",
    "biomarkers": "bmk", "trials": "trial",
}

PLANTILLA = "visor-plantilla.html"
SALIDA = "visor.html"


def main():
    if not os.path.exists(PLANTILLA):
        sys.exit(f"No encuentro {PLANTILLA}")

    archivos = sorted(set(glob.glob("cat-*.yaml") + glob.glob("seed-*.yaml")
                        + glob.glob("../datos/cat-*.yaml")
                        + glob.glob("../datos/seed-*.yaml")))
    if not archivos:
        sys.exit("No hay archivos cat-*.yaml ni seed-*.yaml en este directorio.")

    por_id, edges, contrasts = {}, [], []
    for path in archivos:
        with open(path) as f:
            doc = yaml.safe_load(f) or {}
        for sec, tipo in NODE_SECTIONS.items():
            for n in doc.get(sec) or []:
                nuevo = {**n, "_tipo": tipo, "_archivo": path}
                # Un nodo puede declararse en el catálogo y volver a
                # mencionarse en una semilla: se fusionan, gana el que
                # traiga más campos (normalmente la semilla).
                if n["id"] in por_id:
                    por_id[n["id"]].update({k: v for k, v in nuevo.items() if v})
                else:
                    por_id[n["id"]] = nuevo
        for e in doc.get("edges") or []:
            edges.append({**e, "_archivo": path})
        for c in doc.get("contrasts") or []:
            contrasts.append({**c, "_archivo": path})

    nodes = list(por_id.values())
    datos = {"nodes": nodes, "edges": edges, "contrasts": contrasts}

    pendientes = ""
    for cand in ("PENDIENTES.md", "../PENDIENTES.md"):
        if os.path.exists(cand):
            pendientes = open(cand).read()
            break

    html = open(PLANTILLA).read()
    html = html.replace("/*__DATOS__*/{}", json.dumps(datos, ensure_ascii=False))
    html = html.replace('/*__PENDIENTES__*/""', json.dumps(pendientes, ensure_ascii=False))

    with open(SALIDA, "w") as f:
        f.write(html)

    kb = os.path.getsize(SALIDA) / 1024
    print(f"✓ {SALIDA}  ({kb:.0f} KB)")
    print(f"  archivos leídos: {', '.join(archivos)}")
    print(f"  {len(nodes)} nodos · {len(edges)} aristas · {len(contrasts)} contrastes")


if __name__ == "__main__":
    main()
