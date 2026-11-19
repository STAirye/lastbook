# Detailed maps for Spain: a proposal

This is a proposal for discussion, not a decision. It answers, for Spain, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md),
[REGIONS-AR.md](REGIONS-AR.md) and [REGIONS-DE.md](REGIONS-DE.md) and is meant to feed the same design discussion
(issues #23, #25 and #31). The machine-readable version is [regions-es-proposed.json](regions-es-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026, with AI research agents reading the publishers' own
pages and a person reviewing the result. The boxes and the address figures were computed from the data itself, as
described in each section. Each source carries one of three marks:

- **opened**: the dataset or licence page itself was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

The CNIG download centre and several ministry catalogues are JavaScript applications, so some rows are "search only".
They need a second look before anything is built on them.

## Why Spain is a useful case

Spain is close to the US in the way its data is organised: one national mapping agency (IGN, with its distribution arm
CNIG) publishes nationwide elevation, hydrography, names and boundaries under one licence, CC BY 4.0, and Overture already
carries a nationwide address set with postcodes. Two things are different and worth deciding once, because other
European countries will raise them too:

- **Postcode areas are not open.** Correos owns them, and an agreement published in the BOE forbids CNIG from offering
  the postcode layer for download (see "How addresses are written").
- **Several official languages.** Catalan, Galician, Basque and Valencian names are official in their communities, and
  many places have two official names ("Donostia / San Sebastián", "Arrasate/Mondragón").

## What a region is

Spain has 17 autonomous communities and two autonomous cities (Ceuta and Melilla, on the North African coast). The
proposal is one region per community or city, 19 in all. A community is the level closest to a US state in size and
in what it runs (health, civil protection, most open data portals): the largest, Castilla y León (about 94,000 km²), is about the size of
Indiana; the smallest, La Rioja (about 5,000 km²), is a little smaller than Delaware (areas not reopened for this change).

The 50 provinces are the other candidate. They are what postcodes and Overture's data follow (see below), and they
would give smaller downloads, but they do not match how Spanish emergency services or regional data are organised.
The JSON keeps the province list of each community so that either cut can be made later.

### Codes

ISO 3166-2:ES gives each community two letters after `ES-`: `ES-AN` Andalusia, `ES-CT` Catalonia, `ES-MD` Madrid, and so
on (not checked against the ISO site, as the other proposals also note for their codes).

- A hyphenated code is needed, and here it matters more than in Germany: six of the 19 two-letter parts are also US
  codes in `STATE_CODES` (`engine/address_search.py`). `AR` (Aragon / Arkansas), `CT` (Catalonia / Connecticut),
  `GA` (Galicia / Georgia), `MD` (Madrid / Maryland), `NC` (Navarre / North Carolina) and `RI` (La Rioja / Rhode Island)
  would collide in `Lastbook-Map-<id>.zip` and in `derived/geo/addresses/<id>.sqlite` without the `ES-` prefix.
- A bare `ES` is not a US code, so it would be free for a whole-country map, should one ever be wanted.

### Boxes

The boxes were computed from IGN's INSPIRE service "Unidades administrativas de España"
(`https://www.ign.es/wfs-inspire/unidades-administrativas`, access constraints "CC BY 4.0 ign.es", fees "No se aplican
condiciones", opened). Each community was fetched as one `au:AdministrativeUnit` of the second order, with the ids
`AU_ADMINISTRATIVEUNIT_34<cc>0000000`, where `<cc>` is the INE community code. Every vertex of every polygon was read; the
service gives ETRS89 longitude and latitude (EPSG:4258), which differ from WGS 84 by far less than the 0.01° rounding.
Each box was then widened by 0.15° and rounded outward to 0.01°, the same margin `map_sets.state` uses for US states.

As a check, the outer edges match Spain's known extreme points: Cabo Touriñán in the west of the peninsula (9.30° W),
Cap de Creus in the east (3.33° E), Estaca de Bares in the north (43.79° N), Punta de la Orchilla on El Hierro in the
west and south of the whole country (18.16° W, 27.64° N), and Illa de l'Aire off Menorca in the east (4.33° E). The south
edge of Andalusia (35.94° N) is the island of Alborán, which belongs to the municipality of Almería.

| Code | INE | Name | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|
| `ES-AN` | 01 | Andalucía (Andalusia) | -7.5230, 35.9376, -1.6301, 38.7291 | -7.68, 35.78, -1.48, 38.88 |
| `ES-AR` | 02 | Aragón (Aragon) | -2.1737, 39.8468, 0.7713, 42.9244 | -2.33, 39.69, 0.93, 43.08 |
| `ES-AS` | 03 | Principado de Asturias (Asturias) | -7.1825, 42.8825, -4.5105, 43.6665 | -7.34, 42.73, -4.36, 43.82 |
| `ES-IB` | 04 | Illes Balears (Balearic Islands) | 1.1572, 38.6404, 4.3278, 40.0946 | 1.00, 38.49, 4.48, 40.25 |
| `ES-CN` | 05 | Canarias (Canary Islands) | -18.1612, 27.6377, -13.3350, 29.4165 | -18.32, 27.48, -13.18, 29.57 |
| `ES-CB` | 06 | Cantabria | -4.8518, 42.7580, -3.1496, 43.5137 | -5.01, 42.60, -2.99, 43.67 |
| `ES-CL` | 07 | Castilla y León (Castile and León) | -7.0771, 40.0819, -1.7754, 43.2382 | -7.23, 39.93, -1.62, 43.39 |
| `ES-CM` | 08 | Castilla-La Mancha | -5.4062, 38.0218, -0.9158, 41.3276 | -5.56, 37.87, -0.76, 41.48 |
| `ES-CT` | 09 | Cataluña / Catalunya (Catalonia) | 0.1591, 40.5230, 3.3326, 42.8614 | 0.00, 40.37, 3.49, 43.02 |
| `ES-VC` | 10 | Comunitat Valenciana (Valencian Community) | -1.5288, 37.8438, 0.6903, 40.7886 | -1.68, 37.69, 0.85, 40.94 |
| `ES-EX` | 11 | Extremadura | -7.5413, 37.9410, -4.6476, 40.4867 | -7.70, 37.79, -4.49, 40.64 |
| `ES-GA` | 12 | Galicia | -9.3015, 41.8072, -6.7340, 43.7924 | -9.46, 41.65, -6.58, 43.95 |
| `ES-MD` | 13 | Comunidad de Madrid | -4.5791, 39.8847, -3.0530, 41.1658 | -4.73, 39.73, -2.90, 41.32 |
| `ES-MC` | 14 | Región de Murcia | -2.3442, 37.3738, -0.6480, 38.7551 | -2.50, 37.22, -0.49, 38.91 |
| `ES-NC` | 15 | Comunidad Foral de Navarra (Navarre) | -2.5001, 41.9099, -0.7241, 43.3148 | -2.66, 41.75, -0.57, 43.47 |
| `ES-PV` | 16 | País Vasco / Euskadi (Basque Country) | -3.4503, 42.4724, -1.7293, 43.4572 | -3.61, 42.32, -1.57, 43.61 |
| `ES-RI` | 17 | La Rioja | -3.1343, 41.9190, -1.6787, 42.6443 | -3.29, 41.76, -1.52, 42.80 |
| `ES-CE` | 18 | Ciudad Autónoma de Ceuta | -5.3821, 35.8707, -5.2783, 35.9180 | -5.54, 35.72, -5.12, 36.07 |
| `ES-ML` | 19 | Ciudad Autónoma de Melilla | -2.9703, 35.2655, -2.9232, 35.3203 | -3.13, 35.11, -2.77, 35.48 |

Notes:

- **Islands.** The Canary Islands lie about 1,000 km south-west of the peninsula, so they must be their own region; one
  box for the whole country would be mostly ocean and Africa. Their box (about 5° by 2°) is the size of a mid-sized US
  state's. The Balearic box holds all four main islands.
- **Ceuta inside Andalusia's box.** With the margin, the Andalusia box reaches 35.78° N and so contains the whole of
  Ceuta and a strip of the Moroccan coast across the Strait. Melilla lies outside it. As with Berlin in REGIONS-DE.md, an
  Andalusia map would show Ceuta's streets but not Ceuta's addresses if address indexes are cut by region.
- **Enclaves.** The Condado de Treviño (Castilla y León) lies inside the Basque Country, Llívia (Catalonia) inside
  France, and the Rincón de Ademuz (Valencian Community) between Aragon and Castilla-La Mancha. Each is inside its own
  community's box because the boxes were computed from the full boundaries.
- **The plazas de soberanía** (Peñón de Vélez de la Gomera, the Alhucemas and Chafarinas islands) belong to no community
  and lie outside every box. They have no civilian population.

## Sources, layer by layer

| Layer (file) | US source today | Proposed for Spain | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP, 1 arc-second | **MDT25** (25 m, bare earth from PNOA-LiDAR ground points, 1st and 2nd coverage, COG); MDT05 or MDT02 where finer detail is wanted | IGN / CNIG | CC BY 4.0 (Orden FOM/2807/2015) | product page and licence PDF opened; coverage of the Canaries, Ceuta and Melilla and registration not confirmed |
| Terrain, alternative | | Copernicus DEM GLO-30 (surface model) | ESA / Airbus | Copernicus licence, as in REGIONS.md | opened |
| Water (`water.sqlite`) | NHD | MITECO "Ríos completos clasificados según Pfafstetter modificado", 1:25,000 (SHP, 436 MB, 2018); IGN "Hidrografía de España" (rivers, still water, dams) as an alternative; OSM | MITECO; IGN; OSM contributors | MITECO: free reuse with "Fuente: Ministerio para la Transición Ecológica y el Reto Demográfico", no named licence; IGN: CC BY 4.0; ODbL | MITECO page opened; IGN record search only (timed out) |
| Reservoirs | NHD water bodies | MITECO "Inventario de embalses" (shapefile) | MITECO | no licence text on the page | page opened; file not downloaded |
| Dams | NID | MITECO / SNCZI **Inventario de Presas y Embalses**: 3,208 dams with coordinates, owner, use, height and capacity (SHP, 348 KB, no login) | MITECO | not stated on the download page | file downloaded and read (see notes) |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | **SIGPAC** land-use parcels (yearly); CORINE Land Cover 2018 classes 221-223 as a coarse fallback | FEGA (Ministry of Agriculture); Copernicus / EEA | CC BY 4.0; CLMS data policy | FEGA ATOM page and CLC2018 page opened; SIGPAC use codes and per-municipality rule search only |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Overture buildings (which already include IGN's BTN 2024 for Spain); or the cadastres' INSPIRE buildings: DG Catastro for most of Spain, plus the foral cadastres of Bizkaia, Gipuzkoa, Álava and Navarre | Overture; DG Catastro; the four foral governments | ODbL / CC BY 4.0 (Overture); CC BY 4.0 (Catastro, Navarre, Álava); CC BY 3.0 ES (Bizkaia); **CC BY-SA** (Gipuzkoa) | Overture attribution opened; Catastro metadata, Bizkaia, Gipuzkoa and Navarre opened; Álava search only |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | Nomenclátor Geográfico Básico de España (NGBE); INE municipality register; GeoNames postcode points (`ES.zip`); OSM named places | IGN; INE; GeoNames; OSM contributors | CC BY 4.0; CC BY 4.0 (see notes); CC BY 4.0; ODbL | NGBE metadata and API opened; INE page opened; GeoNames readme opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **Overture addresses: 15,627,615 Spanish rows, every community, all but 549 with a postcode**; DG Catastro INSPIRE addresses and the foral sets to fill gaps | Overture Maps Foundation, from scne.es through OpenAddresses | CC BY 4.0 | attribution page and address guide opened; rows counted (see below) |
| Points of interest (`poi` rows) | OSM | OSM, as today | OSM contributors | ODbL | taginfo counts read |

Notes:

- **Terrain.** Unlike Germany, Spain has one national bare-earth model at close to the size the app uses today: MDT25,
  built from the national LiDAR programme. That avoids both the 16-source problem of REGIONS-DE.md and the canopy and
  roof problem of a surface model such as GLO-30. The exact attribution label for MDT25 comes from the product table at
  `scne.es/productos.html`, which was not opened. A CNIG manual (search only, possibly dated) says free products need
  no registration and bulk download runs through a separate Java application; that should be checked on one product
  page in a browser.
- **Dams.** The inventory file was downloaded and read: 3,208 records, in ETRS89 longitude and latitude, with the fields
  `NOMBRE`, `TITULAR`, `CATEGORIA`, `CAUCE`, `PROVINCIA`, `CCAA`, `TIPO`, `USO`, `NMN_CAPAC`, `COTA_CORON`, `ALT_CIMIEN`
  and others. Andalusia has 819, Castilla y León 401 and Extremadura 361; Ceuta has 2 and Melilla 1. **The Balearic
  Islands have none**, although Mallorca has the Cúber and Gorg Blau reservoirs, and 9 records have no community. So the
  inventory is a strong source but not a complete one. Its licence is in a metadata catalogue that is a JavaScript app
  and was not read.
- **Crops.** `tools/build_crops.py` keeps orchards, vineyards and berries. In Spain the most important permanent food
  crops are olives, citrus and nuts, which have no US class at all. SIGPAC's use codes are VI (vineyard), FY (fruit
  trees), FS (nut trees: almond, hazel, walnut, pistachio, carob), OV (olive grove) and CI (citrus), with mixed codes
  such as VO, OF and CF (search only, from regional official bulletins; FEGA's own code table could not be reached).
  SIGPAC is downloaded per municipality through an ATOM feed, so a national build means about 8,000 downloads. CORINE
  2018 has 221 (vineyards), 222 (fruit trees and berry plantations) and 223 (olive groves), but puts citrus and nuts
  inside 222 at a 25 ha minimum unit. The Ministry's older Mapa de Cultivos y Aprovechamientos (1:50,000, last updated
  2009) is not proposed. Whether the crop layer should grow new kinds for olives, citrus and nuts is a decision for the
  maintainers.
- **Buildings.** The DG Catastro covers all of Spain except the Basque Country and Navarre, which keep their own
  cadastres ("CC BY 4.0 DG Catastro", 95 % of the territory, ATOM per municipality, opened). Gipuzkoa's buildings and
  addresses are under a share-alike licence, which would add a condition no other source here has. Whether Ceuta and
  Melilla are in the DG Catastro feed was not checked. Overture's buildings already blend IGN's BTN 2024 ("Work derived
  from BTN 2024 ign.es", CC BY 4.0, opened) with OSM, Microsoft and Esri.
- **Places and languages.** NGBE names are in the original language: features returned by its API carry Galician
  spellings such as "Punta do Limo" (opened). A 2015 IGN presentation describes a separate extended-name field for
  bilingual names and a language field (search only); the API's `etiqueta` field shows one name only. The place finder
  should index both official forms of a bilingual name. INE's municipality page names CC BY-SA 4.0 in its footer but
  links to CC BY 4.0 (opened); that should be confirmed with INE.

## Addresses in Overture, measured

The Spanish rows of Overture release `2026-10-21.0` (the release `tools/build_addresses.py` defaults to) were read on
17 November 2026, with the same DuckDB query the builder uses but `country = 'ES'`:

- **15,627,615 addresses**, the same figure as Overture's address guide. One source, "scne.es, available under CC BY 4.0,
  distributed by OpenAddresses, accessed 2026-10-15" (attribution page, opened).
- **Postcodes.** 15,627,066 rows have a postcode, every one of them five digits. The first two digits are always 01 to
  52, which in Spain are the province codes. Splitting the rows by those two digits and mapping provinces to communities
  puts every row inside its community's padded box (0 outside). So an index per region can be cut by postcode prefix,
  which is exact, rather than by box, which overlaps.
- **House numbers.** 44,667 rows have no number, and 308,341 have `S-N` (*sin número*, "no number"), common in villages
  and the countryside. The builder keeps `S-N` rows as if `S-N` were a number.
- **Levels.** `address_levels` holds one level, the municipality (8,151 distinct values), and `postal_city` is always
  empty. The builder reads `address_levels[1]` as the state and keeps its first two letters, so a row in Arona would get
  the state `AR` (Arkansas, and also the Spanish code for Aragon) and an empty city. The region has to come from the
  postcode prefix instead, and the city from `address_levels[1]`.
- **Coverage by community.** Andalusia 3,169,403, Catalonia 2,126,882, Castilla y León 1,801,561, Valencian Community
  1,531,698, Castilla-La Mancha 1,318,826, Galicia 1,104,323, Madrid 933,226, Extremadura 623,773, Canary Islands 528,163,
  Aragon 480,557, Murcia 479,396, Balearic Islands 426,587, Asturias 336,254, Basque Country 221,689, Cantabria 203,877,
  Navarre 177,648, La Rioja 144,060, Melilla 11,674, Ceuta 7,469. The Basque Country has hardly more rows than Cantabria
  although its population is several times larger (population figures not reopened for this change). The Basque
  Country, outside the DG Catastro, is probably thinner in this source, and the foral address sets of Bizkaia, Gipuzkoa
  and Álava are the obvious way to fill it. That was not measured.

## Help points

OSM is the practical source for help points across Spain: no national open list with coordinates was confirmed for
hospitals, pharmacies, fire stations or police. The Ministry of Health's national hospital catalogue page loaded but its
download format and licence could not be read, and the health centre register (REGCESS) refused automated access. Counts
from taginfo for Geofabrik's Spain extract, data until 16 November 2026 21:20 UTC (opened):

| Tag | Count | Notes |
|---|---|---|
| `amenity=pharmacy` | 17,746 | |
| `amenity=fire_station` | 921 | far below the 29,226 in REGIONS-DE.md; the reason was not investigated |
| `amenity=police` | 3,767 | |
| `amenity=hospital` | 989 | |
| `amenity=clinic` | 6,467 | includes the *centros de salud* of primary care |
| `amenity=drinking_water` | 44,411 | public drinking fountains, very common in Spain |
| `man_made=water_tap` | 7,435 | |
| `man_made=water_well` | 5,550 | |
| `natural=spring` | 15,337 | not drinkable by default |
| `emergency=water_tank` | 2,011 | mostly firefighting water, not drinking water |
| `emergency=drinking_water` | 0 | the German emergency-well tag is not used in Spain |
| `emergency=defibrillator` | 5,435 | |
| `tourism=wilderness_hut` | 854 | |
| `tourism=alpine_hut` | 435 | |

Three Spanish kinds of point are worth a decision:

- **Drinking fountains.** With 44,411 `amenity=drinking_water` points, public fountains are the densest water source on
  the map, in towns and on mountain paths. Decorative fountains (`amenity=fountain`, 12,144) should count only when they
  also carry `drinking_water=yes`; springs only with a plain "untreated" label.
- **Mountain huts and refuges.** Unstaffed huts (`wilderness_hut`, `alpine_hut`, and `amenity=shelter` with
  `shelter_type=basic_hut`) are real shelter in the mountains. Plain
  `amenity=shelter` (6,833) also holds bus stops and picnic roofs and needs the `shelter_type` filter.
- **Defibrillators.** OSM's 5,435 are thin: Catalonia's own register of defibrillators outside health centres alone has
  12,853 rows with coordinates and opening hours (opened through its open data API; its licence is behind a "Terms of
  Use" link that was not read). Several other communities publish similar lists on datos.gob.es (catalogue search
  only; the individual datasets were not opened), mostly without a declared licence. A defibrillator layer would be a patchwork of regional sources, or
  OSM with a plain "incomplete" note.

## Licence notes and attribution

All proposed licences allow redistribution in a free offline library, including commercial reuse, except where noted.
What each asks:

- **CC BY 4.0, IGN and CNIG** (MDT, hydrography, NGBE, boundaries, BTN). The licence comes from Orden FOM/2807/2015.
  The credit follows the pattern «<product> <date> CC-BY 4.0 <producers>», for example "BTN25 2014-2015 CC-BY 4.0 ign.es",
  and a derived work adds «Obra derivada de …». It must be shown legibly "a pie de mapa", at the foot of the map, or in
  the credits only where that is truly impossible (licence PDF, opened). This is stricter than the other proposals: the
  app would need a visible credit line on the map itself.
- **CC BY 4.0, others**: Overture's scne.es addresses ("scne.es, distributed by OpenAddresses"), DG Catastro (no fixed
  sentence was found; "Fuente: Dirección General del Catastro" is the natural one), Navarre, FEGA, GeoNames ("give
  credit to GeoNames").
- **MITECO.** Free reuse with "Fuente: Ministerio para la Transición Ecológica y el Reto Demográfico", and no named
  licence on the pages opened. datos.gob.es's legal notice allows commercial and non-commercial reuse under Ley 37/2007
  (opened), but whether it covers these files was not confirmed.
- **CC BY 3.0 ES, Bizkaia.** Credit "Bizkaiko Foru Aldundia - Diputación Foral de Bizkaia" with the date of last update.
- **CC BY-SA, Gipuzkoa.** Share-alike: a database built from it would have to be offered under the same terms.
- **ODbL** (OSM, Overture buildings). As for the US map.

These notices would belong wherever the map already credits its sources, and in `THIRD_PARTY_NOTICES.md` if that is
where the maintainers keep data licences.

## How addresses are written

- **Order.** Street type, street name, then the number, then postcode and town: "Calle de Alcalá, 45, 28014 Madrid".
  The type comes first (*Calle*, *Avenida*, *Plaza*, *Paseo*, *Camino*, *Carretera*) and is often abbreviated (*C/*,
  *Avda.*, *Pza.*, *Pº*). A floor and door often follow the number ("45, 3º izq.").
- **Postcode.** Five digits, the same shape as a US ZIP code. The first two are the province, so leading zeros are
  common (Álava is `01`, Barcelona `08`) and a postcode must stay text.
- **Other languages.** Street types also appear in the regional languages: *Rúa* (Galician, 228,754 rows), *Avinguda*
  (131,001) and *Plaça* (39,585) in Catalan and Valencian. Basque names keep their own word for street after the name, and
  Overture puts a Spanish type in front of it ("CALLE KALE ZAHARRA"; 22,960 street names contain *kalea*). Town names can carry two official forms
  joined by a slash ("Arrasate/Mondragón").
- **How Overture writes them.** Street names are in capitals (all but 3,852 rows), mostly without accents ("CALLE
  CANTABRICO", "CALLE JATIVA"), with the type first and leading articles moved to the end, cadastre style ("CALLE
  CUEVAS LAS"; 409,915 street names end in *el*, *la*, *los*, *las*, *de* or *del*). The commonest first words are
  *CALLE* (10.1 million), *LUGAR* (770,345, hamlets, 87 % of them in Galicia and Asturias), *AVENIDA*, *CARRETERA*, *PLAZA*, *CAMINO* and
  *DISEMINADOS* (380,421, scattered rural houses).
- **What the current code does with that** (read in this repository and tried on examples on 17 November 2026):
  - `normalize()` in `engine/address_search.py` and `norm()` in `tools/build_addresses.py` keep only `a-z` and `0-9`,
    so "Alcalá" becomes `alcal` and "Peña" `pe a`, while Overture's "ALCALA" becomes `alcala`. Accents and *ñ* need
    folding (á to a, ñ to n, ç to c, l·l to ll) on both sides.
  - `is_address_query()` needs a number first, so "Calle de Alcalá 45, 28014 Madrid", "C/ Alcalá, 45" and "Avinguda
    Diagonal 640, 08017 Barcelona" are not treated as addresses. Only "45 Calle Alcalá 28014" is.
  - `_parts()` takes a postcode only as the last word, while Spanish addresses put the town after it.
  - Matching would also need the type words and their abbreviations (*c*, *avda*, *pza*), and to ignore the articles
    Overture moves to the end, so that "Calle de las Cuevas" finds "CALLE CUEVAS LAS".
  - `tools/build_addresses.py` keeps only `country = 'US'`, reads the state from `address_levels[1]` (the municipality
    in Spain) and the city from `postal_city` (empty in Spain); see "Addresses in Overture, measured".
  - The five-digit postcode rule itself fits Spain unchanged.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md and the
other proposals.

1. **Codes in setup.** Whether `ES-AN` and the others are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup groups 19 Spanish regions.
   One place this already matters: when a library is upgraded, `carry_over()` in `engine/setup/install.py` keeps only
   address indexes named `[A-Z]{2}.sqlite` or `.json`, so an index named `ES-MD.sqlite` (or any hyphenated code in the
   other proposals) would be left behind in the old library without a message (read in this repository on
   17 November 2026).
2. **The box rule**, as in REGIONS.md, here from IGN's administrative units.
3. **Communities or provinces.** 19 regions, or 50 provinces, which match postcodes and Overture's data more closely.
4. **Postcodes.** Correos owns the postcode areas, and its agreement with CNIG (BOE-A-2023-11522, opened) says the postcode
   layer "no podrá ser facilitada mediante ningún servicio de descarga, plataforma de descarga o de ninguna otra forma"
   and "no podrá ser facilitada y/o suministrada por cualquier medio a terceros". So a postcode *area* layer, like the
   US ZCTAs in the place finder, is not proposed. The postcode *attached to each address* in Overture's CC BY 4.0 data is
   a different thing and is what address search needs; whether Correos' rights reach it was not checked.
5. **The foral territories.** Whether to fill the Basque Country's addresses and buildings from the foral cadastres, and
   whether Gipuzkoa's share-alike licence is acceptable.
6. **New crop kinds**: olives, citrus and nuts.
7. **The map credit line.** IGN's licence asks for the credit at the foot of the map, not only in an about page.
8. **Bilingual names**: whether the place finder and address search index both official forms.

## What was checked, and what was not

- Opened on 17 November 2026: IGN's data policy page and licence PDF; the CNIG elevation models page; IGN's INSPIRE
  administrative units service; MITECO's hydrography downloads page and quick data access page; the dam inventory file
  (downloaded and read); the Copernicus DEM collection page; FEGA's SIGPAC ATOM page; the CORINE 2018 product page; the
  SIOSE home page; NGBE's metadata record and API; INE's municipality code page; GeoNames' postcode readme; Overture's
  attribution page and address guide; the Overture address rows themselves (queried with DuckDB); DG Catastro's
  INSPIRE address metadata and ATOM feed; the Bizkaia, Gipuzkoa and Navarre cadastre download pages; the BOE text of the
  Correos agreement; Geofabrik's taginfo for Spain; Catalonia's defibrillator register (API); the datos.gob.es catalogue
  API and legal notice.
- Computed on 17 November 2026: the 19 boxes, from IGN's administrative units as described above; the address counts
  and checks, from Overture release 2026-10-21.0; the dam counts, from the inventory file.
- Seen only in search results: the SIGPAC use codes and per-municipality download rule; the CNIG download manual; IGN's
  "Hidrografía de España" record; the Mapa de Cultivos y Aprovechamientos; NGBE's bilingual-name field; CartoCiudad's
  provincial address downloads; Álava's building licence; Navarre's address service.
- Not checked: the MDT25 attribution label (`scne.es/productos.html`) and its coverage of the Canaries, Ceuta and
  Melilla; the dam and reservoir inventories' licence; FEGA's code table; the CLMS data policy; REGCESS (refused automated
  access); the national hospital catalogue's format; Madrid's open data portal (did not respond); Catalonia's
  defibrillator licence; Catastro coverage of Ceuta and Melilla; the population figures behind the Basque coverage note;
  and the ISO 3166-2:ES codes against the ISO site.
