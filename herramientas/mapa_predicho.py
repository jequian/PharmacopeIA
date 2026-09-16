#!/usr/bin/env python3
"""
De afinidades a mapa cerebral predicho.

IDEA
----
La afinidad de un fármaco por cada blanco se mide con radioligando (PDSP).
La densidad de cada blanco en cada parcela se mide con PET (atlas públicos).
Multiplicando y sumando se obtiene un mapa espacial predicho del efecto:

    M_f(p) = Σ_r  w_f(r) · z(densidad_r(p))

donde w_f(r) es la fracción de fármaco unida a cada blanco a concentración
baja y común:  w ∝ 1/Ki, normalizado a suma 1.

Eso hace comparables fármacos que no comparten ningún receptor, y permite
correlacionar un fármaco contra cualquier otro mapa cerebral: redes,
gradiente principal, diferencias caso-control, respuesta a tratamiento.

USO
---
    python3 mapa_predicho.py --datos ../datos --densidades ../espacial/densidades.csv
    python3 mapa_predicho.py ... --comparar clozapina quetiapina
    python3 mapa_predicho.py ... --contra gradiente1 --nulos 5000

ENTRADA
-------
espacial/densidades.csv   una fila por parcela. Columnas:
                          parcela, [una por mapa], p.ej. 5HT2A, D2, SERT...
espacial/parcelas.csv     opcional. parcela, x, y, z, network, gradient1
                          Las coordenadas son necesarias para los nulos.

Las columnas de densidades se cruzan con los blancos del grafo por el
campo `column` de las aristas has_density, o por coincidencia de nombre.

LO QUE ESTE MODELO NO SABE
--------------------------
1. Dirección. Un agonista y un antagonista del mismo receptor producen el
   mismo mapa aquí. Mientras las aristas importadas del PDSP tengan
   `action: desconocido`, el mapa es de OCUPACIÓN, no de efecto.
2. Ocupación real. Usa afinidad relativa, no ocupación a dosis clínica.
3. Efecto de red. El signo celular y el signo de red pueden ser opuestos
   (TrkB en interneuronas de parvalbúmina desinhibe piramidales).
4. Al paciente. Los atlas PET son promedios de grupo de adultos sanos.

Trátalo como generador de hipótesis ordenadas, no como medida de efecto.
"""

import argparse
import csv
import glob
import os
import sys

import numpy as np

try:
    import yaml
except ImportError:
    sys.exit("Falta PyYAML:  pip install pyyaml --break-system-packages")


# ----------------------------------------------------------------------
def cargar_grafo(carpeta):
    nodos, aristas = {}, []
    secciones = ("drugs", "molecules", "cells", "circuits", "domains",
                 "phenotypes", "biomarkers", "trials", "parcels", "spatialmaps")
    for ruta in sorted(glob.glob(os.path.join(carpeta, "*.yaml"))):
        doc = yaml.safe_load(open(ruta)) or {}
        for sec in secciones:
            for n in doc.get(sec) or []:
                nodos[n["id"]] = n
        aristas += doc.get("edges") or []
    return nodos, aristas


def cargar_densidades(ruta):
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        sys.exit(f"{ruta} está vacío.")
    cols = [c for c in filas[0] if c.lower() not in ("parcela", "parcel", "roi")]
    key = next(c for c in filas[0] if c.lower() in ("parcela", "parcel", "roi"))
    parcelas = [f[key] for f in filas]
    M = np.full((len(filas), len(cols)), np.nan)
    for i, f in enumerate(filas):
        for j, c in enumerate(cols):
            try:
                M[i, j] = float(f[c])
            except (TypeError, ValueError):
                pass
    return parcelas, cols, M


def z(v):
    v = np.asarray(v, float)
    ok = ~np.isnan(v)
    if ok.sum() < 2 or np.nanstd(v) == 0:
        return np.zeros_like(v)
    out = np.zeros_like(v)
    out[ok] = (v[ok] - v[ok].mean()) / v[ok].std()
    return out


def slugify(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


# ----------------------------------------------------------------------
def pesos_por_farmaco(nodos, aristas, cols):
    """w ∝ 1/Ki, normalizado. Solo aristas acts_on con Ki numérico."""
    # blanco -> columna de densidades
    mapa_col = {}
    for e in aristas:
        if e.get("type") == "has_density" and e.get("column"):
            mapa_col[e["from"]] = e["column"]
    por_slug = {slugify(c): c for c in cols}
    for mid, n in nodos.items():
        if mid in mapa_col:
            continue
        for cand in (n.get("gene"), n.get("name"), mid.split(":", 1)[-1]):
            if cand and slugify(cand) in por_slug:
                mapa_col[mid] = por_slug[slugify(cand)]
                break

    pesos, sin_mapa = {}, set()
    for e in aristas:
        if e.get("type") != "acts_on":
            continue
        ki = e.get("affinity_ki_nm")
        if not isinstance(ki, (int, float)) or ki <= 0:
            continue
        col = mapa_col.get(e["to"])
        if col is None:
            sin_mapa.add(e["to"])
            continue
        pesos.setdefault(e["from"], {})
        pesos[e["from"]][col] = max(pesos[e["from"]].get(col, 0), 1.0 / ki)

    for f in pesos:
        tot = sum(pesos[f].values())
        if tot:
            pesos[f] = {c: w / tot for c, w in pesos[f].items()}
    return pesos, mapa_col, sin_mapa


def mapas_predichos(pesos, cols, M):
    idx = {c: j for j, c in enumerate(cols)}
    Z = np.column_stack([z(M[:, j]) for j in range(M.shape[1])])
    out = {}
    for f, w in pesos.items():
        v = np.zeros(M.shape[0])
        for c, peso in w.items():
            v += peso * Z[:, idx[c]]
        out[f] = v
    return out


# ----------------------------------------------------------------------
def rangos(v):
    o = np.argsort(np.argsort(v))
    return o.astype(float)


def spearman(a, b):
    ra, rb = rangos(a), rangos(b)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra * rb).sum() / d) if d else float("nan")


def sustitutos(v, XYZ, n=1000, rng=None):
    """Mapas nulos que CONSERVAN la autocorrelación espacial.

    Es la parte que la mitad de esta literatura se salta. Dos mapas
    cerebrales cualesquiera correlacionan alto solo porque ambos varían
    suavemente en el espacio: un nulo por permutación simple da p<0.001
    para cualquier par y no significa nada.

    Método (BrainSMASH simplificado): se genera ruido, se suaviza con un
    núcleo gaussiano sobre la matriz de distancias hasta imitar la
    suavidad del mapa original, y se le impone la distribución de valores
    del original por emparejamiento de rangos.
    """
    rng = rng or np.random.default_rng(0)
    D = np.linalg.norm(XYZ[:, None, :] - XYZ[None, :, :], axis=-1)
    escala = np.median(D[D > 0])
    K = np.exp(-(D ** 2) / (2 * escala ** 2))
    K /= K.sum(axis=1, keepdims=True)
    ordenado = np.sort(v)
    out = np.empty((n, len(v)))
    for i in range(n):
        s = K @ rng.standard_normal(len(v))
        out[i] = ordenado[np.argsort(np.argsort(s))]
    return out


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", default="datos")
    ap.add_argument("--densidades", default="espacial/densidades.csv")
    ap.add_argument("--parcelas", default="espacial/parcelas.csv")
    ap.add_argument("--comparar", nargs="*", default=None,
                    help="Fármacos a correlacionar entre sí. Vacío = todos.")
    ap.add_argument("--contra", default=None,
                    help="Columna externa (gradient1, network, un mapa de "
                         "diferencia caso-control...) contra la que medir.")
    ap.add_argument("--nulos", type=int, default=0,
                    help="Número de mapas sustitutos. 0 = no reporta p.")
    ap.add_argument("--salida", default=None, help="CSV con los mapas predichos.")
    a = ap.parse_args()

    nodos, aristas = cargar_grafo(a.datos)
    parcelas, cols, M = cargar_densidades(a.densidades)
    pesos, mapa_col, sin_mapa = pesos_por_farmaco(nodos, aristas, cols)

    if not pesos:
        sys.exit("Ningún fármaco tiene aristas acts_on con Ki que crucen con "
                 "una columna de densidades. Revisa nombres de columna.")

    nm = lambda i: (nodos.get(i) or {}).get("name", i)
    print(f"{len(parcelas)} parcelas · {len(cols)} mapas · "
          f"{len(pesos)} fármacos con mapa predicho")
    if sin_mapa:
        print(f"! {len(sin_mapa)} blancos del grafo sin mapa de densidad "
              f"(se ignoran): {', '.join(sorted(nm(x) for x in list(sin_mapa)[:6]))}"
              f"{'…' if len(sin_mapa) > 6 else ''}")

    mapas = mapas_predichos(pesos, cols, M)

    # -------- cobertura: cuánto del fármaco quedó representado ---------
    print("\nCobertura (fracción del peso de unión con mapa disponible):")
    for f in sorted(mapas, key=nm):
        n_bl = len(pesos[f])
        dom = max(pesos[f].items(), key=lambda kv: kv[1])
        print(f"  {nm(f):<20} {n_bl:>3} blancos · domina {dom[0]} ({dom[1]*100:.0f}%)")
        if dom[1] > 0.8:
            print(f"      ! un solo blanco concentra el peso: el mapa "
                  f"es casi el de {dom[0]}, no el del fármaco")

    XYZ = None
    if os.path.exists(a.parcelas):
        with open(a.parcelas, newline="", encoding="utf-8-sig") as f:
            pf = {r[list(r)[0]]: r for r in csv.DictReader(f)}
        try:
            XYZ = np.array([[float(pf[p][k]) for k in ("x", "y", "z")]
                            for p in parcelas])
        except (KeyError, ValueError):
            XYZ = None

    # -------- fármaco contra fármaco -----------------------------------
    sel = ([f for f in mapas if any(slugify(t) in slugify(f) or
                                    slugify(t) in slugify(nm(f))
                                    for t in a.comparar)]
           if a.comparar else sorted(mapas, key=nm))
    if len(sel) > 1:
        print("\nSimilitud espacial entre fármacos (Spearman):")
        print("  Aquí NO hace falta nulo espacial: ambos mapas comparten la "
              "misma\n  estructura espacial, y lo que se compara son los "
              "fármacos, no el espacio.")
        anchura = max(len(nm(f)) for f in sel)
        print("\n" + " " * (anchura + 2) +
              "  ".join(f"{nm(f)[:6]:>6}" for f in sel))
        for f in sel:
            fila = "  ".join(f"{spearman(mapas[f], mapas[g]):>6.2f}" for g in sel)
            print(f"{nm(f):<{anchura}}  {fila}")

    # -------- fármaco contra mapa externo ------------------------------
    if a.contra:
        ext = None
        if a.contra in cols:
            ext = M[:, cols.index(a.contra)]
        elif XYZ is not None or os.path.exists(a.parcelas):
            with open(a.parcelas, newline="", encoding="utf-8-sig") as f:
                pf = {r[list(r)[0]]: r for r in csv.DictReader(f)}
            try:
                ext = np.array([float(pf[p][a.contra]) for p in parcelas])
            except (KeyError, ValueError):
                ext = None
        if ext is None:
            sys.exit(f"No encuentro la columna '{a.contra}'.")

        print(f"\nCorrelación contra '{a.contra}':")
        if a.nulos and XYZ is None:
            print("  ! Pediste nulos pero falta espacial/parcelas.csv con "
                  "columnas x,y,z.\n    Sin coordenadas no hay nulo espacial "
                  "válido, así que NO reporto p.")
        sur = (sustitutos(ext, XYZ, a.nulos) if (a.nulos and XYZ is not None)
               else None)
        for f in sorted(mapas, key=nm):
            rho = spearman(mapas[f], ext)
            if sur is not None:
                nulo = np.array([spearman(mapas[f], s) for s in sur])
                p = (np.abs(nulo) >= abs(rho)).mean()
                print(f"  {nm(f):<20} rho={rho:>6.2f}   p_espacial={p:.4f}"
                      f"{'  *' if p < .05 else ''}")
            else:
                print(f"  {nm(f):<20} rho={rho:>6.2f}   (sin p: falta nulo espacial)")
        if sur is None:
            print("\n  Un rho sin nulo espacial NO es interpretable. La "
                  "autocorrelación\n  de los mapas cerebrales hace que casi "
                  "cualquier par correlacione.")

    # -------- salida ----------------------------------------------------
    if a.salida:
        with open(a.salida, "w", newline="") as f:
            w = csv.writer(f)
            orden = sorted(mapas, key=nm)
            w.writerow(["parcela"] + [nm(x) for x in orden])
            for i, p in enumerate(parcelas):
                w.writerow([p] + [f"{mapas[x][i]:.5f}" for x in orden])
        print(f"\n✓ {a.salida}")


if __name__ == "__main__":
    main()
