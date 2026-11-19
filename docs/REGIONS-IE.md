# Detailed maps for the island of Ireland: a proposal

This is a proposal for discussion, not a decision. It answers, for the island of Ireland, the questions
[MAPS.md](MAPS.md) asks before coverage can go beyond the United States: which open source replaces each federal list,
under what licence, what a "state" is there, and how addresses are written. It follows the shape of
[REGIONS-LK.md](REGIONS-LK.md) and [REGIONS-DE.md](REGIONS-DE.md) and is meant to feed the same design discussion
(issues #23, #25 and #31). The machine-readable version is [regions-ie-proposed.json](regions-ie-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026, with AI research agents reading the publishers' own
pages, a second agent checking the draft against the sources and the code, and a person reviewing the result. Each
source carries one of three marks:

- **opened**: the dataset or licence page itself was opened and read;
- **search only**: the fact was seen in a search result, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

OpenDataNI's licence and dataset pages returned HTTP 500 or 403, and OSNI's map service did not resolve, so several
Northern Ireland rows are "search only". They need a second look before anything is built on them.

## What a region is

The proposal is **one region for the whole island**: the Republic of Ireland and Northern Ireland together.

- **It is one place on the ground.** There are no routine checks at the border (general knowledge), and someone in the
  Republic may well travel into Northern Ireland during an emergency, or the other way. A map that stops at the border
  would go blank on roads people use.
- **It is small.** The island is about 84,000 km² (general knowledge, not measured here), smaller than many single US
  states that already get one map each. A split by province or county would make a person choose between maps they may
  move between.
- **The source data is already cut this way.** Geofabrik publishes one OpenStreetMap extract for the island,
  "Ireland and Northern Ireland".

The cost is that the region spans two countries. Northern Ireland is part of the United Kingdom, so its official data
comes from different publishers under different licences (OSNI and Land & Property Services under UK terms; Tailte
Éireann, the EPA and data.gov.ie under Irish terms). The tables below list both.

### Code

| Option | For | Against |
|---|---|---|
| `IE` | Short; collides with no US code in `STATE_CODES` (`engine/address_search.py`, checked) | `IE` is the ISO 3166-1 code of the Republic only, and Northern Ireland is `GB-NIR` (general knowledge, not checked against the ISO site) |
| `eu-ie` | Matches PR #84 | Same caveat, and depends on #84's scheme being chosen |

The proposal picks no code: it takes whatever scheme the maintainers choose for countries. It asks only that the name
be **"Ireland and Northern Ireland"** (Geofabrik's name), so the picker says plainly that Northern Ireland is included.
If setup groups maps by country, this entry should be findable from both Ireland and the United Kingdom.

**How this differs from PR #84.** #84 already lists an `eu-ie` entry built from the same extract, titled "Ireland" and
boxed by Geofabrik's polygon (-14.4022, 49.6, -5.0593, 56.8655). Its `eu-gb` entry uses Geofabrik's `united-kingdom`
extract, which also covers Northern Ireland. So under #84 Northern Ireland would ship in two regions. This proposal
differs in the name and in the box rule below.

### Box

| What | Box (west, south, east, north) | How | Mark |
|---|---|---|---|
| Republic of Ireland | -10.6909, 51.3887, -5.9945, 55.4503 | Vertex extent of Tailte Éireann "Counties Ungeneralised 2026" (9,261 polygons, 2,030,853 vertices, fetched in WGS 84) | opened, computed |
| Northern Ireland | -8.1775, 54.0227, -5.4328, 55.3130 | Vertex extent of ONS "Countries December 2023 Boundaries UK BFC", Northern Ireland row | opened, computed; licence not read |
| **Island** | **-10.6909, 51.3887, -5.4328, 55.4503** | The two together | computed |
| Island with 0.15° margin | -10.85, 51.23, -5.28, 55.61 | Rounded outward, as REGIONS.md and REGIONS-DE.md do | computed |
| Geofabrik `ireland-and-northern-ireland.poly` | -14.4022, 49.6000, -5.0593, 56.8655 | Bounding box of its 10 vertices | opened |

- The service's own extent answer for the Republic gives a box that is too wide in the west and too short in the north:
  it is the corners of the projected (Irish Transverse Mercator) envelope, not the boundary. The vertex extent is used
  instead.
- ONS's boundary is used only to compute Northern Ireland's east edge, because OSNI's own service did not resolve. Its
  east edge agrees with Burial Island, the island's easternmost point, at about -5.427 in OpenStreetMap.
- Geofabrik's polygon is a coarse hull reaching 49.6° N in the Celtic Sea and 14.4° W in the Atlantic. It is the
  extract's clipping shape, not a box for cutting map layers.

**What the rectangle takes in from Great Britain.** With the margin, the box includes (Natural Earth 1:50m outlines and
OpenStreetMap place positions):

- in Scotland, the south of Kintyre with Campbeltown, Machrihanish and Sanda; the west coast of Arran; and the south tip
  of Islay;
- in Wales, St David's Head, Ramsey Island, Grassholm and most of Skomer.

The Isle of Man and the Rhins of Galloway lie outside. None of these places is inside Geofabrik's Irish extract (its
polygon's east edge is about -5.94 at 55.3° N and -5.72 at 51.9° N), so a map built from it has no detail there. To
keep them, a build would need the United Kingdom extract as well, which a US state's box never needs. The simpler
choice is to accept that the box's corners hold only base-map detail.

## Sources, layer by layer

| Layer (file) | US source today | Proposed for the island | Publisher | Licence | Mark |
|---|---|---|---|---|---|
| Roads, water, land (base map) | OSM extract | `ireland-and-northern-ireland-latest.osm.pbf` (398 MB) or `-latest-free.gpkg.zip` (954 MB) | OSM contributors via Geofabrik | ODbL 1.0 | opened |
| Points of interest (`poi`) | OSM | OSM (counts and gaps under "Help points") | OSM contributors | ODbL 1.0 | opened |
| Places (`places.sqlite`) | GNIS, Census, OSM | OSM named places and townlands (61,097 areas); Logainm (Placenames Database of Ireland) for Irish-language forms; Tailte Éireann townlands and counties; OSNI boundaries | OSM; Logainm; Tailte Éireann; OSNI | ODbL 1.0; CC BY 4.0 (Logainm, see notes); Tailte Éireann terms; UK Open Government Licence (OSNI) | mixed, see notes |
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30 for the whole island; national LiDAR and OSNI's DTM as later upgrades | ESA / Airbus; Geological Survey Ireland; OSNI | Copernicus WorldDEM-30; CC BY 4.0; LPS Open Government Data Licence | see notes |
| Water: lakes, rivers | NHD | OSM for a first build; EPA river waterbodies and Tailte Éireann "Lakes & Reservoirs" (250k) as candidates | EPA; Tailte Éireann | CC BY 4.0 | opened (EPA rivers); search only (lakes) |
| Water: dams, reservoirs | NID | OSM `waterway=dam` and `water=reservoir`. No open dam register found for the Republic (one search, not exhaustive); Northern Ireland's controlled reservoirs register is public but no open download was found | DfI (Northern Ireland) | not found | search only |
| Crops (`crops.sqlite`) | USDA CDL | OSM `landuse=orchard` (746 objects), or no crop layer | OSM | ODbL 1.0 | opened (taginfo) |
| Buildings (`buildings.sqlite`) | Microsoft US footprints | Microsoft Global ML Building Footprints, Overture buildings or OSM | Microsoft; Overture; OSM | CDLA Permissive 2.0; ODbL | opened |
| Addresses | Overture addresses | OSM `addr:*` tags (partial: 492,642 numbered objects) and OSM townlands. Overture's address theme lists 41 countries and neither Ireland nor the United Kingdom is among them | OSM contributors | ODbL 1.0 | opened |

Notes:

- **Related pull requests.** PR #84 lists `eu-ie` (see "Code" above). PR #35 adds a Dublin box cut from the same
  extract. Both use Geofabrik's Irish extract, so the base map needs no new source.
- **Copernicus GLO-30 is a surface model.** It follows hedgerows, forestry and buildings, not bare ground. It is the
  only single island-wide source found. Geological Survey Ireland's open LiDAR (data.gov.ie, CC BY 4.0, 1 to 2 m, DTM and
  DSM, opened) is bare earth but covers only the areas each survey flew, with no national coverage claimed. OSNI publishes
  a 10 m DTM for Northern Ireland "under Open Data" (search only) under the "LPS Open Government Data Licence", whose text
  was not read. EEA's EU-DEM is marked obsolete in favour of Copernicus DEM (search only).
- **Logainm's licence is stated two ways.** Its licence page (docs.gaois.ie, opened) says CC BY 4.0, and data.gov.ie
  agrees (search only). A Linked Logainm page reportedly says ODbL 1.0 (search only). Access is through an API key; no bulk
  file was found. Bulk redistribution in a pack should be confirmed with Logainm before use.
- **Tailte Éireann** says data it releases "will be free to use as long as Tailte Éireann are attributed as the content
  creator" and "A standard Creative Commons licence applies to this data" (tailte.ie open data page, opened). The county
  service names "© Tailte Éireann" (opened). data.gov.ie lists the 2024 county and local authority boundaries as
  CC BY 4.0 (search only).
- **Land cover.** The EPA's Irish CORINE 2018 (CC BY 4.0, opened) covers the Republic only, with a 25 ha minimum unit
  that would miss almost every orchard. The National Land Cover Map 2018 (Tailte Éireann with the EPA, opened) has no
  orchard class and states no licence. With only 746 orchards mapped in OSM, leaving the crops layer out is a reasonable
  first choice.
- **Buildings.** Microsoft's `dataset-links.csv` (2026-08-13, opened) has 56 rows for "Ireland" and 194 for
  "UnitedKingdom". The UnitedKingdom rows include tiles over Belfast and County Down that the Ireland rows lack, so
  Northern Ireland's footprints are filed under the United Kingdom (tile contents not opened). The licence is CDLA
  Permissive 2.0 (opened), not ODbL, which is the question REGIONS.md already raises. No open official building outlines
  were found for either jurisdiction (search only). OSM holds 4,091,466 objects tagged `building` in the extract (taginfo,
  opened); no completeness figure was found.
- **Water registers.** EPA's Water Framework Directive river waterbodies (data.gov.ie, CC BY 4.0, opened) were seen only
  as a web map service, not a download. Uisce Éireann publishes a reservoirs list as XLSX (search only, licence not seen).
  Northern Ireland's register under the Reservoirs Act (Northern Ireland) 2015 is open to public inspection and may hold
  reservoir managers' details (search only); the app would drop any personal names, as REGIONS.md does for BC's dams.

## Help points

OSM is the practical source for help points on both sides of the border. Counts from taginfo for Geofabrik's extract,
data until 16 November 2026 21:19 UTC (opened):

| Tag | Count | Notes |
|---|---|---|
| `amenity=pharmacy` | 1,745 | |
| `amenity=hospital` | 253 | |
| `amenity=clinic` | 655 | |
| `amenity=doctors` | 789 | |
| `amenity=police` | 536 | |
| `amenity=fire_station` | 295 | |
| `emergency=ambulance_station` | 70 | no class in Geofabrik's free layers |
| `emergency=defibrillator` | 2,816 | no class in Geofabrik's free layers |
| `amenity=drinking_water` | 373 | |
| `natural=spring` | 2,309 | already shown as "Springs (untested water)" |
| `place_of_worship=holy_well` | 826 | no class in Geofabrik's free layers |
| `man_made=water_well` | 661 | not in `POI_KEEP` (`tools/build_map.py`), so not shown today |
| `amenity=shelter` | 2,430 | 1,145 also carry `shelter_type=public_transport`; 337 are `weather_shelter`, 2 `basic_hut` |
| `amenity=fuel` | 2,246 | |
| `shop=supermarket` | 1,664 | |
| `amenity=community_centre` | 2,297 | |

**What the current builder can show.** `tools/build_map.py` takes each point's class from the `fclass` column of
Geofabrik's free GeoPackage. Geofabrik's free layer specification has no class for defibrillators, ambulance stations or
holy wells, and does not carry `shelter_type` (opened, layer specification 0.7.12). Adding those words to `POI_KEEP`
would show nothing. Showing them needs a reader of the full `.osm.pbf`, such as the one PR #63 proposes, and its
bus-shelter filter likewise works only there.

Four kinds of point are worth a decision:

- **Bus shelters.** About half the shelters are bus stops. PR #63 keeps a shelter only when it has no `shelter_type`,
  or when it is a `weather_shelter` or `basic_hut`; the same rule would suit Ireland.
- **Holy wells.** 826 are mapped, and many are springs (general knowledge). If shown, they belong with "Springs
  (untested water)", never with drinking water.
- **Water wells.** 661 are mapped and none is shown today, in Ireland or the US.
- **Defibrillators.** 2,816 mapped AEDs, more than any other help point here.

No official lists of hospitals, Garda or PSNI stations, fire stations or pharmacies were checked; OSM is proposed for all
of them.

## Licence notes and attribution

The island needs two sets of credits, one for each jurisdiction's public data.

- **ODbL** (OpenStreetMap): as for the US map.
- **CC BY 4.0, Irish public bodies.** Geological Survey Ireland's wording is "Contains Irish Public Sector Data
  (Geological Survey Ireland) licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) licence"
  (search only). The EPA and Tailte Éireann would take the same form with their own names.
- **Logainm.** "Irish-language placename data by Logainm © Government of Ireland and licensed under CC BY 4.0" (opened).
- **OSNI and Land & Property Services.** OSNI's boundaries on data.gov.uk (opened) require "Contains LPS Intellectual
  Property © Crown copyright and database right (year). This information is licensed under the terms of the Open
  Government Licence", version 3. The DTM names the "LPS Open Government Data Licence", whose text was not read; whether
  it equals OGL v3 should be confirmed.
- **Copernicus WorldDEM-30** and **CDLA Permissive 2.0** (Microsoft): as in REGIONS.md.

The default licence pages of data.gov.ie (HTTP 404) and OpenDataNI (HTTP 500) could not be opened, so their standard
attribution statements are not quoted here.

## How addresses are written

- **Republic.** Every address has an **Eircode**: seven characters, a three-character routing key and a four-character
  unique identifier, written "A65 F4E2", across 139 routing areas (eircode.ie, opened). Many rural addresses have no
  street number and name a townland instead (general knowledge; needs a local reader's review). In towns the order is
  number, street, town, as in the US.
- **Northern Ireland.** UK postcodes, all starting `BT` (general knowledge), with number-first street addresses.
- **OpenStreetMap is the one open source.** It carries addresses as `addr:*` tags under the ODbL, the same licence as
  the rest of the map; Nominatim, OSM's own geocoder, searches them. Counts for the extract (taginfo, opened):

  | Tag | Objects | Notes |
  |---|---|---|
  | `addr:housenumber` | 492,642 | 469,312 of them are buildings (ways) |
  | `addr:street` | 771,886 | about 280,000 more than have a number: a street with no house number |
  | `addr:housename` | 26,157 | |
  | `addr:city` | 230,858 | |
  | `addr:postcode` | 29,493 | |
  | `locality=townland` | 61,097 areas | townlands, tagged `boundary=administrative`, `admin_level=10`, `place=locality` (OSM wiki "Ireland/Boundaries", opened) |

  - **Coverage is partial.** The island has roughly 2.9 million homes (general knowledge, from the two censuses; not
    checked), so numbered OSM addresses cover very roughly one in six. This is an estimate, not a measurement: an object
    can hold several homes, and where the numbered addresses lie (towns or countryside) was not measured.
  - **Townlands are widely mapped.** 61,097 townlands are mapped as areas (taginfo, opened); how many the island has was
    not checked. A rural address that names a townland instead of a number can be found as a place ("Townland, County") even where no
    address point exists.
- **No other open source was found:**
  - Overture has no Irish or UK addresses (opened, 41 countries listed).
  - The Eircode database is "available through a licence agreement" (eircode.ie, opened); no open licence was found.
  - OSNI's Pointer address database appears to be a paid, annually licensed product (search only).
  - Ordnance Survey's Code-Point Open covers "all the current postcode units in Great Britain"; Northern Ireland
    appears only in the paid Code-Point product (opened).
  - ONS's postcode products say postcodes starting "BT" "need a separate licence for commercial use direct from Land and
    Property Services" (ONS licences page, opened).
- **What the current code does with that** (read in this repository on 17 November 2026):
  - `tools/build_addresses.py` keeps only rows where `country = 'US'`, cuts the region to two letters
    (`state.upper()[:2]`), and keeps `left(postcode, 5)`, which would cut "A65 F4E2" to "A65 F" and "BT1 5GS" to "BT1 5".
  - `engine/address_search.py` reads a postcode only as five digits, and `normalize()` turns every letter outside a-z into
    a space, so "Sráid" becomes "sr id". REGIONS-DE.md records the same for umlauts.
  - `is_address_query()` treats "a number followed by words" as an address. That fits town addresses but not a townland
    address with no number.
  - The place finder holds US ZIP code areas (`tools/build_places.py`); it would have no Eircode or `BT` postcode lookup
    either.

The proposal has two steps:

1. **Townlands in the place finder.** Add the island's townlands, with their county, to `places.sqlite` from OSM. This
   finds the commonest rural address form with no change to address search.
2. **Street addresses from OSM.** Build the address index from OSM's `addr:*` tags instead of Overture. That needs a
   second input for `tools/build_addresses.py` (it reads only Overture today) and the code changes listed above. The
   map's description should say that address search covers only the addresses mapped in OpenStreetMap, as the
   maintainers asked in #23 ("clearly distinguish map detail from street-address search").

If the maintainers would rather ship the map first, it can go without address search and say so; a licensed Eircode
lookup is outside what a free offline pack can carry.

## Still undecided

1. **Code and name in setup.** `IE`, `eu-ie` or another scheme; how one entry that spans two countries appears in a
   country-grouped picker; and whether Northern Ireland should also ship in a United Kingdom region, as #84's `eu-gb`
   would make it.
2. **The box rule.** Keep the box's strips of Scotland and Wales as base-map-only corners, add the United Kingdom
   extract for them, or clip to the island.
3. **Terrain.** One surface model (GLO-30) for the whole island, or bare-earth LiDAR and OSNI's DTM where they exist.
4. **Address search.** Whether the first build carries OSM addresses (partial coverage, said plainly) and townlands in
   the place finder, or ships the map alone first. Also whether an OSM address index would serve other countries
   Overture does not cover, such as Sri Lanka (REGIONS-LK.md).
5. **Irish-language names.** 123,698 objects carry `name:ga` (taginfo, opened), and OSM's Irish guidance puts the Irish
   name there (OSM wiki "Ireland/Gaelic", opened). Placenames orders under the Official Languages Act 2003 make the Irish
   forms official where an order exists (search only); logainm.ie lists the orders made so far, county by county
   (opened). Whether the map shows `name:ga`, and how search folds the síneadh fada (á, é, í, ó, ú), belongs with #3 and
   #54.
6. **New help-point kinds.** Holy wells (as untested water), water wells, defibrillators and ambulance stations, all of
   which need a reader beyond Geofabrik's free layers except water wells.
7. **Crops.** Whether the island gets a crops layer at all.
8. **Boundaries in the loughs.** The United Kingdom and Ireland have no agreed boundary in Lough Foyle or Carlingford
   Lough (general knowledge, not checked). A whole-island region does not need to draw one, but this belongs with the
   disputed boundaries question in REGIONS.md item 6.
9. **The California-only layers.** As REGIONS.md item 7.

## What was checked, and what was not

- Opened: Geofabrik's extract page and polygon; Overture's address documentation (41 countries, release 2026-10-21.0);
  Microsoft's `dataset-links.csv` (2026-08-13); Tailte Éireann's county service (all polygons fetched, vertex extent
  computed) and open data page; ONS's Northern Ireland country boundary (vertex extent computed); data.gov.ie pages for
  GSI LiDAR, Irish CORINE 2018 and EPA river waterbodies; the EPA's National Land Cover Map page; eircode.ie; Ordnance
  Survey's Code-Point Open page; ONS's postcode products and licences pages; the Logainm licence page and orders list;
  OSM wiki "Ireland/Gaelic"; OSNI's country boundary on data.gov.uk; Geofabrik's free layer specification; taginfo for the
  extract; PR #84's diff.
- Search only: OSNI 10 m DTM and its licence; Copernicus GLO-30 licence (the PDF did not render); EU-DEM status;
  Tailte Éireann 250k lakes and reservoirs; Uisce Éireann reservoirs; Northern Ireland's controlled reservoirs register;
  Pointer's licensing; placenames orders' legal effect; GSI's attribution wording.
- Not opened: data.gov.ie and OpenDataNI licence pages (HTTP 404 and 500); OpenDataNI DTM pages (HTTP 500 and 403);
  OSNI's map service (did not resolve); the ONS boundary's licence; DAERA water and land data; floodinfo.ie's open data
  portal; official help-point lists.
- Not computed: sizes of a built map set, OSM address completeness, Microsoft tile contents.
