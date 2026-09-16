# Grafo de convergencia farmacológica

Grafo por capas de blancos, vías, circuitos y fenotipos, construido para
contestar dos preguntas:

1. ¿En qué convergen los fármacos con efecto afectivo, si es que convergen?
2. ¿Por qué fármacos que comparten un mecanismo nominal tienen desenlaces
   clínicos distintos, y por qué dentro de un mismo diagnóstico hay
   perfiles que responden mejor a uno que a otro?

La estructura central no son las vías: es el **contraste**. Un conjunto de
fármacos que comparten un mecanismo y difieren en desenlace. Si el
mecanismo compartido bastara, el contraste no existiría.

Lo que distingue a este grafo de una base de datos de vías es que registra
lo que **no** se sabe y lo que se ha **refutado**: hay estados
`no_probado`, `probado_sin_efecto` y `refutado`, un campo `counter_refs`, y
una marca de proveniencia que separa lo que dice una fuente de lo que
dedujimos nosotros.

## Estructura

```
esquema/ontologia.yaml      normativo: tipos de nodo, arista y evidencia
datos/*.yaml                catálogos y contrastes
espacial/*.csv              densidades de receptor por parcela
herramientas/*.py           validador, importadores, análisis, visor
AGENTS.md                   reglas para modelos que contribuyen
PENDIENTES.md               deuda, dudas y referencias por verificar
```

## Uso

```bash
pip install pyyaml numpy --break-system-packages

# validar
python3 herramientas/validar.py esquema/ontologia.yaml datos/*.yaml --auditoria

# visor (genera visor.html autocontenido)
python3 herramientas/construir_visor.py

# importar afinidades del PDSP (descarga previa desde pdsp.unc.edu)
python3 herramientas/importar_pdsp.py KiDatabase.csv \
        --catalogo datos/cat-01-farmacos.yaml --solo-catalogo --umbral-ki 100

# mapas espaciales predichos
python3 herramientas/mapa_predicho.py --datos datos \
        --densidades espacial/densidades-DEMO.csv \
        --parcelas espacial/parcelas-DEMO.csv --contra gradient1 --nulos 5000
```

## La capa espacial

Es el único nivel donde fármaco y enfermedad se miden en las mismas
unidades. La afinidad de un fármaco por cada blanco se mide con
radioligando; la densidad de cada blanco por parcela se mide con PET.
Multiplicando y sumando sale un mapa espacial predicho, comparable contra
cualquier otro mapa cerebral.

Los archivos `-DEMO` son **sintéticos**, para probar la tubería. Los reales
se generan con `herramientas/preparar_mapas.py`, que no corre en entornos
sin acceso a OSF.

## Advertencia

Casi todas las referencias están marcadas `PENDIENTE`. El contador del
visor lo muestra. Nada de lo cargado está verificado.
