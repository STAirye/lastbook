# Mapas detallados para Paraguay: una propuesta

> Versión en español de [REGIONS-PY.md](REGIONS-PY.md). Si las dos difieren, vale la versión en inglés, que es la que se
> discute en el repositorio.

Esta es una propuesta para discutir, no una decisión. Responde, para Paraguay, las preguntas que [MAPS.md](MAPS.md) pide
contestar antes de que la cobertura vaya más allá de Estados Unidos: qué fuente abierta reemplaza a cada lista federal,
con qué licencia, qué es un "estado" en el país y cómo se escriben las direcciones. Sigue la forma de
[REGIONS.md](REGIONS.md), [REGIONS-AR.md](REGIONS-AR.md) y [REGIONS-LK.md](REGIONS-LK.md) y busca alimentar la misma
discusión de diseño (issues #23, #25 y #31). La versión legible por máquina es
[regions-py-proposed.json](regions-py-proposed.json).

Nada de esto cambia la app, el motor ni una compilación. Ningún código lee el JSON, y nada de esto se distribuye: las
compilaciones empaquetan solo `web/` y `content/`.

**Cómo se verificó.** La investigación se hizo el 17 de noviembre de 2026. Cada dato lleva una de estas marcas:

- **abierta**: se abrió y se leyó la página, el archivo o la respuesta de la API;
- **calculada**: la cifra se calculó aquí a partir de un archivo descargado (se nombran el archivo y el método);
- **solo búsqueda**: el dato se vio en un resultado de búsqueda, pero no se abrió la página;
- **conocimiento general**: dicho de memoria, sin abrir ninguna fuente; necesita la revisión de alguien del país;
- **sin verificar**: no se pudo llegar a la página o leerla; la fila dice qué falta.

"No se encontró" quiere decir que no se encontró buscando en la web. El portal nacional de datos abiertos
(`datos.gov.py`) mostraba una página de mantenimiento el 17 de noviembre de 2026, así que no se pudo buscar en su
catálogo. Tampoco se pudo llegar a la API de Overpass, así que las cifras de OSM se contaron sobre el extracto de
Geofabrik.

## Qué es una región

Paraguay tiene 17 departamentos y el distrito capital, Asunción. La propuesta es **una sola región para todo el país**,
con el código `PY`, como REGIONS.md propone para Guyana y REGIONS-LK.md para Sri Lanka. Un `PY` solo no choca con ningún
código de `STATE_CODES` (`engine/address_search.py`).

Por qué una sola región:

- **Tamaño.** El polígono de Paraguay en el COD-AB de OCHA tiene 399.603 km² (su atributo `area_sqkm`; la cifra oficial
  es 406.752 km², conocimiento general). Es algo menos que California (423.970 km², conocimiento general), que Lastbook
  ya distribuye como un solo mapa estatal. El extracto de OSM de todo el país pesa 147 MB, cerca de los 137 MB de Sri
  Lanka.
- **Los departamentos son chicos.** Central tiene 2.413 km² y Asunción 129 km², mucho menos que la mayoría de los
  estados de EE. UU.
- **Cómo vive y se mueve la gente.** El Gran Asunción abarca la capital y gran parte de Central. Incluye también
  distritos de Presidente Hayes al otro lado del río y, según algunas definiciones, partes de Cordillera y Paraguarí
  (solo búsqueda). Quien vive ahí y elige el mapa de un solo departamento pierde parte de su propia ciudad, el mismo
  problema que REGIONS-AR.md describe para Buenos Aires.
- **El oeste está casi vacío.** Los tres departamentos occidentales (Presidente Hayes, Boquerón y Alto Paraguay) ocupan
  el 60 % del territorio (según las cifras `area_sqkm` de abajo). Ahí vive solo una pequeña parte de la población
  (conocimiento general; sin comparar con el censo 2022), así que sus datos deberían sumar poco a un mapa de todo el
  país.

Si los mantenedores prefieren regiones más chicas, abajo están los rectángulos por departamento. Una opción intermedia
son dos regiones: la Región Oriental (14 departamentos y Asunción) y el Chaco (los tres departamentos occidentales),
divididas por el río Paraguay. Esa división también cortaría el Gran Asunción, cuyo lado chaqueño está en Presidente
Hayes.

### Rectángulo

| Código | Nombre | Rectángulo (oeste, sur, este, norte) | Con margen de 0,15° | Tomado de |
|---|---|---|---|---|
| `PY` | Paraguay | -62.6446, -27.5918, -54.2589, -19.2876 | -62.80, -27.75, -54.10, -19.13 | Nivel 0 del COD-AB de OCHA (calculado) |

El rectángulo es la extensión de todos los vértices del polígono de nivel 0 de OCHA para Paraguay
(`pry_admin0.geojson`, fuente INE, vigente desde el 29 de julio de 2026; descargado y calculado el 17 de noviembre de
2026), menos/más 0,15° y redondeado hacia afuera a 0,01°, el mismo margen que usa `map_sets.state` para los estados de
EE. UU. El polígono de recorte de Geofabrik (`paraguay.poly`, abierto) da un rectángulo más holgado, -62.6948, -27.6568,
-54.2018, -19.2401, como es de esperar para un polígono dibujado alrededor de la frontera.

**Vecinos dentro del rectángulo.** Un rectángulo alrededor de Paraguay incluye mucho de sus vecinos (según una muestra
de puntos dentro del rectángulo; sin medir). En Argentina: toda la provincia de Formosa, la mayor parte de la provincia
del Chaco (con Resistencia), el norte de Corrientes (con la ciudad de Corrientes), la mayor parte de la provincia de
Misiones, una esquina de Santiago del Estero y una franja mínima de Salta. En Brasil: gran parte de Mato Grosso do Sul,
el borde oeste de Paraná (con Foz do Iguaçu) y una esquina de Rio Grande do Sul. En Bolivia: partes del sureste.

Varias ciudades paraguayas tienen una ciudad gemela al otro lado de la frontera: Encarnación y Posadas, Ciudad del Este
y Foz do Iguaçu, Pedro Juan Caballero y Ponta Porã, Asunción y Clorinda.

El extracto de Geofabrik ya está cortado a pocos kilómetros de la frontera, así que una primera compilación hecha con
él casi no trae nada de los vecinos, y corta las ciudades gemelas. Mantener enteras Posadas, Foz do Iguaçu, Ponta Porã
y Clorinda exige sumar datos de los extractos de Argentina y Brasil. La sugerencia es usar la frontera como borde en una
primera compilación y más adelante sumar una franja (por ejemplo 20 km) para las ciudades gemelas. Esto se deja a
decisión de los mantenedores.

No se conoce ningún límite en disputa aquí (conocimiento general); el punto se menciona solo para que se decida una vez
para todas las regiones (punto 6 de REGIONS.md).

### Departamentos, si se quieren regiones más chicas

La ISO 3166-2:PY da `PY-ASU` para Asunción y `PY-1` a `PY-16` y `PY-19` para los departamentos (solo búsqueda; sin
verificar en el sitio de ISO). No existen `PY-17` ni `PY-18`.

**Ojo con la numeración.** Los p-codes de OCHA no coinciden con ISO en dos departamentos: en el COD-AB, `PY16` es
Boquerón y `PY17` es Alto Paraguay, mientras que ISO tiene `PY-16` para Alto Paraguay y `PY-19` para Boquerón. Todo lo
que una las dos listas debe hacerlo por nombre, no por número.

Los rectángulos se calcularon con los polígonos de nivel 1 de OCHA (`pry_admin1.geojson`, 18 elementos) con la misma
regla.

| Código ISO | P-code COD-AB | Nombre | Rectángulo (oeste, sur, este, norte) | Con margen de 0,15° | Superficie (km², `area_sqkm`) |
|---|---|---|---|---|---|
| `PY-ASU` | PY00 | Asunción | -57.6739, -25.3809, -57.5248, -25.2246 | -57.83, -25.54, -57.37, -25.07 | 129 |
| `PY-1` | PY01 | Concepción | -57.9938, -23.5095, -56.1258, -22.0791 | -58.15, -23.66, -55.97, -21.92 | 18.543 |
| `PY-2` | PY02 | San Pedro | -57.4735, -25.0193, -55.7020, -23.3007 | -57.63, -25.17, -55.55, -23.15 | 20.852 |
| `PY-3` | PY03 | Cordillera | -57.4783, -25.6690, -56.5614, -24.8433 | -57.63, -25.82, -56.41, -24.69 | 4.790 |
| `PY-4` | PY04 | Guairá | -56.7477, -26.1973, -55.6334, -25.5648 | -56.90, -26.35, -55.48, -25.41 | 3.870 |
| `PY-5` | PY05 | Caaguazú | -56.8115, -25.7084, -54.9232, -24.4655 | -56.97, -25.86, -54.77, -24.31 | 12.904 |
| `PY-6` | PY06 | Caazapá | -56.8491, -26.7944, -55.2482, -25.5236 | -57.00, -26.95, -55.09, -25.37 | 9.550 |
| `PY-7` | PY07 | Itapúa | -56.8848, -27.5918, -54.6482, -26.0922 | -57.04, -27.75, -54.49, -25.94 | 15.866 |
| `PY-8` | PY08 | Misiones | -57.7431, -27.4861, -56.6259, -26.3761 | -57.90, -27.64, -56.47, -26.22 | 8.160 |
| `PY-9` | PY09 | Paraguarí | -57.7494, -26.6196, -56.6076, -25.4018 | -57.90, -26.77, -56.45, -25.25 | 8.603 |
| `PY-10` | PY10 | Alto Paraná | -55.5506, -26.2571, -54.3458, -24.4762 | -55.71, -26.41, -54.19, -24.32 | 14.209 |
| `PY-11` | PY11 | Central | -57.8268, -26.0251, -57.1930, -25.0965 | -57.98, -26.18, -57.04, -24.94 | 2.413 |
| `PY-12` | PY12 | Ñeembucú | -58.6649, -27.4442, -57.1821, -25.7672 | -58.82, -27.60, -57.03, -25.61 | 11.675 |
| `PY-13` | PY13 | Amambay | -56.8261, -23.8309, -55.5045, -22.0745 | -56.98, -23.99, -55.35, -21.92 | 12.548 |
| `PY-14` | PY14 | Canindeyú | -56.1725, -24.7840, -54.2589, -23.5237 | -56.33, -24.94, -54.10, -23.37 | 15.029 |
| `PY-15` | PY15 | Presidente Hayes | -60.7854, -25.3543, -57.1493, -22.0762 | -60.94, -25.51, -56.99, -21.92 | 73.655 |
| `PY-16` | PY17 | Alto Paraguay | -61.9225, -22.3992, -57.8171, -19.2876 | -62.08, -22.55, -57.66, -19.13 | 78.542 |
| `PY-19` | PY16 | Boquerón | -62.6446, -23.8858, -59.3366, -20.0892 | -62.80, -24.04, -59.18, -19.93 | 88.265 |

Asunción está entre Central y el río Paraguay, y el rectángulo de Central ya contiene todo el de Asunción, así que un
mapa `PY-11` cortado por su rectángulo también trae Asunción. El área metropolitana es más amplia: incluye además el
lado de Villa Hayes, en Presidente Hayes. Un mapa del área metropolitana sería una agrupación aparte con su propio id,
como hace REGIONS-TH.md para Bangkok y sus alrededores, y no un `PY-11` que signifique más que Central.

**Ya en curso.** El PR #35 trae un rectángulo `py-asu` para Asunción (-57.94, -25.59, -57.34, -24.99), cortado del mismo
extracto de Geofabrik. Una región de todo el país reemplazaría ese rectángulo por el extracto completo; no necesita una
fuente nueva.

**Posible control cruzado.** El archivo ADM1 de geoBoundaries para Paraguay (CC BY 4.0, 18 unidades, a partir de los
departamentos de la DGEEC de 2012; metadatos abiertos) podría usarse para comprobar los rectángulos. No se descargó.

## Fuentes, capa por capa

OpenStreetMap es la base para una primera compilación, como para Guyana y Sri Lanka. El instituto de estadística (INE,
antes DGEEC) publica los límites censales, que según el propio INE son solo de referencia, y una cartografía censal de
2012 con calles, manzanas y agua. MapBiomas publica una serie nacional de cobertura del suelo. No se encontraron listas
nacionales abiertas de establecimientos de salud, cuarteles de bomberos ni represas.

| Capa (archivo) | Fuente en EE. UU. hoy | Propuesta para Paraguay | Publicador | Licencia | Marca |
|---|---|---|---|---|---|
| Rutas, agua, tierra (mapa base) | Extracto de OSM | Extracto de OSM `paraguay-latest.osm.pbf` (147 MB; el `.shp.zip` pesa 305 MB y el `.gpkg.zip` 312 MB), datos hasta el 16 de noviembre de 2026, 21:22 UTC | Colaboradores de OSM vía Geofabrik | ODbL 1.0 | abierta |
| Puntos de interés (`poi`) | OSM | OSM (conteos abajo) | Colaboradores de OSM | ODbL 1.0 | calculada |
| Lugares (`places.sqlite`) | GNIS, nomencladores del Censo, OSM | Niveles 1 a 4 del COD-AB de OCHA (departamentos, distritos y dos niveles más finos) y sus archivos `adminpoints` y `admincapitals`; lugares con nombre de OSM | OCHA, a partir del INE; colaboradores de OSM | CC BY-IGO; ODbL 1.0 | Ficha de HDX consultada. Descargas de admin0 y admin1 confirmadas. |
| Lugares y calles, oficial | | "Cartografía Digital 2012" del INE: departamentos, distritos, barrios y localidades, ciudades, manzanas, vías, vías principales, hidrografía y comunidades indígenas, en Shape, KML y GeoJSON para el país y cada departamento | INE | Licencia de Uso de la Información Pública del Gobierno Paraguayo | abierta |
| Relieve (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, como se propone para Guyana | ESA / Airbus | Licencia Copernicus WorldDEM-30 | como en REGIONS.md |
| Agua (`water.sqlite`) | NHD | Cursos y superficies de agua de OSM; hidrografía del INE 2012 para completar | Colaboradores de OSM; INE | ODbL 1.0; licencia del INE | abierta (lista de capas del INE) |
| Represas | NID | `waterway=dam` y `water=reservoir` de OSM; no se encontró un inventario abierto de represas | Colaboradores de OSM | ODbL 1.0 | calculada |
| Cultivos (`crops.sqlite`) | USDA Cropland Data Layer | MapBiomas Paraguay, mapas anuales de cobertura y uso del suelo de 1985 a 2023 (Colección 2, 30 m, de Landsat); ESA WorldCover 2021 como respaldo | MapBiomas Paraguay; consorcio ESA WorldCover | CC BY (ver notas); CC BY 4.0 | abierta (términos de uso); detalles de la colección solo búsqueda |
| Edificios (`buildings.sqlite`) | Huellas de Microsoft para EE. UU., alturas de OSM | Google Open Buildings v3 (Paraguay está en su lista de países; inferido en mayo de 2023); Microsoft Global ML Building Footprints para completar; alturas de OSM | Google; Microsoft; colaboradores de OSM | CC BY 4.0 u ODbL 1.0, a elección (Google); ver REGIONS.md para Microsoft; ODbL | abierta (página de Google); cobertura sin medir |
| Direcciones (`addresses/<código>.sqlite`) | Direcciones de Overture | **No se encontró ninguna.** El tema de direcciones de Overture lista 41 países, y Paraguay no está entre ellos | | | abierta |

### Puntos de ayuda y de recursos

Los conteos se hicieron con pyosmium sobre el extracto de Geofabrik de arriba (datos hasta el 16 de noviembre de 2026,
21:22 UTC). Cada conteo incluye nodos, vías y relaciones con la etiqueta.

| Tipo | Etiqueta OSM | Cantidad | Otra fuente | Marca |
|---|---|---|---|---|
| Hospitales | `amenity=hospital` | 387 | Lista del Ministerio de Salud (MSPBS), ver notas | calculada |
| Clínicas y consultorios | `amenity=clinic`, `amenity=doctors` | 657 (412 clínicas, 245 consultorios) | ídem | calculada |
| Farmacias | `amenity=pharmacy` | 1.377 | no se encontró | calculada |
| Cuarteles de bomberos | `amenity=fire_station` | 123 (100 con nombre) | Bomberos voluntarios (CBVP), ver notas | calculada |
| Policía | `amenity=police` | 1.508 | no se encontró | calculada |
| Agua potable | `amenity=drinking_water`, `man_made=water_tap`, `amenity=water_point` | 83 (56, 21, 6) | no se encontró | calculada |
| Pozos, torres de agua y tanques | `man_made=water_well`, `water_tower`, `storage_tank` | 1.738 (177 pozos, 935 torres, 626 tanques, contenido sin verificar) | no se encontró | calculada |
| Embalses y represas | `water=reservoir`, `waterway=dam` | 2.852 embalses (sin contar `landuse=reservoir`), 291 represas | no se encontró | calculada |
| Combustible | `amenity=fuel` | 1.577 | no se encontró | calculada |
| Bases de ambulancias | `emergency=ambulance_station` | 5 | no se encontró | calculada |
| Refugios y puntos de encuentro | `amenity=shelter`, `social_facility=shelter`, `emergency=assembly_point` | 289 (284, 5, 0) | Secretaría de Emergencia Nacional (SEN), ver notas | calculada |
| Escuelas | `amenity=school` | 4.748 | Datos abiertos del Ministerio de Educación (MEC), ver notas | calculada |

Notas:

- **Contar filas no es contar lugares.** En OSM un hospital suele figurar como un punto y otra vez como cada uno de sus
  edificios, y algunos laboratorios, consultorios y puestos de salud están etiquetados como hospitales. En un mapa de
  prueba de Central y Asunción, 163 filas de hospitales eran unos 113 lugares (agrupando las filas a menos de 150 m).
  Los conteos de arriba son un máximo.
- **Salud.** No se encontró una lista descargable de establecimientos de salud con coordenadas. Según los informes, el
  Ministerio de Salud tiene una: se comprometió a publicarla como datos abiertos, y un informe de 2021 para la OPS la
  obtuvo por nota oficial (ambos solo búsqueda). Pedirle al Ministerio la lista con una licencia abierta es el paso más
  útil para este mapa.
- **Bomberos.** En Paraguay, gran parte del trabajo contra incendios lo hacen cuerpos de bomberos voluntarios. Las
  noticias hablan de unos 140 cuarteles del Cuerpo de Bomberos Voluntarios del Paraguay (solo búsqueda); no se encontró
  una lista publicada de sus ubicaciones. Los 123 cuarteles de OSM (100 con nombre) están cerca de esa cifra, así que OSM
  quizás ya cubra la mayoría. Para compararlos haría falta la lista de los propios bomberos.
- **"Shelter" en OSM.** `amenity=shelter` marca techos pequeños, no refugios de emergencia. De los 284 en Paraguay, por
  `shelter_type` (calculado): 93 de un agua (lean-to), 70 de pícnic, 67 de sombra, 41 sin tipo, 5 pabellones, 4 de
  transporte público, 3 glorietas y 1 refugio contra la intemperie. No deberían dibujarse como refugios de emergencia. No
  se encontraron puntos de encuentro de emergencia en OSM para Paraguay.
- **Albergues por inundaciones.** Las crecidas de los ríos Paraguay y Paraná desplazan familias casi todos los años, y
  la Secretaría de Emergencia Nacional (SEN) habilita albergues junto con los municipios (solo búsqueda, noticias). No se
  encontró un conjunto de datos con sus ubicaciones. Muchos de estos albergues son temporales, así que una lista fija
  quizás no les sirva. Eso lo deciden los mantenedores.
- **Agua en el Chaco.** En la Región Occidental, los aljibes y los tajamares son las principales fuentes de agua
  (conocimiento general). No se encontró un conjunto de datos de ellos. Los 2.852 embalses de OSM probablemente incluyan
  muchos tajamares, pero no se verificó, y los aljibes casi nunca están mapeados. Es el vacío más claro para esta
  región.
- **Escuelas.** Los datos abiertos del Ministerio de Educación se publican con licencia CC BY 4.0 (solo búsqueda); no se
  verificó si incluyen coordenadas.
- **Relieve.** Copernicus GLO-30 es un modelo de superficie: bajo el bosque sigue las copas, no el suelo. No se encontró
  un modelo de elevación nacional abierto.
- **Cultivos.** MapBiomas Paraguay mapea clases de cobertura y uso del suelo (bosque, pastizal, agricultura, etc.), no
  tipos de cultivo. `tools/build_crops.py` toma huertos frutales, viñedos y frutos rojos del CDL, así que la
  correspondencia entre clases necesita una decisión (como el punto 4 de REGIONS.md). MapBiomas también tiene una serie
  aparte para el Gran Chaco, que cubre la Región Occidental junto con sus partes argentina y boliviana (solo búsqueda).
- **Cartografía INE 2012.** Es anterior al censo 2022. El INE menciona cartografía actualizada de departamentos y
  distritos entre los productos del censo 2022 y tiene un portal geoestadístico (solo búsqueda), pero no se encontraron
  archivos 2022 descargables.
- **Direcciones.** OSM tiene 44.614 objetos con `addr:housenumber` en Paraguay (calculado), lo que no alcanza para buscar
  direcciones en todo el país. Las manzanas del INE 2012 son polígonos; no se verificó si traen rangos de numeración. Por
  eso un primer mapa de Paraguay saldría como "mapa de calles, lugares y puntos de ayuda" sin búsqueda de direcciones,
  como se sugiere para Sri Lanka.

## Licencias y atribución

- **Licencia del INE** (abierta: `ine.gov.py/microdatos/license.php`, que cita la Ley 5282/2014 y el Decreto 4064). Una
  licencia gratuita, perpetua y no exclusiva para todo uso lícito, incluidas la copia, extracción, reproducción,
  distribución, comunicación pública, adaptación y transformación. A cambio:
  - citar la fuente pública que proveyó los datos;
  - indicar que el contenido se rige por esta licencia;
  - indicar la fecha de la última actualización, si se conoce;
  - no sugerir ni simular un uso oficial o patrocinado por el Estado paraguayo.

  Permite todo uso lícito y no pone condiciones de "compartir igual" ni de uso no comercial. Dónde muestra la app el
  crédito, el aviso de licencia y la fecha de los datos es el punto 5 de REGIONS.md.
- **CC BY-IGO** (COD-AB de OCHA, abierto con la API de HDX: fuente "Dirección General de Estadísticas, Encuestas y Censos
  (DGEEC), INE"; última modificación el 24 de septiembre de 2026). Dar crédito a OCHA y a su fuente.
- **MapBiomas Paraguay.** Su página de términos de uso (abierta) dice que los datos son públicos, abiertos y gratuitos
  bajo licencia Creative Commons CC BY, y pide citarlos como "MapBiomas – Colección [versión] de la Serie Anual de Mapas
  de Cobertura y Uso del Suelo de Paraguay", con la fecha de acceso y el enlace. Un resultado de búsqueda de la misma
  página mostraba "CC-CY-SA" (sic), y una copia en Source Coop indica CC BY-SA 4.0 (solo búsqueda). Hay que confirmar
  con MapBiomas si aplica "compartir igual" antes de una compilación.
- **ODbL, CC BY 4.0 y Copernicus WorldDEM-30:** como en REGIONS.md. Google Open Buildings puede tomarse bajo CC BY 4.0
  o bajo ODbL 1.0.

## Cómo se escriben las direcciones

Sin verificar en las páginas del propio Correo Paraguayo. Esta parte necesita la revisión de alguien del país.

- **Orden.** Nombre de la calle, luego el número, luego la ciudad: "José Martí 1953, Luque" (solo búsqueda, de una guía
  comercial de formatos de dirección). Como en Argentina, el número va después de la calle, al revés del orden que espera
  `engine/address_search.py`.
- **Esquinas** (conocimiento general). Muchas direcciones se dan por esquina, "Calle X c/ Calle Y" (c/ por *casi*) o
  "Calle X esq. Calle Y" (*esquina*), y muchas casas no tienen número ("s/n", *sin número*). Los nombres de calles
  suelen llevar títulos abreviados como "Avda.", "Mcal." (*Mariscal*) y "Gral." (*General*).
- **Código postal.** Seis dígitos: dos para el departamento, dos para el distrito y dos para el barrio (solo búsqueda).
  Todavía se ven los códigos anteriores de cuatro dígitos
  (conocimiento general). El Correo Paraguayo (DINACOPA) tiene una consulta en línea (solo búsqueda; sin abrir).
- **Qué hace hoy el código con eso.**
  - `engine/address_search.py` lee un código postal solo como cinco dígitos (`\d{5}`), así que no reconocería un código
    de seis, y `tools/build_addresses.py` guarda los primeros cinco caracteres (`left(postcode, 5)`), lo que cortaría el
    último dígito del barrio.
  - `normalize()` en `engine/address_search.py` y `norm()` en `tools/build_addresses.py` dejan solo `a-z`, `0-9` y
    espacios, así que toda letra fuera de `a-z` (vocales con tilde, la ñ, la ü) se vuelve un espacio: "Avda. Mcal.
    López 1234 c/ Ñeembucú" queda como `avda mcal l pez 1234 c eembuc` (probado el 17 de noviembre de 2026).
    REGIONS-DE.md encontró lo mismo para el alemán. Hay que quitar los diacríticos de los dos lados, y el PR #79 propone
    que cada índice declare su propia regla.
  - El buscador de lugares ya funciona bien: su índice FTS5 usa el tokenizador `unicode61`, que quita los diacríticos.
    Probado el 17 de noviembre de 2026, las búsquedas `neembucu`, `ypacarai` e `itapesyi` encontraron "Ñeembucú",
    "Ypacaraí" e "Itapesỹi" (el `name:gn` de un barrio en el extracto, con la letra guaraní ỹ). No se encontró en el
    extracto ningún nombre de lugar con g̃ (g con tilde combinada); una grafía inventada con esa letra también se
    encontró escribiendo `g`.

## Idioma

El castellano y el guaraní son los dos idiomas oficiales (conocimiento general). Muchos nombres de lugares son guaraníes
(Ñeembucú, Caaguazú, Itapúa, Ypacaraí), y la grafía guaraní usa letras que el castellano no tiene: ã, ẽ, ĩ, õ, ũ, ỹ y
g̃. No se verificó si las fuentes tipográficas del mapa base las dibujan; la g̃ no tiene un carácter precompuesto en
Unicode. OSM lleva `name:gn` en 147 objetos del extracto (calculado). Si se conserva es parte de la cuestión de idioma
de los issues #3 y #54.

## Todavía sin decidir

Cada punto necesita una decisión de los mantenedores antes de cambiar código. Los puntos 1, 2, 4 y 5 corresponden a
los puntos 1, 2, 4 y 3 de REGIONS.md, y el punto 8 a su punto 7.

1. **Códigos en la instalación.** Si `PY` es aceptable como `id` del manifiesto, en `map-set.json` y en
   `Lastbook-Map-PY.zip` y, si se quieren departamentos, si también se aceptan códigos con guion como `PY-ASU`.
2. **La regla del rectángulo.** Si la frontera es el borde de una primera compilación, y si más adelante se suma una
   franja para que las ciudades gemelas del otro lado queden enteras.
3. **Una región, dos o dieciocho.** Todo el país (lo propuesto), Región Oriental y Chaco, o cada departamento más un
   mapa aparte para el área metropolitana.
4. **La licencia de MapBiomas**: CC BY o CC BY-SA, y cómo sus clases de cobertura corresponden a la capa de cultivos.
5. **Búsqueda de direcciones.** Códigos postales de seis dígitos, número después de la calle, esquinas con "c/" y
   "esq.", y quitar tildes antes de comparar. Sin una fuente abierta de direcciones, un primer mapa sale sin búsqueda de
   direcciones.
6. **Puntos de ayuda sin fuente abierta**: establecimientos de salud, cuarteles de bomberos voluntarios, albergues por
   inundaciones y fuentes de agua del Chaco (aljibes y tajamares). A quién pedirlos, y si OSM alcanza para una primera
   compilación.
7. **Idioma**: qué nombre muestra el mapa cuando el castellano y el guaraní difieren, y si las fuentes tipográficas
   cubren las letras guaraníes.
8. **Las capas solo de California.** Como el punto 7 de REGIONS.md.

## Qué se verificó

- Abierto el 17 de noviembre de 2026: la página de Paraguay de Geofabrik (tamaños, fecha de los datos) y
  `paraguay.poly`; el registro COD-AB de Paraguay de OCHA con la API de HDX (licencia, fuente, fechas, archivos); la
  página "Cartografía Digital 2012" del INE y su página de licencia; los términos de uso de MapBiomas Paraguay; la guía
  de direcciones de Overture (versión 2026-10-21.0, 41 países); la página de Open Buildings de Google (Paraguay en la
  lista v3, licencia a elección); los metadatos ADM1 de Paraguay en geoBoundaries; `datos.gov.py` (solo la página de
  mantenimiento); el diff del PR #35 (su rectángulo `py-asu`).
- Descargado y calculado el 17 de noviembre de 2026: el GeoJSON del COD-AB de OCHA (rectángulos del país y de los
  departamentos; las superficies son el atributo `area_sqkm` del archivo) y el `paraguay-latest.osm.pbf` de Geofabrik
  (los conteos de OSM, y el mapa de prueba de Central y Asunción de la nota sobre hospitales).
- Probado el 17 de noviembre de 2026: `normalize()` de `engine/address_search.py` y un índice FTS5 `unicode61` como el
  que construye `tools/build_places.py`, con nombres en castellano y guaraní.
- Solo búsqueda: los códigos ISO 3166-2:PY, la extensión del Gran Asunción, los detalles de la colección de MapBiomas y
  la copia CC BY-SA, el formato del código postal, la dirección de ejemplo y la consulta de DINACOPA, los informes del
  Ministerio de Salud y la OPS, la cantidad de cuarteles de bomberos voluntarios, los albergues de la SEN, la licencia de
  los datos abiertos del MEC y la cartografía del censo 2022 del INE.
- Conocimiento general, para que lo confirme alguien del país: la superficie oficial de Paraguay y la de California,
  dónde vive la gente, las direcciones por esquina y "s/n", los códigos postales de cuatro dígitos, los idiomas
  oficiales, las fuentes de agua del Chaco y que no hay límites en disputa.
- Sin verificar: el sitio de ISO, la consulta del Correo Paraguayo, los sitios del MSPBS y de la SEN, el sitio del
  propio CBVP, el catálogo de `datos.gov.py` (en mantenimiento), el portal geoestadístico del INE, la numeración en las
  manzanas del INE 2012, la cobertura tipográfica de las letras guaraníes, cuánto de cada vecino entra en el rectángulo
  y la cobertura de Google Open Buildings en Paraguay.
