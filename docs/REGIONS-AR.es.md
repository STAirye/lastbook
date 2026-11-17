# Mapas detallados para Argentina: una propuesta

> Versión en español de [REGIONS-AR.md](REGIONS-AR.md). Si las dos difieren, vale la versión en inglés, que es la que se
> discute en el repositorio.

Esta es una propuesta para discutir, no una decisión. Responde, para Argentina, las preguntas que [MAPS.md](MAPS.md) pide
contestar antes de que la cobertura vaya más allá de Estados Unidos: qué fuente abierta reemplaza a cada lista federal,
con qué licencia, qué es un "estado" acá y cómo se escriben las direcciones. Sigue la forma de [REGIONS.md](REGIONS.md)
(Ontario, Columbia Británica y Guyana) y busca alimentar la misma discusión de diseño (issues #23, #25 y #31). La versión
legible por máquina es [regions-ar-proposed.json](regions-ar-proposed.json).

Nada de esto cambia la app, el motor ni una compilación. Ningún código lee el JSON, y nada de esto se distribuye: las
compilaciones empaquetan solo `web/` y `content/`.

**Cómo se verificó.** La investigación se hizo el 16 de noviembre de 2026. Cada fuente lleva una de tres marcas:

- **abierta**: se abrió y se leyó la página del conjunto de datos o de la licencia;
- **solo búsqueda**: el dato se vio en un resultado de búsqueda del sitio del propio publicador, pero no se abrió la
  página;
- **sin verificar**: no se pudo llegar a la página o leerla; la fila dice qué falta.

Las capas del IGN, Georef y el catálogo de datos.gob.ar se leyeron con sus interfaces públicas: el servicio WFS del IGN
para los límites, la cantidad de elementos y atributos de muestra; la API pública de Georef; y la API CKAN de
datos.gob.ar para licencias y listas de archivos. Lo que sigue marcado como "solo búsqueda" necesita una segunda mirada
antes de construir algo encima.

## Qué es una región

Argentina tiene 23 provincias y la Ciudad Autónoma de Buenos Aires (CABA). La propuesta es una región por provincia más
CABA, 24 en total, al mismo nivel que un estado de Estados Unidos.

### Códigos

La norma ISO 3166-2:AR le da a cada una una sola letra después de `AR-`: `AR-B` provincia de Buenos Aires, `AR-C` CABA,
`AR-X` Córdoba, `AR-S` Santa Fe, `AR-M` Mendoza, y así (solo búsqueda; no se cotejó con el sitio de ISO, como también
aclara REGIONS.md para sus códigos). El archivo de provincias de Natural Earth trae los mismos 24 códigos.

- Acá el código con guion hace todavía más falta que para Canadá: un `AR` solo ya significa **Arkansas** en
  `STATE_CODES` (`engine/address_search.py`), y las letras solas (`B`, `C`, `X`) no le dicen nada a quien lee.
- Esas mismas letras son el primer carácter del código postal argentino (ver "Cómo se escriben las direcciones"), así que
  el código y la dirección coinciden.

### Dos lugares que necesitan una decisión

- **CABA dentro de la provincia de Buenos Aires.** CABA es un enclave dentro de `AR-B`, y el rectángulo de `AR-B` ya la
  cubre. Hay dos opciones: distribuirlas por separado (simple, pero quien vive en el área metropolitana y elige un solo
  mapa se queda con la mitad), o que el mapa de `AR-B` incluya `AR-C`. La segunda refleja cómo vive y se mueve la gente
  del área, y es lo que sugiere esta propuesta.
- **Tierra del Fuego (`AR-V`).** Por ley argentina, la provincia es "Tierra del Fuego, Antártida e Islas del Atlántico
  Sur": incluye las Islas Malvinas (Falkland Islands), las islas del Atlántico Sur y un sector antártico, que administra
  el Reino Unido o quedan bajo el Tratado Antártico. Las capas oficiales del IGN siguen el límite legal. El rectángulo de
  abajo cubre solo la parte que administra Argentina (la parte argentina de la Isla Grande de Tierra del Fuego y la Isla
  de los Estados), y cómo muestra el mapa las zonas reclamadas queda para la decisión de los mantenedores sobre límites
  en disputa (punto 6 de REGIONS.md, "Still undecided").

### Rectángulos

Los rectángulos de abajo se calcularon con la propia **capa de polígonos "Provincia" del IGN** (Capas SIG, "Geodesia y
demarcación", "Límites"), leída con el servicio WFS público del IGN (`wms.ign.gob.ar/geoserver/ign/ows`,
`typeName=ign:provincia`, GeoJSON) el 16 de noviembre de 2026. La capa tiene 24 elementos, uno por provincia y CABA, con
el código de provincia del INDEC (`in1`) y `sag` = IGN. Cada rectángulo es la extensión de todos los vértices de la
provincia, menos/más 0,15° y redondeado hacia afuera a 0,01°, el mismo margen que usa `map_sets.state` para los estados
de Estados Unidos.

- **`AR-V` (Tierra del Fuego).** El polígono del IGN sigue el límite legal: 1.730 partes que llegan al Polo Sur
  (oeste -74, sur -90, este -25). El rectángulo de abajo conserva solo las 84 partes que quedan al oeste de 63,5° O y al
  norte de 56° S, que son la parte argentina de la Isla Grande y la Isla de los Estados con islotes cercanos. Las 1.646
  partes que quedan afuera son las Islas Malvinas, las islas del Atlántico Sur y el sector antártico, como se explicó
  arriba.
- **Control cruzado.** Los límites admin-1 1:10m de Natural Earth (dominio público) dan rectángulos a menos de 0,11° de
  estos en 22 de las 24 regiones, pero con 0,29° de diferencia en San Juan y 0,32° en Santiago del Estero, así que la
  capa del IGN es la que hay que usar.

En la tabla, los números van en el formato del archivo (punto decimal), igual que en la versión en inglés.

| Código | INDEC | Nombre | Rectángulo (oeste, sur, este, norte) | Rectángulo con margen de 0,15° |
|---|---|---|---|---|
| `AR-A` | 66 | Salta | -68.5688, -26.4168, -62.3414, -21.9988 | -68.72, -26.57, -62.19, -21.84 |
| `AR-B` | 06 | Buenos Aires | -63.3859, -41.0379, -56.6650, -33.2619 | -63.54, -41.19, -56.51, -33.11 |
| `AR-C` | 02 | Ciudad Autónoma de Buenos Aires | -58.5315, -34.7054, -58.3351, -34.5265 | -58.69, -34.86, -58.18, -34.37 |
| `AR-D` | 74 | San Luis | -67.3838, -36.0012, -64.8827, -31.8338 | -67.54, -36.16, -64.73, -31.68 |
| `AR-E` | 30 | Entre Ríos | -60.7762, -34.0398, -57.7974, -30.1590 | -60.93, -34.19, -57.64, -30.00 |
| `AR-F` | 46 | La Rioja | -69.6350, -31.9984, -65.4230, -27.7071 | -69.79, -32.15, -65.27, -27.55 |
| `AR-G` | 86 | Santiago del Estero | -65.1883, -30.4804, -61.7118, -25.6491 | -65.34, -30.64, -61.56, -25.49 |
| `AR-H` | 22 | Chaco | -63.4224, -28.0668, -58.3782, -24.0787 | -63.58, -28.22, -58.22, -23.92 |
| `AR-J` | 70 | San Juan | -70.5693, -32.6264, -66.6618, -28.3888 | -70.72, -32.78, -66.51, -28.23 |
| `AR-K` | 10 | Catamarca | -69.0954, -30.1196, -64.7810, -25.1683 | -69.25, -30.27, -64.63, -25.01 |
| `AR-L` | 42 | La Pampa | -68.2966, -39.3305, -63.3831, -35.0022 | -68.45, -39.49, -63.23, -34.85 |
| `AR-M` | 50 | Mendoza | -70.5837, -37.5753, -66.4780, -31.9994 | -70.74, -37.73, -66.32, -31.84 |
| `AR-N` | 54 | Misiones | -56.0586, -28.1642, -53.6374, -25.4943 | -56.21, -28.32, -53.48, -25.34 |
| `AR-P` | 34 | Formosa | -62.3423, -26.8798, -57.5594, -22.4609 | -62.50, -27.03, -57.40, -22.31 |
| `AR-Q` | 58 | Neuquén | -71.9679, -41.1006, -67.9981, -36.1099 | -72.12, -41.26, -67.84, -35.95 |
| `AR-R` | 62 | Río Negro | -71.9130, -42.0000, -62.7897, -37.5719 | -72.07, -42.15, -62.63, -37.42 |
| `AR-S` | 82 | Santa Fe | -62.8839, -34.3865, -58.8808, -27.9977 | -63.04, -34.54, -58.73, -27.84 |
| `AR-T` | 90 | Tucumán | -66.1769, -28.0141, -64.4818, -26.0583 | -66.33, -28.17, -64.33, -25.90 |
| `AR-U` | 26 | Chubut | -72.1885, -46.0000, -63.5828, -42.0000 | -72.34, -46.15, -63.43, -41.85 |
| `AR-V` | 94 | Tierra del Fuego (parte administrada) | -68.6094, -55.0635, -63.7959, -52.6583 | -68.76, -55.22, -63.64, -52.50 |
| `AR-W` | 18 | Corrientes | -59.7120, -30.7302, -55.6202, -27.2540 | -59.87, -30.89, -55.47, -27.10 |
| `AR-X` | 14 | Córdoba | -65.7715, -35.0153, -61.7716, -29.4987 | -65.93, -35.17, -61.62, -29.34 |
| `AR-Y` | 38 | Jujuy | -67.2130, -24.6134, -64.1508, -21.7809 | -67.37, -24.77, -64.00, -21.63 |
| `AR-Z` | 78 | Santa Cruz | -73.5666, -52.3977, -65.7107, -45.9999 | -73.72, -52.55, -65.56, -45.84 |

El rectángulo de `AR-B` ya contiene todo el de `AR-C`, que es en lo que se apoya la sugerencia sobre CABA.

## Fuentes, capa por capa

La página Capas SIG del IGN es la columna vertebral: lista, para todo el país, capas que equivalen a casi todas las listas
federales de Estados Unidos que usa hoy el mapa. Cada capa se ofrece en Shapefile, KML, GeoJSON y CSV, en WGS 84 /
POSGAR 07 (EPSG:4326), y el IGN dice que las capas se actualizan periódicamente (abierta).

| Capa (archivo) | Fuente de EE. UU. hoy | Propuesta para Argentina | Publicador | Licencia | Verificación |
|---|---|---|---|---|---|
| Relieve (`terrain.sqlite`) | USGS 3DEP | MDE-Ar v2.1, 30 m, unos 2 m de precisión vertical, alturas en SRVN16 | IGN | Términos del IGN (ver "Licencias") | abierta |
| Relieve, alternativa | | Copernicus DEM GLO-30, como se propuso para Guyana | ESA / Airbus | Copernicus WorldDEM-30 | como en REGIONS.md |
| Agua (`water.sqlite`) | NHD | Capas SIG "Hidrografía y oceanografía": cursos de agua (perennes e intermitentes), canales, embalses, espejos de agua | IGN | Términos del IGN | abierta (lista de capas) |
| Agua, alternativa | | Cursos y superficies de agua de OSM (extracto de Argentina de Geofabrik) | Colaboradores de OSM | ODbL | licencia de Geofabrik: solo búsqueda |
| Diques | NID | "Embalse" (98 polígonos de embalses con nombre) y "Muro de embalse" (125 paredes de diques) del IGN como reemplazo parcial; no se encontró un inventario abierto de diques | IGN | Términos del IGN | abierta; cantidades leídas |
| Cultivos (`crops.sqlite`) | USDA Cropland Data Layer | Mapa Nacional de Cultivos 2023/2024, GeoTIFF de 30 m, un mapa de invierno y uno de verano | INTA | CC BY 4.0 | abierta (registro en Zenodo) |
| Edificios (`buildings.sqlite`) | Huellas de Microsoft para EE. UU., alturas de OSM | Google Open Buildings v3; Microsoft Global ML Building Footprints para llenar huecos; alturas de OSM | Google; Microsoft; colaboradores de OSM | CC BY 4.0; ODbL (según la lista de Overture); ODbL | abierta (página de atribución de Overture); cobertura en Argentina: solo búsqueda |
| Lugares (`places.sqlite`) | GNIS, nomencladores del censo, OSM | Capas SIG "Localidad" (3.528 puntos) y "Paraje" (10.425), ambas de BAHRA con códigos de provincia y departamento y coordenadas, puntos de "Sublocalidad" (707) y polígonos de "Planta urbana" (3.350); lugares con nombre de OSM | IGN; colaboradores de OSM | Términos del IGN; ODbL | abierta; cantidades leídas |
| Caminos (mapa base) | OSM | OSM, como hoy; Capas SIG "Red vial nacional" (2.738 tramos, con número de ruta, fuente: Dirección Nacional de Vialidad), "Red vial provincial" (12.928, de las direcciones de vialidad provinciales), "Red vial terciaria" (136.168), "Senda rural" (20.965) y "Huella" (84.606 caminos de tierra) para llenar huecos rurales | Colaboradores de OSM; IGN | ODbL; Términos del IGN | abierta; cantidades leídas |
| Direcciones (`addresses/<code>.sqlite`) | Direcciones de Overture | **no se encontraron puntos de dirección**; cuadras con alturas como posible reemplazo (ver notas) | Georef; Ciudad de Buenos Aires | CC BY 4.0 (Georef) | ver notas |
| Puntos de interés (filas `poi`) | OSM | OSM, más las listas del IGN, de salud y de agua de abajo | | | abajo |

### Puntos de ayuda y de recursos

Son los puntos que la gente busca en una emergencia. Todas las capas del IGN de esta tabla son nacionales y salen de la
misma página Capas SIG (abierta). Las cantidades se leyeron del servicio WFS del IGN (`resultType=hits`) el 16 de
noviembre de 2026, y se leyó un elemento de muestra de cada una para ver sus campos: la mayoría trae un nombre (`fna`), un
tipo genérico (`gna`) y la fuente de la que salió el punto (`fdc`). Las listas provinciales y de salud suman detalle donde
existen.

| Tipo | Fuente propuesta | Publicador | Licencia | Verificación |
|---|---|---|---|---|
| Agua potable | Capas SIG "Planta potabilizadora de agua" (205 puntos y 186 polígonos, con nombre; entre las fuentes están el ENOHSa y empresas provinciales de agua), "Tanque de agua elevado" (137), "Planta de bombeo de agua" (39), "Acueducto" (290 líneas) | IGN | Términos del IGN | abierta; cantidades leídas |
| Canillas y bebederos | OSM `amenity=drinking_water` (614 en Argentina) y `man_made=water_tap` (171), contados con la API Overpass sobre datos de OSM del 17 de noviembre de 2026, 02:06 UTC | Colaboradores de OSM | ODbL | contados |
| Salud | Capas SIG "Edificio de salud" (8.311 puntos con nombre, por ejemplo "Centro Sanitario") | IGN | Términos del IGN | abierta; cantidad leída |
| Salud, con tipo y código REFES | Establecimientos de salud públicos de la provincia de Buenos Aires, con latitud, longitud y código REFES, en CSV, Shapefile y GeoJSON (edición 2025) | Ministerio de Salud de la Provincia de Buenos Aires | ver notas | solo búsqueda |
| Salud, registro nacional | REFES, el registro nacional de establecimientos de salud públicos y privados; el último archivo es un XLSX del 27 de diciembre de 2024 | Ministerio de Salud de la Nación | CC BY (`cc-by` en el catálogo de datos.gob.ar) | licencia y lista de archivos leídas con la API de datos.gob.ar; no se confirmó si tiene coordenadas |
| Farmacias | REFAR, el registro nacional de farmacias; el último archivo es un XLSX del 27 de diciembre de 2024 | Ministerio de Salud de la Nación | CC BY | leído con la API de datos.gob.ar; coordenadas sin confirmar |
| Bomberos | Capas SIG "Cuartel de bomberos" (1.081 puntos con nombre, por ejemplo "Bomberos Voluntarios de Fiambalá"); para la provincia de Buenos Aires, además, "Bomberos Voluntarios: Cuarteles" (Shapefile, GeoJSON, KML; actualizado en 2026), también hecho por el IGN | IGN | Términos del IGN; CC BY 4.0 en el portal provincial | abierta; cantidad leída; registro provincial: solo búsqueda |
| Policía y seguridad | Capas SIG "Edificio de seguridad" (4.117 puntos, la mayoría sin nombre) | IGN | Términos del IGN | abierta; cantidad leída |
| Escuelas y universidades | Capas SIG "Establecimiento educativo" (51.141 puntos con nombre, del Mapa Educativo Nacional), "Universidad" (1.132) y las capas del proyecto de preparación ante inundaciones "Escuelas Proyecto Anticipando la Crecida" (14) y "Lugares estratégicos Anticipando la Crecida" (176 lugares, como escuelas, con la amenaza para la que están previstos) | IGN | Términos del IGN | abierta; cantidades leídas |
| Combustible | Capas SIG "Estación de servicio" (5.383 puntos con nombre; fuente: Secretaría de Energía) | IGN | Términos del IGN | abierta; cantidad leída |
| Cruces | Capas SIG "Puente" (6.002 puntos y 1.049 líneas), "Vado" (35.290), "Alcantarilla", "Tunel" | IGN | Términos del IGN | abierta; cantidades leídas |
| Aeródromos | Capas SIG "Aeropuerto", "Aeródromo", "Helipuerto", "Pista" | IGN | Términos del IGN | abierta (lista de capas) |
| Energía | Capas SIG "Central eléctrica", "Línea de transmisión eléctrica", "Planta transformadora" | IGN | Términos del IGN | abierta (lista de capas) |

Notas:

- **Relieve.** El IGN dice que el MDE-Ar cubre todo el territorio continental argentino y que se distribuye en forma libre
  y gratuita. Se hizo con datos de SRTM y ALOS, así que, igual que Copernicus GLO-30, se parece más a un modelo de
  superficie en zonas de bosque y edificadas. El IGN también tiene un modelo de 5 m para algunas zonas (solo búsqueda).
- **Diques.** El organismo que regula la seguridad de presas, el ORSEP, publica un "Mapa de presas fiscalizadas,
  binacionales y sedes" para descargar (solo búsqueda), y en 2019 presentó un inventario "en elaboración" (solo
  búsqueda). Ninguno de los dos es un conjunto de datos abierto de puntos de diques. El ORSEP solo fiscaliza las presas
  concesionadas por el Estado nacional; las demás son provinciales.
- **Cultivos.** El mapa del INTA cubre las principales zonas agrícolas, no todo el país, y sus clases se explican en el
  informe que lo acompaña. `tools/build_crops.py` toma del CDL frutales, viñedos y frutos rojos; el mapa del INTA trata
  sobre cultivos extensivos (soja, maíz, trigo, etc.), así que hace falta decidir cómo se corresponden las listas de
  clases (como el punto 4 de REGIONS.md). El INTA también publicó la edición 2024/2025, como informe y como visor de Earth
  Engine (solo búsqueda); sus archivos de datos y su licencia no se verificaron, así que la propuesta usa la 2023/2024.
- **Edificios.** La versión 3 de Google cubre "América Latina y el Caribe", se generó en mayo de 2023 y tiene licencia
  CC BY 4.0 (solo búsqueda, en páginas de Google). No se midió cuánto de Argentina cubre. La wiki de OSM lista una
  importación de Google Open Buildings como disponible para editar en Argentina (solo búsqueda, wiki de OSM).
- **Lugares.** Georef, el servicio de normalización del Gobierno nacional, publica provincias, departamentos, municipios,
  localidades y calles armados con datos del IGN, BAHRA y el INDEC, y dice que todo lo que publica tiene licencia CC BY
  4.0, con la atribución "Servicio Georef – argentina.gob.ar/georef" (solo búsqueda).
- **Direcciones.** La página de atribución de Overture no lista ninguna fuente de direcciones para Argentina (abierta),
  así que el camino actual de `tools/build_addresses.py` no daría nada. Lo que sí existe:
  - **Cuadras de Georef.** Georef ubica direcciones interpolando a lo largo de las cuadras. La API en sí es en línea, así
    que, como el BC Address Geocoder de REGIONS.md, no sirve para una compilación sin conexión; pero datos.gob.ar también
    publica las cuadras como archivos completos (`infra.datos.gob.ar/georef/cuadras.csv`, `.geojson`, `.json` y `.zip`,
    del 5 de diciembre de 2023, CC BY 4.0; leído con la API de datos.gob.ar). El recurso `/cuadras` de Georef muestra la
    calle de cada cuadra y su rango de alturas de cada lado (`altura.inicio` y `altura.fin`, `izquierda` y `derecha`), y
    solo Córdoba tiene 248.672 cuadras (leído con la API). Muchas cuadras no tienen alturas (0 a 0): de las primeras 100
    que devolvió la API para cada provincia, tenían alturas 58 en la provincia de Buenos Aires, 46 en CABA, 31 en Jujuy,
    27 en Corrientes, y 3 o menos en Córdoba, Chaco, Catamarca, Chubut, Entre Ríos y Formosa. La muestra es chica y no es
    aleatoria; el límite de consultas de la API frenó el conteo en las otras 14 provincias, y el archivo completo no se
    descargó. Hay que medir la cobertura con el archivo completo antes de confiar en él.
  - La Ciudad de Buenos Aires publica su callejero en BA Data; una copia del registro dice que el archivo no trae
    licencia (solo búsqueda), mientras que el sitio de la Ciudad dice que su contenido tiene licencia CC BY 2.5 Argentina
    (solo búsqueda). Hay que resolverlo con la Ciudad antes de usarlo.
  - El archivo de domicilios del censo (ADRA) no es público.
  - No se pudo contar la cobertura de `addr:housenumber` de OSM en Argentina: la API Overpass se quedó sin tiempo con esa
    consulta.
  - Por eso, un índice de direcciones argentino se armaría con cuadras con rangos de alturas, por interpolación, y no con
    puntos de dirección como en Estados Unidos, y funcionaría bien solo donde las cuadras tienen alturas. Es un tipo de
    índice nuevo para `engine/address_search.py`, y una decisión de los mantenedores. Un primer mapa argentino podría
    salir como "mapa de calles, lugares y puntos de ayuda", sin búsqueda de direcciones. (El prototipo de Croacia del
    #25 es el caso inverso: direcciones, pero no las otras capas.)
- **Agua potable.** No se encontró una lista oficial nacional de puntos públicos de agua potable (canillas, bebederos,
  puntos de carga de camiones cisterna). Las capas del IGN de arriba marcan plantas potabilizadoras, tanques elevados,
  plantas de bombeo y acueductos, que dicen de dónde sale y dónde se guarda el agua de una red; con 205 plantas y 137
  tanques para todo el país, están claramente incompletas. OSM tiene 614 bebederos y 171 canillas, también poco para un
  país de 46 millones de personas. Se encontraron dos fuentes de investigación que no se proponen porque no se encontró
  su licencia: una base del CONICET con las tomas y los vertidos de agua de 243 ciudades argentinas, y el mapa del ITBA
  con mediciones de arsénico en agua de pozo y de red. Las dos serían valiosas, y vale la pena consultarles a sus autores.
- **Salud, provincia de Buenos Aires.** El archivo provincial vincula cada establecimiento con su código REFES nacional,
  así que se puede cotejar con el registro nacional. Su licencia no aparecía en el resultado de búsqueda y hay que leerla
  en el registro.

## Licencias y atribución

- **IGN** (abierta: `ign.gob.ar/descargas/tyc1.html`). Son términos propios del IGN, no una licencia Creative Commons.
  Permiten copiar, distribuir, modificar, adaptar, extraer y recombinar, siempre que el uso no desnaturalice el sentido
  de la información. A cambio:
  - los datos deben **compartirse en forma libre y gratuita**;
  - **el uso comercial solo se permite en obras derivadas** que usen los datos como insumo para un producto nuevo;
  - hay que citar la fuente como "FUENTE: Instituto Geográfico Nacional de la República Argentina";
  - hay que mantener intactos los metadatos de fecha de actualización y las condiciones de reutilización, y en los
    productos derivados indicar la fecha de los datos originales del IGN;
  - no se puede decir ni sugerir que el IGN participa, patrocina o avala la reutilización.

  Lastbook es gratis y sus paquetes se descargan gratis, así que esto encaja con cómo se distribuye Lastbook hoy. Dos
  puntos para los mantenedores: un paquete con capas del IGN tiene que seguir siendo gratis (no se podría vender tal
  cual, ni siquiera alguien más amparado en la licencia MIT del código de la app), y el mapa tendría que mostrar el
  crédito del IGN y las fechas de los datos. Si eso no se acepta, las alternativas son Copernicus GLO-30 para el relieve
  y OSM para el agua, los caminos y los lugares.
- **Natural Earth** (solo el control cruzado de los rectángulos). Dominio público; no pide crédito.
- **CC BY 4.0** (mapa de cultivos del INTA, Google Open Buildings, Georef, bomberos de la provincia de Buenos Aires).
  Hay que dar crédito al publicador, enlazar la licencia y decir si los datos se modificaron: por ejemplo "Mapa Nacional
  de Cultivos 2023/2024, INTA, CC BY 4.0", "Google Open Buildings v3, CC BY 4.0" y "Servicio Georef –
  argentina.gob.ar/georef".
- **ODbL** (OSM a través de Geofabrik, huellas de Microsoft como las lista Overture). Igual que para el mapa de Estados
  Unidos: "© OpenStreetMap contributors", los datos están bajo la ODbL, y una base armada con ellos se ofrece bajo la
  ODbL.
- **CC BY-IGO** (límites de Argentina de OCHA, del IGN y ACNUR, última modificación el 4 de mayo de 2020; abierta), si
  se usan como control cruzado de los rectángulos. Hay que dar crédito a OCHA y a su fuente.
- **Conjuntos de datos sin licencia declarada.** Varios conjuntos de datos.gob.ar dicen "No se especificó la licencia",
  y el kit nacional de datos abiertos sugiere CC BY 4.0 o licencias Open Data Commons sin que eso sea automático (solo
  búsqueda). Acá, un conjunto sin licencia declarada se considera todavía no utilizable.

## Cómo se escriben las direcciones

- **Orden.** Nombre de la calle, después la altura, después la localidad y la provincia: "Av. Corrientes 1234, C1043AAZ,
  Ciudad Autónoma de Buenos Aires". El número va *después* de la calle, al revés del orden de Estados Unidos que espera el
  analizador. Las palabras comunes son *Av.* / *Avenida*, *Calle*, *Pasaje*, *Bv.* / *Bulevar*, *Diagonal* y *Ruta*.
  La gente también da una dirección como "Calle X al 2950" (la cuadra del 2900), por esquinas ("Calle X y Calle Y") o
  "entre" calles ("Calle X entre Calle Y y Calle Z"); Georef acepta todas estas formas (solo búsqueda).
- **Código postal (CPA).** Ocho caracteres: una letra para la provincia (la misma letra que ISO 3166-2:AR), cuatro
  dígitos para la localidad (el código postal viejo) y tres letras para el lado de la manzana, como en `C1043AAZ` (solo
  búsqueda; no se abrió la consulta del propio Correo Argentino). La forma vieja de cuatro dígitos (`1043`) se sigue
  usando todos los días, así que la búsqueda debería aceptar las dos.
- **Qué hace hoy el código con eso.** `tools/build_addresses.py` guarda los primeros cinco caracteres de un código postal,
  que en un CPA dan `C1043`: letra de provincia más localidad, una clave útil. `engine/address_search.py` lee un código
  postal solo como cinco dígitos (`\d{5}`), así que no reconocería ni `C1043AAZ` ni `1043`, y espera el número antes de
  la calle.

## Todavía sin decidir

Cada punto necesita una decisión de los mantenedores antes de cambiar código. Los tres primeros se comparten con
REGIONS.md.

1. **Códigos en la configuración inicial.** Si se aceptan códigos con guion como `AR-B` como `id` del manifiesto, en
   `map-set.json` y en `Lastbook-Map-<id>.zip`, y cómo agrupa la configuración inicial 24 regiones argentinas.
2. **La regla del rectángulo**, como en REGIONS.md, incluida la regla que se usa acá para recortar `AR-V` a la zona que
   administra Argentina.
3. **Límites en disputa**: qué muestra el mapa de `AR-V` más allá de la zona que administra Argentina.
4. **CABA y la provincia de Buenos Aires**: un mapa con las dos, o dos mapas.
5. **Los términos del IGN**: si "libre y gratuito, uso comercial solo en obras derivadas" se acepta para los paquetes, y
   dónde se muestran el crédito del IGN y las fechas de los datos.
6. **Búsqueda de direcciones por interpolación** a lo largo de las cuadras, ya que Argentina no tiene puntos de dirección
   abiertos.
7. **Nuevos tipos de puntos de ayuda**: plantas potabilizadoras y tanques, bomberos, escuelas, combustible y vados del
   IGN, y cómo se corresponden con los tipos que ya dibuja `web/map.js`.

## Qué se verificó y qué no

- Abiertas el 16 de noviembre de 2026: la página Capas SIG del IGN (lista de capas, formatos, la capa "Provincia" y las
  capas de agua, salud, emergencias, educación, energía y transporte nombradas arriba), los términos y condiciones del
  IGN, la página del MDE-Ar del IGN, el registro en Zenodo del mapa de cultivos 2023/2024 del INTA, la página de
  atribución de Overture y el registro de COD-AB de Argentina de OCHA en HDX.
- Leídas con API públicas el 16 de noviembre de 2026: el servicio WFS del IGN (polígonos de
  provincias, cantidades de elementos y un elemento de muestra por capa), el recurso `/cuadras` de Georef, la API CKAN de
  datos.gob.ar (licencias y listas de archivos de REFES, REFAR y Georef) y la API Overpass de OSM (conteo de agua
  potable).
- Calculados el 16 de noviembre de 2026: los 24 rectángulos, con la capa "Provincia" del IGN a través de su servicio WFS,
  con control cruzado contra Natural Earth.
- Vistos solo en resultados de búsqueda de los sitios de los propios publicadores: la licencia de Georef, la cobertura de
  Google Open Buildings, los establecimientos de salud y los bomberos de la provincia de Buenos Aires, el mapa del ORSEP,
  el callejero de la Ciudad de Buenos Aires, la edición 2024/2025 del INTA, la licencia de Geofabrik, los códigos ISO
  3166-2:AR y el formato del CPA.
- Sin verificar: si REFES y REFAR tienen coordenadas (sus archivos están en `datos.salud.gob.ar`, que rechaza la lectura
  automática, y no se abrieron), la licencia del archivo de salud de la provincia de Buenos Aires, los PDF de licencia
  por producto del IGN, los archivos de datos 2024/2025 del INTA, las páginas del propio Correo Argentino sobre el CPA,
  la cobertura de alturas de las cuadras de Georef más allá de la muestra chica de arriba, y la cobertura de direcciones
  de OSM (la consulta de Overpass se quedó sin tiempo).
