#!/usr/bin/env python3
"""
Importa afinidades de la base Ki del PDSP a aristas acts_on del grafo.

CÓMO OBTENER EL CSV
-------------------
1. Abre https://pdsp.unc.edu/databases/kidb.php
2. Consulta por fármaco (campo Ligand Name) o por blanco (Receptor Name).
   Puedes traer varios fármacos en consultas sucesivas.
3. Descarga el resultado con el botón de exportar a CSV.
4. Deja los CSV en una carpeta y apunta este script a ella.

    # volcado completo, filtrando por catálogo y por afinidad:
    python3 importar_pdsp.py KiDatabase.csv --catalogo cat-01-farmacos.yaml \
            --solo-catalogo --umbral-ki 100

    # Sin --umbral-ki salen ~1700 aristas y 245 blancos: la matriz se
    # vuelve ilegible. Con 100 nM quedan ~450 aristas y 105 blancos, que es
    # más o menos el rango donde la unión suele importar en clínica.

    # o una carpeta con CSV de consultas sueltas:
    python3 importar_pdsp.py ./pdsp_csv --catalogo cat-01-farmacos.yaml

Genera `cat-02-afinidades.yaml` con una arista acts_on por cada par
fármaco-blanco encontrado, lista para validar y cargar en el visor.

LO QUE EL SCRIPT NO PUEDE HACER
-------------------------------
- Determinar la ACCIÓN. El PDSP da afinidad de unión, no si el compuesto
  es agonista o antagonista. Todas las aristas salen con
  `action: desconocido` y hay que completarlas a mano o cruzando con la
  guía de IUPHAR/BPS. El script las marca para que el validador las vea.
- Determinar la OCUPACIÓN a dosis terapéutica, que es lo que realmente
  discrimina en varios contrastes. Eso viene de estudios de PET, no de aquí.
- Decidir relevancia terapéutica. Marca `dudosa` cuando el Ki supera el
  umbral configurable de abajo, pero es una heurística, no un criterio.
"""

import sys
import os
import csv
import io
import glob
import re
import unicodedata

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML:  pip install pyyaml --break-system-packages")

# Ki por encima de este valor (nM) se marca de relevancia dudosa.
UMBRAL_KI_NM = 1000.0

SALIDA = "cat-02-afinidades.yaml"

# Nombres de columna que el PDSP ha usado. Se busca sin distinguir
# mayúsculas ni espacios; si tu CSV trae otros, añádelos aquí.
COL_LIGANDO = ["ligand name", "ligand", "name", "drug"]
COL_BLANCO = ["receptor name", "receptor", "target", "name"]
COL_KI = ["ki val", "ki", "ki_val", "ki (nm)", "value"]
COL_ESPECIE = ["species", "receptor species"]
COL_REF = ["reference", "refs", "source"]


def canon(s):
    """Normaliza para cruzar nombres en inglés (PDSP) con los del catálogo
    en español. clozapine/clozapina, phenytoin/fenitoína, valproate/valproato,
    risperidone/risperidona -> misma clave."""
    t = slug(s).replace("-", "")
    t = t.replace("ph", "f").replace("th", "t").replace("y", "i")
    while t and t[-1] in "aeo":
        t = t[:-1]
    return t


def slug(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def buscar_col(cabeceras, candidatos):
    norm = {h.strip().lower(): h for h in cabeceras}
    for c in candidatos:
        if c in norm:
            return norm[c]
    for h_low, h in norm.items():
        if any(h_low.startswith(c) for c in candidatos):
            return h
    return None


def cargar_alias(catalogo):
    """Mapea nombre de fármaco -> id existente, para no duplicar nodos."""
    alias = {}
    if not catalogo or not os.path.exists(catalogo):
        return alias
    doc = yaml.safe_load(open(catalogo)) or {}
    for d in doc.get("drugs") or []:
        for k in (d.get("name", ""), d["id"].split(":", 1)[1]):
            alias[slug(k)] = d["id"]
            alias[canon(k)] = d["id"]
    for m in doc.get("molecules") or []:
        alias[slug(m.get("name", ""))] = m["id"]
        alias[canon(m.get("name", ""))] = m["id"]
        for g in str(m.get("gene", "")).replace("/", " ").split():
            alias[slug(g)] = m["id"]
    return alias


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    catalogo = None
    if "--catalogo" in sys.argv:
        catalogo = sys.argv[sys.argv.index("--catalogo") + 1]
        args = [a for a in args if a != catalogo]
    if not args:
        sys.exit(__doc__)

    solo_cat = "--solo-catalogo" in sys.argv
    umbral = float("inf")
    if "--umbral-ki" in sys.argv:
        umbral = float(sys.argv[sys.argv.index("--umbral-ki") + 1])
        args = [a for a in args if a != str(umbral)]
    carpeta = args[0]
    rutas = ([carpeta] if carpeta.lower().endswith(".csv")
             else sorted(glob.glob(os.path.join(carpeta, "*.csv"))))
    if not rutas:
        sys.exit(f"No hay CSV en {carpeta}")

    alias = cargar_alias(catalogo)
    nuevos_farmacos, nuevas_moleculas, aristas = {}, {}, {}
    sin_mapear = set()

    for ruta in rutas:
        # El volcado del PDSP no es UTF-8 limpio: trae bytes cp1252
        # (comillas tipográficas en las referencias) repartidos por todo el
        # archivo, así que hay que decidir la codificación leyéndolo entero.
        crudo = open(ruta, "rb").read()
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                texto = crudo.decode(enc)
                break
            except UnicodeDecodeError:
                texto = None
        if texto is None:
            texto = crudo.decode("cp1252", errors="replace")
        with io.StringIO(texto, newline="") as f:
            r = csv.DictReader(f)
            if not r.fieldnames:
                continue
            cl = buscar_col(r.fieldnames, COL_LIGANDO)
            cb = buscar_col(r.fieldnames, COL_BLANCO)
            ck = buscar_col(r.fieldnames, COL_KI)
            cg = buscar_col(r.fieldnames, ["unigene", "gene"])
            ce = buscar_col(r.fieldnames, COL_ESPECIE)
            cr = buscar_col(r.fieldnames, COL_REF)
            if not (cl and cb and ck):
                print(f"! {os.path.basename(ruta)}: no reconozco las columnas "
                      f"{r.fieldnames}. Ajusta COL_* en el script.")
                continue

            for fila in r:
                lig, bl = (fila.get(cl) or "").strip(), (fila.get(cb) or "").strip()
                if not lig or not bl:
                    continue
                try:
                    ki = float(str(fila.get(ck)).replace(",", "").strip())
                except (TypeError, ValueError):
                    continue

                did = alias.get(slug(lig)) or alias.get(canon(lig))
                mid = (alias.get(slug(fila.get(cg, "") if cg else "")) or
                       alias.get(slug(bl)) or alias.get(canon(bl)))
                if solo_cat and not did:
                    continue          # el volcado completo trae ~10k ligandos
                did = did or f"drug:{slug(lig)}"
                mid = mid or f"mol:{slug(bl)}"
                if did not in alias.values():
                    nuevos_farmacos.setdefault(did, lig)
                    sin_mapear.add(lig)
                if mid not in alias.values():
                    nuevas_moleculas.setdefault(mid, bl)

                # Varias filas por par: nos quedamos con el Ki más bajo y
                # contamos cuántas mediciones lo respaldan.
                clave = (did, mid)
                prev = aristas.get(clave)
                n = (prev["_n"] + 1) if prev else 1
                if prev and prev["affinity_ki_nm"] <= ki:
                    prev["_n"] = n
                    continue
                aristas[clave] = {
                    "affinity_ki_nm": round(ki, 2),
                    "_n": n,
                    "species": (fila.get(ce) or "").strip() if ce else "",
                    "ref": (fila.get(cr) or "").strip() if cr else "",
                }

    doc = {
        "meta": {"schema_version": "0.1", "catalog_id": "cat-02-afinidades",
                 "verified": False,
                 "source": "PDSP Ki database — pdsp.unc.edu/databases/kidb.php",
                 "nota": "action: desconocido en TODAS. El PDSP da afinidad, "
                         "no dirección. Completar a mano o con IUPHAR/BPS."},
    }
    if nuevos_farmacos:
        doc["drugs"] = [{"id": i, "name": n, "class": "experimental",
                         "approval_status": "uso_no_aprobado",
                         "notes": "Creado por el importador. Revisar clase."}
                        for i, n in sorted(nuevos_farmacos.items())]
    if nuevas_moleculas:
        doc["molecules"] = [{"id": i, "name": n, "subtype": "receptor_gpcr",
                             "notes": "Creado por el importador. Revisar subtipo."}
                            for i, n in sorted(nuevas_moleculas.items())]

    aristas = {k: v for k, v in aristas.items()
               if v["affinity_ki_nm"] <= umbral}
    usados = {i for par in aristas for i in par}
    doc["molecules"] = [m for m in doc.get("molecules", []) if m["id"] in usados]
    doc["edges"] = []
    for (did, mid), v in sorted(aristas.items()):
        esp = v["species"].lower()
        especie = ("humano" if "human" in esp else
                   "roedor" if any(x in esp for x in ("rat", "mouse", "mus")) else
                   "in_vitro")
        doc["edges"].append({
            "type": "acts_on", "from": did, "to": mid,
            "action": "desconocido",
            "sign": "desconocido",
            "provenance": "sourced",
            "affinity_ki_nm": v["affinity_ki_nm"],
            "affinity_source": "pdsp",
            "therapeutic_relevance": ("dudosa" if v["affinity_ki_nm"] > UMBRAL_KI_NM
                                      else "desconocida"),
            "evidence": {
                "strength": "A" if v["_n"] >= 3 else "B",
                "kind": "union_radioligando",
                "species": especie,
                "status": "establecido",
                "refs": [v["ref"] or "PDSP Ki database"],
            },
            "notes": f"{v['_n']} medición(es) en el CSV; se conserva el Ki más bajo. "
                     f"FALTA la acción (agonista/antagonista) y la ocupación.",
        })

    with open(SALIDA, "w") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False, width=88)

    print(f"✓ {SALIDA}")
    print(f"  {len(doc['edges'])} aristas · "
          f"{len(nuevos_farmacos)} fármacos nuevos · "
          f"{len(nuevas_moleculas)} moléculas nuevas")
    if sin_mapear:
        print("\n! Fármacos del CSV que no coincidieron con el catálogo "
              "(revisa ortografía antes de aceptar los nodos nuevos):")
        for n in sorted(sin_mapear)[:25]:
            print("   " + n)
    print("\nSiguiente: completar 'action' en cada arista y correr")
    print("  python3 validar.py ontologia.yaml cat-*.yaml seed-*.yaml")


if __name__ == "__main__":
    main()
