#!/usr/bin/env python3
"""
Contraste `exp-2` de seed-02: ¿la razón entre bloqueo 5-HT2 y ocupación D2
ordena a los antipsicóticos según su propensión a inducir sintomatología
obsesiva?

    python3 analisis_razon_5ht2_d2.py datos_razon.csv

ESTE SCRIPT NO TRAE DATOS. Trae el método.
--------------------------------------------------
No corrí el análisis porque no tengo las cifras y no voy a inventarlas.
Hacen falta tres columnas por fármaco y cada una viene de una fuente
distinta:

  ki_5ht2a, ki_5ht2c   base Ki del PDSP (pdsp.unc.edu/databases/kidb.php)
  ocup_d2_pct          literatura de PET a dosis clínica; NO es afinidad
  soc_incidencia_pct   series clínicas de sintomatología obsesiva

Corre `--plantilla` para generar el CSV vacío con los fármacos ya puestos.

LO QUE EL ANÁLISIS PUEDE Y NO PUEDE DECIR
-----------------------------------------
Puede: si existe orden monotónico entre la razón y la incidencia.
No puede: establecer causalidad. Las incidencias vienen de poblaciones
distintas, con criterios distintos y sin ajuste por gravedad ni por
comorbilidad obsesiva basal. Con ocho o diez fármacos, el intervalo de
confianza de una correlación de rangos es tan ancho que solo un resultado
extremo significa algo. Trátalo como generador de hipótesis.

Y antes de interpretar cualquier resultado: `exp-4` del contraste sigue
sin descartarse. Si lo que la clozapina hace es desenmascarar
sintomatología preexistente, esta correlación puede salir positiva y no
significar nada sobre inducción.
"""

import sys
import csv
import math

FARMACOS = ["Clozapina", "Olanzapina", "Quetiapina", "Risperidona",
            "Paliperidona", "Aripiprazol", "Cariprazina", "Brexpiprazol",
            "Ziprasidona", "Lurasidona", "Amisulprida", "Haloperidol"]

COLS = ["farmaco", "ki_5ht2a_nm", "ki_5ht2c_nm", "ocup_d2_pct",
        "ocup_d2_fuente", "soc_incidencia_pct", "soc_n", "soc_fuente"]


def plantilla(path="datos_razon.csv"):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for d in FARMACOS:
            w.writerow([d] + [""] * (len(COLS) - 1))
    print(f"✓ {path} — {len(FARMACOS)} filas por llenar.")
    print("  Deja vacío lo que no encuentres; el script ignora filas incompletas")
    print("  y te dice cuántas descartó. No rellenes con estimaciones.")


def spearman(x, y):
    """Correlación de rangos, con empates promediados."""
    def rangos(v):
        orden = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(orden):
            j = i
            while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
                j += 1
            prom = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[orden[k]] = prom
            i = j + 1
        return r

    rx, ry = rangos(x), rangos(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def main():
    if "--plantilla" in sys.argv:
        plantilla()
        return
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    filas, descartadas = [], []
    with open(sys.argv[1], newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                ki2a = float(row["ki_5ht2a_nm"])
                ocu = float(row["ocup_d2_pct"])
                inc = float(row["soc_incidencia_pct"])
                if ki2a <= 0 or ocu <= 0:
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                descartadas.append(row.get("farmaco", "?"))
                continue
            # Afinidad alta = Ki bajo. Se usa pKi (−log10 M) para que
            # "más bloqueo 5-HT2" sea un número mayor.
            p2a = -math.log10(ki2a * 1e-9)
            filas.append({"f": row["farmaco"], "razon": p2a / ocu, "inc": inc,
                          "p2a": p2a, "ocu": ocu})

    if descartadas:
        print(f"! {len(descartadas)} fila(s) incompleta(s), descartadas: "
              f"{', '.join(descartadas)}\n")
    if len(filas) < 4:
        sys.exit(f"Solo {len(filas)} fármaco(s) completo(s). Con menos de "
                 f"cuatro no tiene sentido calcular nada.")

    filas.sort(key=lambda r: -r["razon"])
    print(f"{'Fármaco':<15}{'pKi 5-HT2A':>11}{'Ocup D2 %':>11}"
          f"{'Razón':>9}{'SOC %':>8}")
    print("-" * 54)
    for r in filas:
        print(f"{r['f']:<15}{r['p2a']:>11.2f}{r['ocu']:>11.1f}"
              f"{r['razon']:>9.4f}{r['inc']:>8.1f}")

    rho = spearman([r["razon"] for r in filas], [r["inc"] for r in filas])
    n = len(filas)
    print(f"\nCorrelación de rangos (Spearman): rho = {rho:.3f}, n = {n}")

    # Intervalo aproximado por transformación de Fisher. Con n pequeña es
    # ancho a propósito: esa anchura es el resultado principal.
    if n > 3 and abs(rho) < 1:
        z = 0.5 * math.log((1 + rho) / (1 - rho))
        se = 1 / math.sqrt(n - 3)
        lo, hi = (math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se))
        print(f"IC 95% aproximado: [{lo:.2f}, {hi:.2f}]")
        if lo < 0 < hi:
            print("\nEl intervalo cruza cero. Con esta n, el resultado es "
                  "compatible con ausencia de asociación.")

    print("\nRecuerda: `exp-4` (desenmascaramiento) sigue sin descartarse.")
    print("Una correlación positiva aquí no distingue inducción de "
          "desenmascaramiento.")


if __name__ == "__main__":
    main()
