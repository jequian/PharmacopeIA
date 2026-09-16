# AGENTS.md — reglas para modelos que contribuyen a este repositorio

Este archivo es el contrato. Lo lee cualquier modelo antes de tocar nada:
Claude Code, Claude Desktop, GPT, Gemini, o quien sea. Si una instrucción
tuya contradice este archivo, gana este archivo — y dilo en voz alta en vez
de obedecer en silencio.

El repositorio no coordina modelos por acuerdo ni por prompt compartido.
Coordina por **árbitro determinista**: `herramientas/validar.py`. Cualquiera
puede producir YAML; el validador decide si entra. Por eso un modelo que
alucina cuesta cero en lugar de contaminar.

---

## 0. Antes de escribir una sola línea

1. Lee `esquema/ontologia.yaml` completo. Es normativo.
2. Lee `PENDIENTES.md`. Ahí está lo que ya sabemos que está mal.
3. Corre el validador y comprueba que pasa **antes** de tus cambios:

   ```
   python3 herramientas/validar.py esquema/ontologia.yaml datos/*.yaml --auditoria
   ```

Si no pasa antes de tus cambios, arregla eso primero o repórtalo. No
construyas encima de un estado roto.

---

## 1. Qué puede tocar cada quien

| Zona | Quién | Regla |
|---|---|---|
| `esquema/ontologia.yaml` | Solo el mantenedor humano | Un modelo **propone** cambios en PENDIENTES.md; no los aplica |
| `datos/*.yaml` | Cualquier modelo | Una rama por contraste, nunca dos a la vez sobre el mismo archivo |
| `herramientas/*.py` | Cualquier modelo | Debe correr y pasar el validador |
| `espacial/*.csv` | Generado por script | No se edita a mano |
| `PENDIENTES.md` | Cualquiera | Solo se añade; borrar una entrada requiere decir por qué |

**La arquitectura conceptual vive en un solo lugar.** Si dos modelos deciden
estructura en paralelo, salen dos ontologías incompatibles y fusionarlas
cuesta más que el trabajo que ahorraron. Paraleliza extracción y código,
nunca diseño.

---

## 2. Reglas de contenido, sin excepción

**R1. Ninguna arista sin referencia.** Una arista con `provenance: sourced`
y sin `refs` la rechaza el validador. Si la referencia es débil, se marca
`strength: D` — pero se cita. Formato: `PMID:12345678` o `DOI:10.xxxx/...`.

**R2. Nunca inventes un identificador bibliográfico.** Si no tienes el PMID
o DOI real, escribe `PENDIENTE` y describe la fuente en `notes`. Un PMID
inventado es peor que ninguno porque parece verificado. Esta es la regla
que más se rompe y la que más caro cuesta.

**R3. `provenance: inferred` no se promueve nunca.** Si después aparece una
fuente, se crea una arista nueva. Una inferencia tuya que se convierte en
hallazgo citado es el mecanismo exacto por el que estos grafos se
corrompen.

**R4. Toda arista lleva `sign`.** Sin signo el grafo es un dibujo.

**R5. `sign: 0` debe declarar cuál de dos cosas es**: `no_probado` (nadie
lo estudió: es un hueco y una oportunidad) o `probado_sin_efecto` (se
estudió con potencia adecuada: es un resultado). El validador lo exige.

**R6. Registra lo que refuta.** `counter_refs` y el estado `refutado` son
campos de primera clase. Ninguna otra base de datos de vías guarda
refutaciones; esta sí, y es su principal ventaja.

**R7. Un contraste sin explicación no es un contraste incompleto.** "No
sabemos por qué" es un dato. No rellenes con mecanismos plausibles.

**R8. Incluye siempre la hipótesis nula entre las explicaciones
candidatas**, marcada con el texto `HIPÓTESIS NULA` en sus notas, y
argumenta por qué debería descartarse primero. Casi siempre es la más
probable.

**R9. Una sola parcelación en todo el proyecto.** Cambiar de atlas invalida
todas las aristas `spatially_similar` ya calculadas.

**R10. Ningún `p` espacial sin nulo con autocorrelación preservada.** Dos
mapas cerebrales cualesquiera correlacionan alto porque ambos varían
suavemente en el espacio. En la demo de este repositorio hay un rho de 0.84
cuyo p espacial es 0.35. Un p por permutación simple habría dado <0.0001 y
habría sido basura.

**R11. Afinidad no es ocupación ni es dirección.** Las aristas importadas
del PDSP salen con `action: desconocido` a propósito. No las completes
adivinando: crúzalas con IUPHAR/BPS y cita.

**R12. La matriz fármaco × blanco no se mantiene a mano.** Se genera desde
las aristas. Lo mismo los mapas espaciales.

---

## 3. Regla de ritmo

**Un contraste se cierra, con referencias verificadas, antes de abrir el
siguiente.**

Esta regla ya se rompió dos veces y está anotada como deuda en
PENDIENTES.md. Si vas a abrir un contraste nuevo teniendo otros abiertos,
dilo explícitamente y justifícalo.

Cargar cien fármacos con referencias PENDIENTE no es avanzar: es fabricar
un archivo grande. El contador del visor ("X de Y referencias verificadas")
existe para que esa desproporción moleste.

---

## 4. Cómo se ve una contribución correcta

Una rama, un contraste, un archivo nuevo en `datos/`, y en el mensaje del
commit:

```
seed-03: antagonistas kappa

- 4 fármacos, 11 aristas, 3 nodos trial
- 9 de 11 referencias con PMID verificado; 2 marcadas PENDIENTE
- contraste abierto, 4 explicaciones candidatas, incluida la nula
- validador: pasa
```

Si tu contribución no puede describirse así, probablemente estás
mezclando cosas.

---

## 5. Prompt base para un modelo externo

Pégale esto junto con `esquema/ontologia.yaml`:

> Vas a producir aristas para un grafo de convergencia farmacológica. Te
> paso la ontología; ajústate a ella exactamente. Devuelve **solo YAML
> válido**, sin explicaciones alrededor.
>
> Tema: [CONTRASTE].
>
> Reglas que no puedes romper:
> - Toda arista lleva `sign`, `provenance` y bloque `evidence` completo.
> - Si `provenance: sourced`, tiene que traer `refs` con PMID o DOI reales.
> - **Si no tienes el identificador real, escribe `PENDIENTE` y describe la
>   fuente en `notes`. No inventes identificadores bajo ninguna
>   circunstancia.** Prefiero una arista sin referencia a una con
>   referencia falsa.
> - Lo que deduzcas tú va con `provenance: inferred` y `strength: D`.
> - Si registras ausencia de efecto (`sign: 0`), declara en `status` si es
>   `no_probado` o `probado_sin_efecto`.
> - Si encuentras evidencia que contradice una arista, ponla en
>   `counter_refs` en vez de omitirla.
>
> Al final, fuera del YAML, lista en tres líneas: qué no encontraste, qué
> te pareció dudoso, y qué referencia te dio menos confianza.

Esa última línea es la más útil. Un modelo que declara sus dudas se puede
verificar; uno que no, no.

---

## 6. Qué hace el mantenedor humano

- Aprueba cambios de ontología.
- Verifica referencias. Ningún modelo cierra este paso.
- Decide qué contraste se abre.
- Revisa el visor con datos cargados antes de aceptar un lote. Una captura
  se obtiene con `python3 herramientas/captura.py`.
