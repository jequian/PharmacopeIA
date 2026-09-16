# Pendientes

Estado al cierre de la sesión de construcción del esquema.
El validador (`--auditoria`) detecta automáticamente lo mecánico:
referencias PENDIENTE, aristas sin referencia, aristas inferidas,
contrastes abiertos. Este archivo es para lo que el validador no puede
ver: decisiones, dudas y deuda conceptual.

---

## 1. Referencias por verificar

Todas las referencias del grafo dicen PENDIENTE salvo una. Nada de lo
cargado está verificado. Prioridad de verificación:

**Alta — sostienen una explicación candidata**
- [ ] Poolos, Migliore & Johnston sobre potenciación de la corriente Ih
      por lamotrigina en dendritas apicales de CA1. PMID citado de memoria
      como 12118259. Es el único PMID concreto del grafo y es la pieza
      central de `exp-2` en el contraste de bloqueadores de sodio.
- [ ] Incidencia de sintomatología obsesiva bajo clozapina. Deliberadamente
      NO puse cifra porque no confío en mi memoria del rango. Verificar y
      registrar como rango, no como número único.
- [ ] Reportes de caso de reversión con cariprazina. Contar cuántos hay
      realmente. Si son menos de cinco, bajar la arista a strength D y
      anotarlo en el contraste.
- [ ] Metaanálisis de potenciación antipsicótica en TOC, con la magnitud
      del efecto en el subgrupo con tics.

**Media — estructura del contraste**
- [ ] Indicación exacta aprobada de lamotrigina en bipolar. Confirmar que
      es mantenimiento y no depresión aguda.
- [ ] Ensayos de fenitoína en manía: ¿existen, con qué n, de quién?
- [ ] Fracaso de topiramato en manía: cuál ensayo, cuál desenlace.
- [ ] Relevancia de la inhibición de GSK-3 beta por valproato a
      concentraciones terapéuticas. Está marcada como contestada sin
      tener la contrarreferencia.

**Baja — descargables en bloque**
- [ ] Afinidades de unión de todo el catálogo. Fuente: base Ki del PDSP
      en `pdsp.unc.edu/databases/kidb.php`, que exporta CSV. Esto NO se
      transcribe a mano: hay que escribir un importador.

---

## 2. Decisiones de esquema sin resolver

- [ ] **Ocupación de receptor no tiene campo.** El contraste del TOC
      depende de la distinción entre afinidad y ocupación a dosis
      terapéutica, y el esquema solo tiene `affinity_ki_nm`. Hace falta
      algo como `occupancy_pct` con dosis asociada, o el argumento no se
      puede codificar.
- [ ] **Dosis no existe en el modelo.** Varios efectos son
      dosis-dependientes y hoy no hay dónde ponerlo.
- [ ] **Metabolitos activos.** Norclozapina, desmetilcitalopram,
      7-hidroximitraginina. Hoy tendrían que ser nodos `drug` separados,
      lo cual es feo. Alternativa: un tipo de arista `metabolizes_to`.
- [ ] **Tiempo.** Aguda contra mantenimiento no se distingue bien: el
      campo `temporal` está en la arista pero no diferencia "el fármaco
      actúa rápido" de "el ensayo midió mantenimiento".
- [ ] **Ausencia de evidencia contra evidencia de ausencia.** Hoy ambas
      caerían en `sign: 0`. Hacen falta valores distintos: nunca probado
      contra probado y negativo.
- [ ] ¿Los ensayos deberían poder conectarse a `contrast` directamente,
      para decir "este ensayo resolvería este contraste"?

---

## 3. Contrastes abiertos

| ID | Estado | Falta |
|---|---|---|
| `contrast:bloqueadores-sodio` | 6 miembros, 3 explicaciones | Descartar primero la hipótesis nula (exp-3): que el contraste refleje qué diseño se usó con cada fármaco, no biología |
| `contrast:d2-disordinal-toc` | 4 miembros, 4 explicaciones | Descartar primero exp-4, el desenmascaramiento. Es la explicación más probable y la menos atractiva |

Análisis más barato disponible hoy, sin permisos ni pacientes: `exp-2`
del contraste del TOC. Ordenar los antipsicóticos por la razón entre
afinidad 5-HT2 y ocupación D2, y correlacionar con la incidencia
reportada de sintomatología obsesiva. Los datos de afinidad son
descargables; los de incidencia están en la literatura.

---

## 4. Contrastes por construir

Ordenados por valor esperado.

- [ ] **Antagonistas kappa.** Aticaprant y navacaprant fracasaron en fase
      III con el mismo mecanismo y estrategias de enriquecimiento
      distintas. El caso más limpio que existe de fallo de selección de
      pacientes con blanco bien definido. Estrena el tipo de nodo `trial`.
- [ ] **Anticrisis con efecto afectivo negativo.** Levetiracetam induce
      irritabilidad y disforia; perampanel tiene advertencia regulatoria
      por agresividad. Perampanel es antagonista AMPA, dirección opuesta a
      los moduladores alostéricos positivos de AMPA que se desarrollan
      para depresión. Aristas `induces`, no `treats`.
- [ ] **Clomipramina contra el resto de tricíclicos en TOC.** Un solo
      miembro de la clase funciona. Mismo patrón lógico que lamotrigina.
- [ ] **Zuranolona.** Eficaz en depresión posparto, fracasó en depresión
      mayor general. Enriquecimiento por subpoblación biológicamente
      definida que sí funcionó.
- [ ] **Tianeptina.** Potencia la recaptura de serotonina, dirección
      opuesta a los ISRS, y tiene eficacia reportada. Desafía de frente
      la hipótesis monoaminérgica.
- [ ] **Deterioro cognitivo en esquizofrenia.** Encenicline, pomaglumetad,
      luvadaxistat, iclepertin: todos con señal farmacodinámica en
      electroencefalograma en fase temprana, todos fracasados en fase
      tardía sin selección. El ejemplo canónico de `fallo_seleccion_pacientes`.

---

## 5. Por implementar

- [ ] Importador de la base Ki del PDSP a aristas `acts_on`.
- [ ] Vista de grafo, no solo matriz. Hoy el visor muestra matriz,
      contrastes y catálogo; falta la red navegable por capas.
- [ ] Consulta de caminos: dado un fármaco y un fenotipo, listar todas
      las rutas que los conectan cruzando las cuatro capas.
- [ ] Detección de convergencia: dado un conjunto de fármacos, encontrar
      los nodos por los que todos pasan. Es la función que contesta la
      pregunta original del proyecto.
- [ ] Editor de aristas en el visor, para no escribir YAML a mano.
- [ ] Integración y análisis de fenotipado digital con Beiwe (ver sección 10).

---

## 6. Deuda conceptual

- **Sesgo de armado.** La conversación que originó este proyecto empezó
  por TrkB, y buena parte de la estructura está organizada alrededor de
  ese eje. La coherencia aparente puede ser mía, no del campo. Al menos
  un contraste debería construirse desde una línea sin relación con
  plasticidad, para comprobar que el esquema no está sesgado.

- **Completitud ilusoria.** Un grafo de mil nodos se siente como
  conocimiento. Las protecciones vigentes son el campo `provenance`, el
  rechazo automático de aristas `sourced` sin referencia, y la existencia
  de `counter_refs` y del estado `refutado`. Ninguna sirve si se dejan de
  usar con rigor.

- **Regla de ritmo, adoptada y no probada:** un contraste se cierra con
  referencias verificadas antes de abrir el siguiente. Hoy hay dos
  abiertos y cero cerrados. Si al abrir el tercero siguen los dos
  abiertos, la regla se rompió.

---

## 7. Bitácora de cambios del esquema

**v0.2** — añadidos tras la primera revisión de uso:
- `occupancy` en `acts_on`: porcentaje, método (PET/SPECT/estimado), dosis
  asociada y referencias propias. Afinidad y ocupación son cosas distintas
  y el contraste del TOC depende de la diferencia.
- `dose_regimen` como objeto reutilizable. Sin él, dos aristas del mismo
  fármaco con signo opuesto parecen un error de captura en vez de un
  efecto dosis-dependiente.
- Estados `no_probado` y `probado_sin_efecto`. El validador ahora RECHAZA
  cualquier arista de efecto con `sign: 0` que no declare cuál de los dos
  es. Nunca-se-probó es una oportunidad de investigación;
  se-probó-y-es-nulo es un resultado. Confundirlos era el error más caro.

Pendiente de la misma revisión, sin implementar:
- [ ] `metabolizes_to` para metabolitos activos (norclozapina,
      desmetilcitalopram, 7-hidroximitraginina).
- [ ] Separar "el fármaco actúa rápido" de "el ensayo midió mantenimiento".
      Hoy ambas caen en `temporal`.
- [ ] Poder conectar un `trial` a un `contrast` para decir "este ensayo
      resolvería este contraste".

---

## 8. Estado tras cargar el volcado del PDSP

Importadas 449 aristas `acts_on` con Ki ≤ 100 nM sobre 44 fármacos del
catálogo. Sin umbral serían 1713 aristas y 245 blancos.

- [ ] **Todas las aristas importadas tienen `action: desconocido`.** El
      PDSP da afinidad de unión, no dirección. Hay que completar agonista
      / antagonista / modulador cruzando con IUPHAR/BPS. Sin esto la
      matriz muestra 449 signos de interrogación.
- [ ] **228 moléculas nuevas creadas por el importador**, con
      `subtype: receptor_gpcr` puesto por defecto y nombres derivados del
      campo Name del PDSP. Hay duplicados semánticos que hay que fusionar:
      `mol:5-ht2` y `mol:5HT2A`, `mol:cholinergic-muscarinic` y `mol:M1`,
      `mol:5-ht7s` y el receptor 5-HT7. Revisar y consolidar.
- [ ] **El importador conserva el Ki más bajo** de todas las mediciones de
      un par. Eso mezcla especies y tejidos, y sesga sistemáticamente hacia
      la afinidad más alta reportada. Alternativa: mediana, o preferir
      humano cuando exista.
- [ ] **La matriz con 105 columnas no es legible.** Faltan filtros por
      clase de fármaco, por blanco y por afinidad.

Ausencias confirmadas, no son fallo del cruce: lamotrigina, valproato,
carbamazepina, levetiracetam, litio y el resto de anticrisis no aparecen
en el PDSP porque actúan sobre canales y enzimas, no sobre receptores de
unión de radioligando. El contraste de bloqueadores de sodio no se puede
alimentar desde esta fuente.

---

## 9. Capa espacial — estado

Implementada la estructura: nodos `parcel` y `spatialmap`, aristas
`has_density`, `spans` y `spatially_similar`, y
`herramientas/mapa_predicho.py`.

Probada de punta a punta con datos **sintéticos** (`espacial/*-DEMO.csv`).
La demostración dejó dos cosas claras:

- [ ] **Un solo blanco domina el peso en la mayoría de los fármacos.** Con
      pesos proporcionales a 1/Ki, el mapa de la fluoxetina es 97% el mapa
      del transportador de serotonina, y el de la amitriptilina es 83% el
      del receptor H1. Para esos fármacos el "mapa del fármaco" no aporta
      nada sobre el mapa del receptor dominante. Hay que decidir: usar
      ocupación fraccional a una concentración realista en vez de 1/Ki
      crudo, o aceptar que el método solo discrimina entre fármacos
      genuinamente promiscuos (clozapina, quetiapina, antipsicóticos).
- [ ] **El nulo espacial cambia todo.** En la demo, un rho de 0.84 contra
      el gradiente dio p espacial de 0.35. Un nulo por permutación simple
      habría dado p<0.0001. Confirma que la regla R10 de AGENTS.md no es
      pedantería.

Por hacer:
- [ ] Correr `herramientas/preparar_mapas.py` en el MacBook para generar
      las densidades reales. No corre en el contenedor: los mapas están en
      OSF y figshare, fuera de la red permitida.
- [ ] Verificar la cita de origen de los mapas (Hansen et al., Nature
      Neuroscience 2022). Dada de memoria.
- [ ] Obtener el gradiente funcional principal. Requiere brainspace sobre
      una matriz de conectividad; no automatizado.
- [ ] Decidir la parcelación definitiva y anotarla. Cambiarla después
      invalida todo lo calculado.
- [ ] 94 de los blancos del grafo no tienen mapa de densidad. La cobertura
      PET es mucho más estrecha que la del PDSP.

---

## 10. Fenotipado digital y análisis de datos continuos (Beiwe)

Interés en incorporar la plataforma **Beiwe** ([onnela-lab/beiwe](https://github.com/onnela-lab/beiwe.git), Onnela Lab / Harvard) y análisis relativos a esta modalidad de datos:

- [ ] **Modalidad de datos:** Fenotipado digital continuo (sensores pasivos: acelerometría, GPS/movilidad, patrones de comunicación/uso de smartphone, y encuestas activas EMA) en contraposición o complemento a escalas clínicas transversales discretas (e.g., HAM-D, Y-BOCS, MADRS).
- [ ] **Mapeo al esquema:** Definir cómo representar en el grafo métricas continuas derivadas de fenotipado digital (estabilidad circadiana, fragmentación del sueño, variabilidad de movilidad, latencia de respuesta digital) dentro de los nodos `phenotype` o asociados a desenlaces en nodos `trial`.
- [ ] **Análisis de contraste:** Explorar si las discrepancias de respuesta clínica entre fármacos con mecanismo nominal idéntico se manifiestan tempranamente en marcadores digitales objetivos (por ejemplo, cambios motores o de ritmo sueño-vigilia previo a la respuesta sindrómica formal).
- [ ] **Pipeline de ingesta:** Desarrollar herramientas (`herramientas/`) para ingerir y resumir características de series temporales conductuales provenientes de Beiwe para correlacionarlas con vías y afinidades del grafo.
