# Detailed maps for Paraguay: a proposal

This is a proposal for discussion, not a decision. It answers, for Paraguay, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a "state"
is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md), [REGIONS-AR.md](REGIONS-AR.md)
and [REGIONS-LK.md](REGIONS-LK.md) and is meant to feed the same design discussion (issues #23, #25 and #31). The
machine-readable version is [regions-py-proposed.json](regions-py-proposed.json), and a Spanish translation is
[REGIONS-PY.es.md](REGIONS-PY.es.md).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026. Each fact carries one of these marks:

- **opened**: the page, file or API response itself was opened and read;
- **computed**: the figure was computed here from a downloaded file (the file and method are named);
- **search only**: the fact was seen in a search result, but the page itself was not opened;
- **general knowledge**: stated from memory, with no source opened; it needs a local reader's check;
- **not checked**: the page could not be reached or read; the row says what is missing.

"None found" means none found by web search. Paraguay's national open data portal (`datos.gov.py`) showed a maintenance
page on 17 November 2026, so its catalogue could not be searched. The Overpass API could not be reached either, so OSM
figures were counted from Geofabrik's extract.

## What a region is

Paraguay has 17 departments and the capital district of Asunción. The proposal is **one region for the whole country**,
code `PY`, as REGIONS.md proposes for Guyana and REGIONS-LK.md for Sri Lanka. A bare `PY` collides with no code in
`STATE_CODES` (`engine/address_search.py`).

Why one region:

- **Size.** Paraguay's polygon in OCHA's COD-AB covers 399,603 km² (its `area_sqkm` attribute; the official figure is
  406,752 km², general knowledge). That is a little less than California (423,970 km², general knowledge), which
  Lastbook already ships as one state map. The whole-country OSM extract is 147 MB, close to Sri Lanka's 137 MB.
- **Departments are small.** Central is 2,413 km² and Asunción 129 km², far smaller than most US states.
- **How people live and move.** Greater Asunción spans the capital district and much of Central. It also takes in
  districts of Presidente Hayes across the river and, by some definitions, parts of Cordillera and Paraguarí (search
  only). Someone there who picked one department's map would lose part of the city they live in, the same problem
  REGIONS-AR.md describes for Buenos Aires.
- **The west is nearly empty.** The three western departments (Presidente Hayes, Boquerón and Alto Paraguay) hold 60%
  of the land (from the `area_sqkm` figures below). Only a small share of the people live there (general knowledge; not
  checked against the 2022 census), so their data should add little to a whole-country map.

If the maintainers prefer finer regions, the department boxes are listed below. A middle option is two regions: eastern
Paraguay (14 departments and Asunción) and the Chaco (the three western departments), split along the Paraguay River.
That split would also cut Greater Asunción, whose Chaco side lies in Presidente Hayes.

### Box

| Code | Name | Box (west, south, east, north) | Box with 0.15° margin | Box taken from |
|---|---|---|---|---|
| `PY` | Paraguay | -62.6446, -27.5918, -54.2589, -19.2876 | -62.80, -27.75, -54.10, -19.13 | OCHA COD-AB level 0 (computed) |

The box is the extent of every vertex of OCHA's level 0 polygon for Paraguay (`pry_admin0.geojson`, source INE, valid
from 29 July 2026; downloaded and computed on 17 November 2026), minus/plus 0.15° and rounded outward to 0.01°, the same
margin `map_sets.state` uses for US states. Geofabrik's clipping polygon (`paraguay.poly`, opened) gives a looser box,
-62.6948, -27.6568, -54.2018, -19.2401, as expected for a polygon drawn around the border.

**Neighbours inside the box.** A rectangle around Paraguay holds a lot of its neighbours (from a sample of points inside
the box; not measured). In Argentina: all of Formosa province, most of Chaco province (with Resistencia), the north of
Corrientes (with Corrientes city), most of Misiones province, a corner of Santiago del Estero and a sliver of Salta. In
Brazil: much of Mato Grosso do Sul, the western edge of Paraná (with Foz do Iguaçu) and a corner of Rio Grande do Sul.
In Bolivia: parts of the south-east.

Several Paraguayan cities have a twin city across the border: Encarnación and Posadas, Ciudad del Este and Foz do
Iguaçu, Pedro Juan Caballero and Ponta Porã, Asunción and Clorinda.

Geofabrik's extract is already cut a few kilometres outside the border, so a first build from it holds almost nothing
of the neighbours, and cuts the twin cities. Keeping Posadas, Foz do Iguaçu, Ponta Porã and Clorinda whole means adding
data from the Argentina and Brazil extracts. The suggestion is to keep the border as the edge for a first build, and
later add a band (for example 20 km) for the twin cities. This is left to the maintainers.

No boundary here is known to be disputed (general knowledge); the point is listed only so it is decided once for every
region (REGIONS.md item 6).

### Departments, if finer regions are wanted

ISO 3166-2:PY gives `PY-ASU` for Asunción and `PY-1` to `PY-16` and `PY-19` for the departments (search only; not
checked against the ISO site). There is no `PY-17` or `PY-18`.

**Watch the numbering.** OCHA's p-codes do not match ISO for two departments: in COD-AB, `PY16` is Boquerón and `PY17`
is Alto Paraguay, while ISO has `PY-16` for Alto Paraguay and `PY-19` for Boquerón. Anything joining the two must join
by name, not by number.

The boxes were computed from OCHA's level 1 polygons (`pry_admin1.geojson`, 18 features) by the same rule as above.

| ISO code | COD-AB p-code | Name | Box (west, south, east, north) | Box with 0.15° margin | Area (km², `area_sqkm`) |
|---|---|---|---|---|---|
| `PY-ASU` | PY00 | Asunción | -57.6739, -25.3809, -57.5248, -25.2246 | -57.83, -25.54, -57.37, -25.07 | 129 |
| `PY-1` | PY01 | Concepción | -57.9938, -23.5095, -56.1258, -22.0791 | -58.15, -23.66, -55.97, -21.92 | 18,543 |
| `PY-2` | PY02 | San Pedro | -57.4735, -25.0193, -55.7020, -23.3007 | -57.63, -25.17, -55.55, -23.15 | 20,852 |
| `PY-3` | PY03 | Cordillera | -57.4783, -25.6690, -56.5614, -24.8433 | -57.63, -25.82, -56.41, -24.69 | 4,790 |
| `PY-4` | PY04 | Guairá | -56.7477, -26.1973, -55.6334, -25.5648 | -56.90, -26.35, -55.48, -25.41 | 3,870 |
| `PY-5` | PY05 | Caaguazú | -56.8115, -25.7084, -54.9232, -24.4655 | -56.97, -25.86, -54.77, -24.31 | 12,904 |
| `PY-6` | PY06 | Caazapá | -56.8491, -26.7944, -55.2482, -25.5236 | -57.00, -26.95, -55.09, -25.37 | 9,550 |
| `PY-7` | PY07 | Itapúa | -56.8848, -27.5918, -54.6482, -26.0922 | -57.04, -27.75, -54.49, -25.94 | 15,866 |
| `PY-8` | PY08 | Misiones | -57.7431, -27.4861, -56.6259, -26.3761 | -57.90, -27.64, -56.47, -26.22 | 8,160 |
| `PY-9` | PY09 | Paraguarí | -57.7494, -26.6196, -56.6076, -25.4018 | -57.90, -26.77, -56.45, -25.25 | 8,603 |
| `PY-10` | PY10 | Alto Paraná | -55.5506, -26.2571, -54.3458, -24.4762 | -55.71, -26.41, -54.19, -24.32 | 14,209 |
| `PY-11` | PY11 | Central | -57.8268, -26.0251, -57.1930, -25.0965 | -57.98, -26.18, -57.04, -24.94 | 2,413 |
| `PY-12` | PY12 | Ñeembucú | -58.6649, -27.4442, -57.1821, -25.7672 | -58.82, -27.60, -57.03, -25.61 | 11,675 |
| `PY-13` | PY13 | Amambay | -56.8261, -23.8309, -55.5045, -22.0745 | -56.98, -23.99, -55.35, -21.92 | 12,548 |
| `PY-14` | PY14 | Canindeyú | -56.1725, -24.7840, -54.2589, -23.5237 | -56.33, -24.94, -54.10, -23.37 | 15,029 |
| `PY-15` | PY15 | Presidente Hayes | -60.7854, -25.3543, -57.1493, -22.0762 | -60.94, -25.51, -56.99, -21.92 | 73,655 |
| `PY-16` | PY17 | Alto Paraguay | -61.9225, -22.3992, -57.8171, -19.2876 | -62.08, -22.55, -57.66, -19.13 | 78,542 |
| `PY-19` | PY16 | Boquerón | -62.6446, -23.8858, -59.3366, -20.0892 | -62.80, -24.04, -59.18, -19.93 | 88,265 |

Asunción lies between Central and the Paraguay River, and the Central box already contains the whole Asunción box, so
a `PY-11` map cut by its box holds Asunción too. The metropolitan area is wider: it also takes in the Villa Hayes side
of Presidente Hayes. A map of the metropolitan area would be a separate grouping with its own id, as REGIONS-TH.md does
for Bangkok and its vicinity, not a `PY-11` that means more than Central.

**Already in flight.** PR #35 has a `py-asu` box for Asunción (-57.94, -25.59, -57.34, -24.99), cut from the same
Geofabrik extract. A whole-country region would replace that box with the full extract; it needs no new source.

**Possible cross-check.** geoBoundaries' ADM1 file for Paraguay (CC BY 4.0, 18 units, from the 2012 DGEEC departments;
metadata opened) could be used to check the boxes. It was not downloaded.

## Sources, layer by layer

OpenStreetMap is the backbone for a first build, as for Guyana and Sri Lanka. Paraguay's statistics office (INE,
formerly DGEEC) publishes the census boundaries, which it says are for reference only, and a 2012 census cartography
with streets, blocks and water. MapBiomas publishes a national land cover series. No open national lists of health
facilities, fire stations or dams were found.

| Layer (file) | US source today | Proposed for Paraguay | Publisher | Licence | Mark |
|---|---|---|---|---|---|
| Roads, water, land (base map) | OSM extract | OSM extract `paraguay-latest.osm.pbf` (147 MB; the `.shp.zip` is 305 MB and the `.gpkg.zip` 312 MB), data up to 16 November 2026 21:22 UTC | OSM contributors via Geofabrik | ODbL 1.0 | opened |
| Points of interest (`poi`) | OSM | OSM (counts below) | OSM contributors | ODbL 1.0 | computed |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | OCHA COD-AB levels 1 to 4 (departments, districts, and two finer levels) and its `adminpoints` and `admincapitals` files; OSM named places | OCHA, from INE; OSM contributors | CC BY-IGO; ODbL 1.0 | HDX record opened. Admin0 and admin1 downloads confirmed. |
| Places and streets, official | | INE "Cartografía Digital 2012": departments, districts, barrios and localities, cities, blocks (manzanas), roads, main roads, hydrography and indigenous communities, as Shape, KML and GeoJSON for the country and each department | INE | Licencia de Uso de la Información Pública del Gobierno Paraguayo | opened |
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, as proposed for Guyana | ESA / Airbus | Copernicus WorldDEM-30 licence | as in REGIONS.md |
| Water (`water.sqlite`) | NHD | OSM waterways and water areas; INE 2012 hydrography to fill gaps | OSM contributors; INE | ODbL 1.0; INE licence | opened (INE layer list) |
| Dams | NID | OSM `waterway=dam` and `water=reservoir`; no open dam inventory found | OSM contributors | ODbL 1.0 | computed |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | MapBiomas Paraguay, annual land cover and land use maps 1985 to 2023 (Collection 2, 30 m, from Landsat); ESA WorldCover 2021 as a fallback | MapBiomas Paraguay; ESA WorldCover consortium | CC BY (see notes); CC BY 4.0 | opened (terms page); collection details search only |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Google Open Buildings v3 (Paraguay is in its country list; inferred May 2023); Microsoft Global ML Building Footprints to fill gaps; OSM heights | Google; Microsoft; OSM contributors | CC BY 4.0 or ODbL 1.0, at the user's choice (Google); see REGIONS.md for Microsoft; ODbL | opened (Google's page); coverage not measured |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **None found.** Overture's address theme lists 41 countries, and Paraguay is not among them | | | opened |

### Help and resource points

Counts were made with pyosmium over the Geofabrik extract above (data up to 16 November 2026 21:22 UTC). Each count
includes nodes, ways and relations carrying the tag.

| Kind | OSM tag | Count | Other source | Mark |
|---|---|---|---|---|
| Hospitals | `amenity=hospital` | 387 | Ministry of Health (MSPBS) list, see notes | computed |
| Clinics and doctors | `amenity=clinic`, `amenity=doctors` | 657 (412 clinics, 245 doctors) | as above | computed |
| Pharmacies | `amenity=pharmacy` | 1,377 | none found | computed |
| Fire stations | `amenity=fire_station` | 123 (100 named) | Volunteer fire brigades (CBVP), see notes | computed |
| Police | `amenity=police` | 1,508 | none found | computed |
| Drinking water | `amenity=drinking_water`, `man_made=water_tap`, `amenity=water_point` | 83 (56, 21, 6) | none found | computed |
| Wells, water towers and tanks | `man_made=water_well`, `water_tower`, `storage_tank` | 1,738 (177 wells, 935 towers, 626 tanks, contents not checked) | none found | computed |
| Reservoirs and dams | `water=reservoir`, `waterway=dam` | 2,852 reservoirs (`landuse=reservoir` not counted), 291 dams | none found | computed |
| Fuel | `amenity=fuel` | 1,577 | none found | computed |
| Ambulance stations | `emergency=ambulance_station` | 5 | none found | computed |
| Shelters and assembly points | `amenity=shelter`, `social_facility=shelter`, `emergency=assembly_point` | 289 (284, 5, 0) | National Emergency Secretariat (SEN), see notes | computed |
| Schools | `amenity=school` | 4,748 | Ministry of Education (MEC) open data, see notes | computed |

Notes:

- **A count of rows is not a count of places.** OSM often has one hospital as a point and again as each of its
  buildings, and tags some laboratories, consulting rooms and health posts as hospitals. In a test map of Central and
  Asunción, 163 hospital rows were about 113 sites (rows within 150 m grouped). The counts above are upper bounds.
- **Health.** No downloadable list of health facilities with coordinates was found. Reports say the Ministry of Health
  holds one: it has committed to publishing it as open data, and a 2021 report for PAHO obtained it by formal request
  (both search only). Asking the Ministry for the list under an open licence is the most useful single step for this
  map.
- **Fire stations.** Firefighting in Paraguay is largely done by volunteer brigades. News reports give about 140
  stations for the Cuerpo de Bomberos Voluntarios del Paraguay (search only); no published list of their locations was
  found. OSM's 123 fire stations (100 of them named) are close to that figure, so OSM may already cover most of them.
  Matching the two would need the brigades' own list.
- **"Shelter" in OSM.** `amenity=shelter` marks small roofs, not emergency shelters. Of the 284 in Paraguay, by
  `shelter_type` (computed): 93 lean-to, 70 picnic shelter, 67 sun shelter, 41 with no type, 5 pavilion, 4 public
  transport, 3 gazebo and 1 weather shelter. They should not be drawn as emergency shelters. No OSM emergency assembly
  points were found in Paraguay.
- **Flood shelters.** Floods along the Paraguay and Paraná rivers displace families most years, and the National
  Emergency Secretariat (SEN) opens shelters with the municipalities (search only, news reports). No dataset of shelter
  locations was found. These shelters are often temporary, so a fixed list may not suit them. That is for the
  maintainers to decide.
- **Water in the Chaco.** In the western region, rainwater cisterns (aljibes) and earth reservoirs (tajamares) are the
  main water sources (general knowledge). No dataset of them was found. The 2,852 OSM reservoirs above probably include
  many tajamares, but that was not checked, and cisterns are rarely mapped. This is the clearest gap for this region.
- **Schools.** The Ministry of Education's open data is published under CC BY 4.0 (search only); whether it includes
  coordinates was not checked.
- **Terrain.** Copernicus GLO-30 is a surface model: under forest it follows the canopy, not the ground. No open
  national elevation model was found.
- **Crops.** MapBiomas Paraguay maps land cover and land use classes (forest, grassland, farming and so on), not crop
  types. `tools/build_crops.py` keeps orchards, vineyards and berries from the CDL, so the class mapping needs a decision
  (as item 4 in REGIONS.md). MapBiomas also runs a separate Gran Chaco series that covers the western region with its
  Argentine and Bolivian parts (search only).
- **INE 2012 cartography.** It predates the 2022 census. INE lists updated department and district cartography among the
  2022 census products and runs a geostatistical portal (search only), but no downloadable 2022 files were found.
- **Addresses.** OSM has 44,614 objects with `addr:housenumber` in Paraguay (computed), which is not enough for
  address search across the country. INE's 2012 blocks are polygons; whether they carry door-number ranges was not
  checked. So a first Paraguayan map would ship as "street map, places and help points" without address search, as
  suggested for Sri Lanka.

## Licence notes and attribution

- **INE licence** (opened: `ine.gov.py/microdatos/license.php`, which cites Law 5282/2014 and Decree 4064). A free,
  perpetual, non-exclusive licence for any lawful use, including copying, extraction, reproduction, distribution, public
  communication, adaptation and transformation. In return:
  - cite the public source that provided the data;
  - say that the content is under this licence;
  - give the date of the last update, if known;
  - do not suggest or simulate an official use or one sponsored by the Paraguayan State.

  It allows any lawful use and sets no share-alike or non-commercial condition. Where the app shows the credit, the
  licence notice and the data date is REGIONS.md item 5.
- **CC BY-IGO** (OCHA's COD-AB, opened through HDX's API: source "Dirección General de Estadísticas, Encuestas y Censos
  (DGEEC), INE"; last modified 24 September 2026). Credit OCHA and its source.
- **MapBiomas Paraguay.** Its terms page (opened) says the data are public, open and free under a Creative Commons CC BY
  licence, and asks to be cited as "MapBiomas – Colección [versión] de la Serie Anual de Mapas de Cobertura y Uso del
  Suelo de Paraguay", with the access date and link. A search result for the same page showed "CC-CY-SA" (sic), and a
  mirror on Source Coop lists CC BY-SA 4.0 (search only). Whether share-alike applies has to be confirmed with MapBiomas
  before a build.
- **ODbL, CC BY 4.0 and Copernicus WorldDEM-30:** as in REGIONS.md. Google Open Buildings can be taken under either
  CC BY 4.0 or ODbL 1.0.

## How addresses are written

Not checked against Correo Paraguayo's own pages. This part needs a Paraguayan reader's review.

- **Order.** Street name, then door number, then the city: "José Martí 1953, Luque" (search only, from a commercial
  address-format guide). As in Argentina, the number comes after the street, the opposite of the order
  `engine/address_search.py` expects.
- **Corners** (general knowledge). Many addresses are given by corner, "Calle X c/ Calle Y" (c/ for *casi*, "almost at
  the corner of") or "Calle X esq. Calle Y" (*esquina*, "at the corner of"), and many homes have no number ("s/n",
  *sin número*). Street names often carry abbreviated titles such as "Avda.", "Mcal." (*Mariscal*) and "Gral."
  (*General*).
- **Postal code.** Six digits: two for the department, two for the district, two for the barrio (search only). Older
  four-digit codes are still seen (general knowledge). Correo Paraguayo (DINACOPA) has an online look-up (search only; not opened).
- **What the current code does with that.**
  - `engine/address_search.py` reads a postcode only as five digits (`\d{5}`), so it would miss a six-digit code, and
    `tools/build_addresses.py` keeps the first five characters (`left(postcode, 5)`), which would cut off the last digit
    of the barrio.
  - `normalize()` in `engine/address_search.py` and `norm()` in `tools/build_addresses.py` keep only `a-z`, `0-9` and
    spaces, so every other letter becomes a space: "Avda. Mcal. López 1234 c/ Ñeembucú" becomes
    `avda mcal l pez 1234 c eembuc` (tested 17 November 2026). REGIONS-DE.md found the same for German. Folding is
    needed on both sides, and #79 proposes that each index declares its own rule.
  - The place finder is already fine: its FTS5 index uses the `unicode61` tokenizer, which folds diacritics. Tested on
    17 November 2026, searches for `neembucu`, `ypacarai` and `itapesyi` found "Ñeembucú", "Ypacaraí" and "Itapesỹi"
    (a neighbourhood's `name:gn` in the extract, with the Guaraní letter ỹ). No place name with g̃ (g with a combining
    tilde) was found in the extract; a made-up spelling with it was matched by plain `g` as well.

## Language

Spanish and Guaraní are both official languages (general knowledge). Many place names are Guaraní (Ñeembucú, Caaguazú,
Itapúa, Ypacaraí), and Guaraní spelling uses letters Spanish does not: ã, ẽ, ĩ, õ, ũ, ỹ and g̃. Whether the base map's
fonts draw them was not checked; g̃ has no precomposed character in Unicode. OSM carries `name:gn` on 147 objects in
the extract (computed). Whether to keep it is part of the language question in issues #3 and #54.

## Still undecided

Each of these needs the maintainers' decision before any code changes. Items 1, 2, 4 and 5 correspond to REGIONS.md
items 1, 2, 4 and 3, and item 8 to its item 7.

1. **Codes in setup.** Whether `PY` is acceptable as a manifest `id`, in `map-set.json` and in `Lastbook-Map-PY.zip`,
   and, if departments are wanted, whether hyphenated codes such as `PY-ASU` are.
2. **The box rule.** Whether the border is the edge of a first build, and whether a band is added later so the twin
   cities across the border are whole.
3. **One region, two, or eighteen.** The whole country (proposed), eastern Paraguay and the Chaco, or each department
   plus a separate map for the metropolitan area.
4. **MapBiomas' licence**: CC BY or CC BY-SA, and how its land cover classes map to the crop layer.
5. **Address search.** Six-digit postcodes, number after the street, corners given with "c/" and "esq.", and folding
   accents before matching. Without an open address source, a first map ships without address search.
6. **Help points with no open source**: health facilities, volunteer fire stations, flood shelters, and Chaco water
   sources (aljibes and tajamares). Who to ask, and whether OSM alone is enough for a first build.
7. **Language**: which name the map shows when Spanish and Guaraní names differ, and font coverage for Guaraní letters.
8. **The California-only layers.** As REGIONS.md item 7.

## What was checked

- Opened on 17 November 2026: Geofabrik's Paraguay page (file sizes, data date) and `paraguay.poly`; OCHA's COD-AB
  record for Paraguay through HDX's API (licence, source, dates, files); INE's "Cartografía Digital 2012" page and its
  licence page; MapBiomas Paraguay's terms of use; Overture's addresses guide (release 2026-10-21.0, 41 countries);
  Google's Open Buildings page (Paraguay in the v3 list, licence choice); geoBoundaries' metadata for Paraguay ADM1;
  `datos.gov.py` (maintenance page only); the diff of PR #35 (its `py-asu` box).
- Downloaded and computed on 17 November 2026: OCHA's COD-AB GeoJSON (the country and department boxes; areas are the
  file's `area_sqkm` attribute) and Geofabrik's `paraguay-latest.osm.pbf` (the OSM counts, and the test map of Central
  and Asunción behind the hospital note).
- Tested on 17 November 2026: `normalize()` in `engine/address_search.py`, and an FTS5 `unicode61` index like the one
  `tools/build_places.py` builds, on Spanish and Guaraní names.
- Search only: ISO 3166-2:PY codes, the extent of Greater Asunción, MapBiomas collection details and the CC BY-SA
  mirror, the postal code format, the sample address and the DINACOPA look-up, Ministry of Health and PAHO reports,
  volunteer fire station numbers, SEN shelters, MEC open data licence, INE's 2022 census cartography.
- General knowledge, for a local reader to confirm: Paraguay's official area and California's, where people live, the
  corner and "s/n" address forms, four-digit postcodes, the official languages, Chaco water sources, and that no
  boundary is disputed.
- Not checked: the ISO site, Correo Paraguayo's look-up, the MSPBS and SEN sites, the CBVP's own site, `datos.gov.py`'s
  catalogue (under maintenance), INE's geostatistical portal, door-number coverage of INE's 2012 blocks, font coverage
  of Guaraní letters, how much of each neighbour the box holds, and Google Open Buildings coverage of Paraguay.
