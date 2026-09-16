#!/usr/bin/env python3
"""
Prepara espacial/densidades.csv y espacial/parcelas.csv desde neuromaps.

ESTE SCRIPT NO CORRE EN EL CONTENEDOR DE CLAUDE: los mapas viven en OSF y
figshare, que están fuera de la red permitida. Córrelo en tu MacBook.

    pip install neuromaps nibabel nilearn numpy pandas --break-system-packages
    python3 preparar_mapas.py --atlas Schaefer2018_100Parcels_7Networks

Qué hace:
1. Descarga las anotaciones de densidad de receptor de neuromaps
   (derivadas de PET, ya normalizadas a espacio común).
2. Las promedia dentro de cada parcela de la parcelación elegida.
3. Escribe densidades.csv (parcela × receptor) y parcelas.csv
   (parcela, x, y, z, network).

REGLA DEL PROYECTO: una sola parcelación para todo. Si cambias de atlas,
se invalidan todas las aristas spatially_similar ya calculadas y hay que
regenerarlas. Anótalo en PENDIENTES.md antes de cambiar.

ADVERTENCIAS QUE HAY QUE LEER ANTES DE USAR LOS DATOS
-----------------------------------------------------
- Cada mapa viene de una muestra distinta, normalmente de decenas de
  adultos jóvenes sanos. No son el mismo estudio ni la misma población.
- Un receptor puede tener varios trazadores con mapas discrepantes.
  Registra cuál usaste en el campo `tracer` del nodo spatialmap.
- La cobertura subcortical de muchos mapas corticales es mala o nula.
- El origen de los mapas compilados es Hansen et al., Nature Neuroscience
  2022. VERIFICA la cita antes de usarla: está dada de memoria.
"""

import argparse
import sys

FALTA = """
Falta una dependencia: {0}

    pip install neuromaps nibabel nilearn numpy pandas --break-system-packages

neuromaps descarga datos la primera vez; necesita conexión.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default="Schaefer2018_100Parcels_7Networks",
                    help="Parcelación. Debe ser la MISMA en todo el proyecto.")
    ap.add_argument("--salida", default="espacial")
    ap.add_argument("--listar", action="store_true",
                    help="Solo lista las anotaciones disponibles y sale.")
    a = ap.parse_args()

    try:
        import numpy as np
        import pandas as pd
        from neuromaps import datasets, transforms, parcellate
        from nilearn import datasets as nid
    except ImportError as e:
        sys.exit(FALTA.format(e.name))

    import os
    os.makedirs(a.salida, exist_ok=True)

    anns = datasets.available_annotations()
    if a.listar:
        for s, d, sp, den in sorted(anns):
            print(f"{s:<18} {d:<22} {sp:<10} {den}")
        print(f"\n{len(anns)} anotaciones. Filtra las de receptor y pon sus "
              f"nombres en RECEPTORES abajo.")
        return

    # Ajusta esta lista a lo que necesites. El nombre corto es el que
    # aparecerá como columna y el que el grafo cruzará con `gene`/`name`.
    RECEPTORES = {
        "5HT1A": ("savli2012", "5HT1a"),
        "5HT2A": ("beliveau2017", "5HT2a"),
        "SERT":  ("beliveau2017", "5HTT"),
        "D1":    ("kaller2017", "D1"),
        "D2":    ("sandiego2015", "D2"),
        "DAT":   ("dukart2018", "DAT"),
        "NET":   ("ding2010", "NET"),
        "MOR":   ("kantonen2020", "MU"),
        "CB1":   ("normandin2015", "CB1"),
        "M1":    ("naganawa2020", "M1"),
        "GABAa": ("norgaard2021", "GABAa"),
        "NMDA":  ("galovic2021", "NMDA"),
    }

    schaefer = nid.fetch_atlas_schaefer_2018(
        n_rois=int(a.atlas.split("Parcels")[0].split("_")[-1]),
        yeo_networks=7)
    parc = parcellate.Parcellater(schaefer.maps, "MNI152")
    etiquetas = [l.decode() if isinstance(l, bytes) else l
                 for l in schaefer.labels]

    datos, faltantes = {}, []
    for corto, (fuente, desc) in RECEPTORES.items():
        try:
            ann = datasets.fetch_annotation(source=fuente, desc=desc)
            mni = transforms.fsaverage_to_mni152(ann, "1mm") \
                if isinstance(ann, tuple) else ann
            datos[corto] = np.asarray(parc.fit_transform(mni, "MNI152")).ravel()
            print(f"  ✓ {corto:<8} {fuente}/{desc}")
        except Exception as e:                       # noqa: BLE001
            faltantes.append(f"{corto} ({fuente}/{desc}): {e}")

    if not datos:
        sys.exit("No se pudo traer ninguna anotación. Revisa la lista con "
                 "--listar y corrige RECEPTORES.")

    df = pd.DataFrame(datos)
    df.insert(0, "parcela", etiquetas[:len(df)])
    df.to_csv(f"{a.salida}/densidades.csv", index=False)

    from nilearn import image, plotting
    coords = plotting.find_parcellation_cut_coords(schaefer.maps)
    pd.DataFrame({
        "parcela": etiquetas[:len(coords)],
        "x": coords[:, 0], "y": coords[:, 1], "z": coords[:, 2],
        "network": [e.split("_")[2] if e.count("_") > 2 else ""
                    for e in etiquetas[:len(coords)]],
    }).to_csv(f"{a.salida}/parcelas.csv", index=False)

    print(f"\n✓ {a.salida}/densidades.csv  ({df.shape[0]} parcelas, "
          f"{df.shape[1]-1} mapas)")
    print(f"✓ {a.salida}/parcelas.csv")
    if faltantes:
        print("\n! No se pudieron traer:")
        for x in faltantes:
            print("   " + x)
    print("\nFalta el gradiente funcional principal (columna gradient1).")
    print("Se obtiene con brainspace sobre una matriz de conectividad; "
          "no está automatizado aquí.")


if __name__ == "__main__":
    main()
