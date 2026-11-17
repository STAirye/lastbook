# Detailed maps for Argentina: a proposal

This is a proposal for discussion, not a decision. It answers, for Argentina, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a "state"
is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) (Ontario, British Columbia and
Guyana) and is meant to feed the same design discussion (issues #23, #25 and #31). The machine-readable version is
[regions-ar-proposed.json](regions-ar-proposed.json), and a Spanish translation is [REGIONS-AR.es.md](REGIONS-AR.es.md).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 16 November 2026. Each source carries one of three marks:

- **opened**: the dataset or licence page itself was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

IGN's layers, Georef and datos.gob.ar's catalogue were read through their public interfaces: the IGN WFS service for
boundaries, feature counts and sample attributes, Georef's public API, and datos.gob.ar's CKAN API for licences and file
lists. Facts still marked "search only" need a second look before anything is built on them.

## What a region is

Argentina has 23 provinces and the Autonomous City of Buenos Aires (CABA). The proposal is one region per province plus
CABA, 24 in all, the same level as a US state.

### Codes

ISO 3166-2:AR gives each one a single letter after `AR-`: `AR-B` Buenos Aires province, `AR-C` CABA, `AR-X` Córdoba,
`AR-S` Santa Fe, `AR-M` Mendoza, and so on (search only; not checked against the ISO site, as REGIONS.md also notes for
its codes). Natural Earth's province file carries the same 24 codes.

- A hyphenated code is needed here even more than for Canada: a bare `AR` already means **Arkansas** in `STATE_CODES`
  (`engine/address_search.py`), and the single letters alone (`B`, `C`, `X`) mean nothing to a reader.
- The same letters are the first character of the Argentine postal code (see "How addresses are written"), so the code
  and the address agree.

### Two places that need a decision

- **CABA inside Buenos Aires province.** CABA is an enclave inside `AR-B`, and the `AR-B` box already covers it. Two
  options: ship them separately (simple, but someone in the metropolitan area who picks one map loses half of it), or let
  the `AR-B` map include `AR-C`. The second matches how people in the area live and move, and is what this proposal
  suggests.
- **Tierra del Fuego (`AR-V`).** By Argentine law the province is "Tierra del Fuego, Antártida e Islas del Atlántico
  Sur": it includes the Malvinas/Falkland Islands, the South Atlantic islands and an Antarctic sector, which are
  administered by the United Kingdom or fall under the Antarctic Treaty. IGN's official layers follow the legal
  boundary. The box below covers only the part Argentina administers (the Argentine part of Isla Grande de Tierra del
  Fuego and Isla de los Estados), and how the map shows the claimed areas is left to the maintainers' decision on
  disputed boundaries (item 6 in REGIONS.md, "Still undecided").

### Boxes

The boxes below were computed from IGN's own **"Provincia" polygon layer** (Capas SIG, "Geodesia y demarcación",
"Límites"), read through IGN's public WFS service
(`wms.ign.gob.ar/geoserver/ign/ows`, `typeName=ign:provincia`, GeoJSON) on 16 November 2026. The layer has 24 features,
one per province and CABA, with the INDEC province code (`in1`) and `sag` = IGN. Each box is the extent of every vertex of
the province, then minus/plus 0.15° and rounded outward to 0.01°, the same margin `map_sets.state` uses for US states.

- **`AR-V` (Tierra del Fuego).** IGN's polygon follows the legal boundary: 1,730 parts reaching to the South Pole
  (west -74, south -90, east -25). The box below keeps only the 84 parts that lie west of 63.5° W and north of 56° S,
  which are the Argentine part of Isla Grande and Isla de los Estados with nearby islets. The 1,646 parts left out are the
  Malvinas/Falkland Islands, the South Atlantic islands and the Antarctic sector, as discussed above.
- **Cross-check.** Natural Earth's 1:10m admin-1 boundaries (public domain) give boxes within 0.11° of these for
  22 of the 24, but 0.29° off for San Juan and 0.32° for Santiago del Estero, so IGN's layer is the one to use.

| Code | INDEC | Name | Box (west, south, east, north) | Box with 0.15° margin |
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
| `AR-V` | 94 | Tierra del Fuego (administered part) | -68.6094, -55.0635, -63.7959, -52.6583 | -68.76, -55.22, -63.64, -52.50 |
| `AR-W` | 18 | Corrientes | -59.7120, -30.7302, -55.6202, -27.2540 | -59.87, -30.89, -55.47, -27.10 |
| `AR-X` | 14 | Córdoba | -65.7715, -35.0153, -61.7716, -29.4987 | -65.93, -35.17, -61.62, -29.34 |
| `AR-Y` | 38 | Jujuy | -67.2130, -24.6134, -64.1508, -21.7809 | -67.37, -24.77, -64.00, -21.63 |
| `AR-Z` | 78 | Santa Cruz | -73.5666, -52.3977, -65.7107, -45.9999 | -73.72, -52.55, -65.56, -45.84 |

The `AR-B` box already contains the whole `AR-C` box, which is what the CABA suggestion above relies on.

## Sources, layer by layer

IGN's Capas SIG page is the backbone: it lists, for the whole country, layers that match almost every US federal list the
map uses today. Each layer is offered as Shapefile, KML, GeoJSON and CSV, in WGS 84 / POSGAR 07 (EPSG:4326), and IGN says
the layers are updated periodically (opened).

| Layer (file) | US source today | Proposed for Argentina | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | MDE-Ar v2.1, 30 m, about 2 m vertical accuracy, heights in SRVN16 | IGN | IGN terms (see "Licence notes") | opened |
| Terrain, fallback | | Copernicus DEM GLO-30, as proposed for Guyana | ESA / Airbus | Copernicus WorldDEM-30 | as in REGIONS.md |
| Water (`water.sqlite`) | NHD | Capas SIG "Hidrografía y oceanografía": watercourses (perennial and intermittent), canals, reservoirs, water surfaces | IGN | IGN terms | opened (layer list) |
| Water, fallback | | OSM waterways and water areas (Geofabrik's Argentina extract) | OSM contributors | ODbL | Geofabrik licence search only |
| Dams | NID | IGN "Embalse" (98 named reservoir polygons) and "Muro de embalse" (125 dam walls) as a partial stand-in; no open dam inventory found | IGN | IGN terms | opened; counts read |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | Mapa Nacional de Cultivos 2023/2024, 30 m GeoTIFF, one winter and one summer map | INTA | CC BY 4.0 | opened (Zenodo record) |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Google Open Buildings v3; Microsoft Global ML Building Footprints to fill gaps; OSM heights | Google; Microsoft; OSM contributors | CC BY 4.0; ODbL (as Overture lists it); ODbL | opened (Overture attribution page); Argentina coverage search only |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | Capas SIG "Localidad" (3,528 points) and "Paraje" (10,425), both from BAHRA with province and department codes and coordinates, "Sublocalidad" (707) points and "Planta urbana" (3,350) polygons; OSM named places | IGN; OSM contributors | IGN terms; ODbL | opened; counts read |
| Roads (base map) | OSM | OSM, as today; Capas SIG "Red vial nacional" (2,738 segments, route numbers, source: Dirección Nacional de Vialidad), "Red vial provincial" (12,928, from the provincial road agencies), "Red vial terciaria" (136,168), "Senda rural" (20,965) and "Huella" (84,606 dirt tracks) to fill rural gaps | OSM contributors; IGN | ODbL; IGN terms | opened; counts read |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **no address points found**; street blocks with door numbers as a possible substitute (see notes) | Georef; Buenos Aires City | CC BY 4.0 (Georef) | see notes |
| Points of interest (`poi` rows) | OSM | OSM, plus the IGN, health and water lists below | | | below |

### Help and resource points

These are the points people look for in an emergency. Every IGN layer here is national and comes from the same Capas
SIG page (opened). The feature counts were read from IGN's WFS service (`resultType=hits`) on 16 November 2026, and one
sample feature of each was read to see its fields: most carry a name (`fna`), a generic type (`gna`) and the source the
point came from (`fdc`). The provincial and health lists add detail where they exist.

| Kind | Proposed source | Publisher | Licence | Checked |
|---|---|---|---|---|
| Drinking water | Capas SIG "Planta potabilizadora de agua" (205 points, 186 polygons, named, sources include ENOHSa and provincial water companies), "Tanque de agua elevado" (137), "Planta de bombeo de agua" (39), "Acueducto" (290 lines) | IGN | IGN terms | opened; counts read |
| Drinking water taps | OSM `amenity=drinking_water` (614 in Argentina) and `man_made=water_tap` (171), counted through the Overpass API against OSM data of 17 November 2026 02:06 UTC | OSM contributors | ODbL | counted |
| Health | Capas SIG "Edificio de salud" (8,311 named points, e.g. "Centro Sanitario") | IGN | IGN terms | opened; count read |
| Health, with type and REFES code | Buenos Aires province's public health establishments, with latitude, longitude and the REFES code, as CSV, Shapefile and GeoJSON (2025 edition) | Ministerio de Salud de la Provincia de Buenos Aires | see notes | search only |
| Health, national register | REFES, the national register of public and private health establishments; latest file is an XLSX dated 27 December 2024 | Ministerio de Salud de la Nación | CC BY (`cc-by` in datos.gob.ar's catalogue) | licence and file list read through datos.gob.ar's API; whether it has coordinates not confirmed |
| Pharmacies | REFAR, the national pharmacy register; latest file is an XLSX dated 27 December 2024 | Ministerio de Salud de la Nación | CC BY | read through datos.gob.ar's API; coordinates not confirmed |
| Fire stations | Capas SIG "Cuartel de bomberos" (1,081 named points, e.g. "Bomberos Voluntarios de Fiambalá"); for Buenos Aires province also "Bomberos Voluntarios: Cuarteles" (Shapefile, GeoJSON, KML; updated 2026), also produced by IGN | IGN | IGN terms; CC BY 4.0 on the provincial portal | opened; count read; provincial record search only |
| Police and security | Capas SIG "Edificio de seguridad" (4,117 points, mostly unnamed) | IGN | IGN terms | opened; count read |
| Schools and universities | Capas SIG "Establecimiento educativo" (51,141 named points, from the Mapa Educativo Nacional), "Universidad" (1,132), and the flood-preparedness project layers "Escuelas Proyecto Anticipando la Crecida" (14) and "Lugares estratégicos Anticipando la Crecida" (176 places such as schools, with the hazard they are planned for) | IGN | IGN terms | opened; counts read |
| Fuel | Capas SIG "Estación de servicio" (5,383 named points; source: Secretaría de Energía) | IGN | IGN terms | opened; count read |
| Crossings | Capas SIG "Puente" (6,002 points, 1,049 lines), "Vado" (35,290 fords), "Alcantarilla", "Tunel" | IGN | IGN terms | opened; counts read |
| Airfields | Capas SIG "Aeropuerto", "Aeródromo", "Helipuerto", "Pista" | IGN | IGN terms | opened (layer list) |
| Power | Capas SIG "Central eléctrica", "Línea de transmisión eléctrica", "Planta transformadora" | IGN | IGN terms | opened (layer list) |

Notes:

- **Terrain.** IGN says MDE-Ar covers all of continental Argentina and is distributed free of charge. It was built from
  SRTM and ALOS data, so like Copernicus GLO-30 it is closer to a surface model in forest and built-up areas. IGN also
  has a 5 m model for some areas (search only).
- **Dams.** The dam regulator, ORSEP, publishes a "Mapa de presas fiscalizadas, binacionales y sedes" as a downloadable
  map (search only), and presented an inventory "in preparation" in 2019 (search only). Neither is an open dataset of
  dam points. ORSEP only oversees dams concessioned by the national state; the others are provincial.
- **Crops.** The INTA map covers the main agricultural areas, not the whole country, and its classes are explained in the
  report that comes with it. `tools/build_crops.py` keeps orchards, vineyards and berries from the CDL; the INTA map is
  about extensive crops (soy, maize, wheat and so on), so the mapping between class lists needs a decision (as item 4 in
  REGIONS.md). INTA has published the 2024/2025 edition too, as a report and an Earth Engine viewer (search only); its
  data files and licence were not checked, so 2023/2024 is the one proposed.
- **Buildings.** Google's v3 dataset covers "Latin America and the Caribbean", inferred in May 2023, under CC BY 4.0
  (search only, Google's own pages). How much of Argentina it covers was not measured. An OSM import of Google Open
  Buildings is listed as available to edit for Argentina on the OSM wiki (search only).
- **Places.** Georef, the national government's normalisation service, publishes provinces, departments, municipalities,
  localities and streets built from IGN, BAHRA and INDEC data, and says everything it publishes is under CC BY 4.0, with
  the attribution "Servicio Georef – argentina.gob.ar/georef" (search only).
- **Addresses.** Overture's attribution page lists no address source for Argentina (opened), so the current
  `tools/build_addresses.py` path would give nothing. What exists instead:
  - **Georef street blocks ("cuadras").** Georef geocodes addresses by interpolating along street blocks. The API
    itself is online, so like the BC Address Geocoder in REGIONS.md it does not fit an offline build, but datos.gob.ar
    also publishes the blocks as bulk files (`infra.datos.gob.ar/georef/cuadras.csv`, `.geojson`, `.json` and `.zip`,
    dated 5 December 2023, CC BY 4.0; read through datos.gob.ar's API). Georef's `/cuadras` resource shows each block's
    street and its door-number range on each side (`altura.inicio` and `altura.fin`, `izquierda` and `derecha`), and
    Córdoba alone has 248,672 blocks (read through the API). Many blocks have no numbers (0 to 0): in the first 100
    blocks returned for each province, 58 had numbers in Buenos Aires province, 46 in CABA, 31 in Jujuy, 27 in
    Corrientes, and 3 or fewer in Córdoba, Chaco, Catamarca, Chubut, Entre Ríos and Formosa. That sample is small and
    not random; the API's rate limit stopped the count for the other 14 provinces, and the bulk file itself was not
    downloaded. Coverage has to be measured from the bulk file before relying on it.
  - Buenos Aires City publishes its street file ("callejero") on BA Data; a mirror of the record says no licence is
    given on the file itself (search only), while the City's website says its content is under CC BY 2.5 Argentina
    (search only). That needs to be settled with the City before use.
  - The national census address file (ADRA) is not public.
  - OSM's `addr:housenumber` coverage in Argentina could not be counted: the Overpass API timed out on that query.
  - So an Argentine address index would be built from street blocks with door-number ranges, by interpolation, not from
    address points as in the US, and would work well only where the blocks carry numbers. That is a new kind of index
    for `engine/address_search.py`, and a decision for the maintainers. A first Argentine map could ship as "street
    map, places and help points" without address search. (The Croatia prototype in #25 is the reverse case: addresses,
    but not the other layers.)
- **Drinking water.** No official national list of public drinking water points (taps, fountains, tanker stops) was found.
  The IGN layers above mark water treatment plants, elevated tanks, pumping stations and aqueducts, which say where a
  network's water comes from and is stored; with 205 plants and 137 tanks for the whole country they are clearly
  incomplete. OSM has 614 drinking-water points and 171 taps, also sparse for a country of 46 million people. Two
  research sources were found and not proposed, because their licences were not found: a CONICET database of the water
  intakes and outflows of 243 Argentine cities, and ITBA's map of arsenic measurements in well and tap water. Both would
  be valuable, and worth asking their authors about.
- **Health, Buenos Aires province.** The provincial file links each establishment to its national REFES code, so it can
  be checked against the national register. Its licence was not seen in the search result and must be read on the
  record.

## Licence notes and attribution

- **IGN** (opened: `ign.gob.ar/descargas/tyc1.html`). IGN's own terms, not a Creative Commons licence. They allow copying,
  distribution, modification, adaptation, extraction and recombination as long as the use does not distort the meaning
  of the information. In return:
  - the data must be **shared freely and at no cost**;
  - **commercial use is allowed only for derivative works** that use the data as input to make a new product;
  - credit the source as "FUENTE: Instituto Geográfico Nacional de la República Argentina";
  - keep the update-date metadata and reuse conditions intact, and for derived products state the date of the original
    IGN data;
  - do not say or suggest that IGN takes part in, sponsors or endorses the reuse.

  Lastbook is free and its packs are free downloads, so this fits how Lastbook is distributed today. Two points for the
  maintainers: a pack holding IGN layers must stay free (so it could not be sold as is, even by someone else under the
  MIT licence of the app's code), and the map would need to show the IGN credit and data dates. If that is not
  acceptable, the fallbacks are Copernicus GLO-30 for terrain and OSM for water, roads and places.
- **Natural Earth** (the cross-check for the boxes only). Public domain; no credit required.
- **CC BY 4.0** (INTA crop map, Google Open Buildings, Georef, Buenos Aires province's fire stations). Credit the
  publisher, link the licence and say if the data was changed: for example "Mapa Nacional de Cultivos 2023/2024, INTA,
  CC BY 4.0", "Google Open Buildings v3, CC BY 4.0" and "Servicio Georef – argentina.gob.ar/georef".
- **ODbL** (OSM through Geofabrik, Microsoft footprints as Overture lists them). The same as for the US map:
  "© OpenStreetMap contributors", the data is under the ODbL, and a database built from it is offered under the ODbL.
- **CC BY-IGO** (OCHA's Argentina boundaries, from IGN and UNHCR, last modified 4 May 2020; opened), if used as a
  cross-check for the boxes. Credit OCHA and its source.
- **Datasets without a stated licence.** Several datasets on datos.gob.ar say "No se especificó la licencia" (no licence
  given), and the national open data kit suggests CC BY 4.0 or Open Data Commons licences without making them automatic
  (search only). A dataset with no stated licence is treated here as not yet usable.

## How addresses are written

- **Order.** Street name, then the door number, then the locality and province: "Av. Corrientes 1234, C1043AAZ, Ciudad
  Autónoma de Buenos Aires". The number comes *after* the street, the opposite of the US order the parser expects.
  Common street words are *Av.* / *Avenida*, *Calle*, *Pasaje*, *Bv.* / *Bulevar*, *Diagonal* and *Ruta*. People also
  give an address as "Calle X al 2950" (the 2900 block), or by corners ("Calle X y Calle Y") and "between" streets
  ("Calle X entre Calle Y y Calle Z"); Georef accepts all of these forms (search only).
- **Postal code (CPA).** Eight characters: one letter for the province (the same letter as ISO 3166-2:AR), four digits
  for the locality (the old postal code), and three letters for the side of the block, as in `C1043AAZ` (search only;
  Correo Argentino's own look-up was not opened). The old four-digit form (`1043`) is still in everyday use, so search
  should accept both.
- **What the current code does with that.** `tools/build_addresses.py` keeps the first five characters of a postcode,
  which for a CPA gives `C1043`: province letter plus locality, a useful key. `engine/address_search.py` reads a postcode
  only as five digits (`\d{5}`), so it would miss both `C1043AAZ` and `1043`, and it expects the number before the
  street.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first three are shared with REGIONS.md.

1. **Codes in setup.** Whether hyphenated codes such as `AR-B` are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup groups 24 Argentine regions.
2. **The box rule**, as in REGIONS.md, including the rule used here to cut `AR-V` down to the area Argentina
   administers.
3. **Disputed boundaries**: what the `AR-V` map shows beyond the area Argentina administers.
4. **CABA and Buenos Aires province**: one map that holds both, or two.
5. **IGN's terms**: whether "free and at no cost, commercial use only in derivative works" is acceptable for packs, and
   where the IGN credit and data dates are shown.
6. **Address search by interpolation** along street blocks, since Argentina has no open address points.
7. **New help-point kinds**: drinking water plants and tanks, fire stations, schools, fuel and fords from IGN, and how
   they map to the kinds `web/map.js` already draws.

## What was checked, and what was not

- Opened on 16 November 2026: IGN's Capas SIG page (layer list, formats, the "Provincia" layer, and the water, health,
  emergency, education, energy and transport layers named above), IGN's terms and conditions, IGN's MDE-Ar page, the INTA
  crop map 2023/2024 record on Zenodo, Overture's attribution page, and OCHA's Argentina COD-AB record on HDX.
- Read through public APIs on 16 November 2026: IGN's WFS service (province polygons, feature counts and one
  sample feature per layer), Georef's `/cuadras` resource, datos.gob.ar's CKAN API (licences and file lists for REFES,
  REFAR and Georef), and OSM's Overpass API (drinking-water counts).
- Computed on 16 November 2026: the 24 boxes, from IGN's "Provincia" layer through its WFS service, cross-checked
  against Natural Earth.
- Seen only in search results from the publishers' own sites: the Georef licence, Google Open Buildings coverage, Buenos
  Aires province's health establishments and fire stations, the ORSEP map, Buenos Aires City's street file, INTA's
  2024/2025 edition, Geofabrik's licence, the ISO 3166-2:AR codes and the CPA format.
- Not checked: whether REFES and REFAR carry coordinates (their files are on `datos.salud.gob.ar`, which refuses
  automated reading, and were not opened), the licence of Buenos Aires province's health file, IGN's per-product licence
  PDFs, INTA's 2024/2025 data files, Correo Argentino's own CPA pages, door-number coverage of Georef's blocks beyond the
  small sample above, and OSM address coverage (the Overpass query timed out).
