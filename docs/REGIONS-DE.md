# Detailed maps for Germany: a proposal

This is a proposal for discussion, not a decision. It answers, for Germany, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) and
[REGIONS-AR.md](REGIONS-AR.md) and is meant to feed the same design discussion (issues #23, #25 and #31). The
machine-readable version is [regions-de-proposed.json](regions-de-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026, with AI research agents reading the publishers' own
pages and a person reviewing the result. Each source carries one of three marks:

- **opened**: the dataset or licence page itself was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

Several state portals are JavaScript applications, one sits behind a CAPTCHA, and one refused the certificate, so a fair
number of rows are "search only". They need a second look before anything is built on them.

## Why Germany is a good second case

Germany has no single federal list for most layers. Surveying belongs to the 16 states (Länder), and the federal agency
(BKG) gives its nationwide combinations of their data only to public bodies or under a paid licence. But most states now publish their own elevation models,
building outlines and address points as open data, and Overture already carries addresses from 15 of the 16 states. So
the question for Germany is less "is there an open source" and more "which of 16 sources, under which of four licences".

## What a region is

Germany has 16 states, three of which are city-states (Berlin, Hamburg, Bremen). The proposal is one region per state,
16 in all, the same level as a US state.

### Codes

ISO 3166-2:DE gives each state two letters after `DE-`: `DE-BY` Bavaria, `DE-NW` North Rhine-Westphalia, `DE-BE` Berlin,
and so on (not checked against the ISO site, as REGIONS.md and REGIONS-AR.md also note for their codes).

- A hyphenated code is needed: a bare `DE` already means **Delaware** in `STATE_CODES` (`engine/address_search.py`) and
  would collide with `Lastbook-Map-DE.zip` and `derived/geo/addresses/DE.sqlite`.
- None of the 16 two-letter state parts (`BW`, `BY`, `BE` and so on) is one of the 52 entries in `STATE_CODES`, so the
  part after the hyphen is unambiguous on its own; the country part is not.

### City-states

- **Berlin inside Brandenburg, Bremen inside Lower Saxony.** Berlin is an enclave in Brandenburg, and both parts of
  Bremen (Bremen and Bremerhaven) lie inside Lower Saxony. The `DE-BB` box already contains the whole `DE-BE` box, and
  the `DE-NI` box already contains the whole `DE-HB` box. Because a state map holds every row inside its box, a
  Brandenburg map would show Berlin's streets and help points without any extra rule. Address search is different: it
  reads one index per state, so a `DE-BB` map would find Berlin streets on the map but not Berlin addresses unless the
  index is cut by box, not by state. That is a decision for the maintainers.
- **Hamburg** sits between Schleswig-Holstein and Lower Saxony. Its box reaches west to the island of Neuwerk (8.42° E),
  and with the margin it lies wholly inside the `DE-SH` box.

### Boxes

The boxes were computed from BKG's **Verwaltungsgebiete 1:250 000 (VG250)**, state layer `VG250_LAN`, as of
1 January 2026 (file `vg250_01-01.utm32s.shape.ebenen.zip`, MD5 checked against BKG's published sum). Only land areas
were used (`GF = 4`, "land with structure"), which leaves out the coastal waters of the North Sea and the Baltic and the
two "Bodensee" polygons. Every vertex was transformed from ETRS89 / UTM 32N (EPSG:25832) to WGS 84 (EPSG:4326) with
pyproj, then each box was widened by 0.15° and rounded outward to 0.01°, the same margin `map_sets.state` uses for US
states.

The two areas with `GF = 3` (tidal flats without municipalities in Schleswig-Holstein and Lower Saxony) lie inside the
land boxes. As a check, the outer edges match Germany's known extreme points: Selfkant in the west (5.87° E), near
Görlitz in the east (15.04° E), List on Sylt in the north (55.06° N) and the Allgäu Alps in the south (47.27° N).

| Code | AGS | Name | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|
| `DE-SH` | 01 | Schleswig-Holstein | 7.8691, 53.3598, 11.3129, 55.0588 | 7.71, 53.20, 11.47, 55.21 |
| `DE-HH` | 02 | Hamburg | 8.4199, 53.3951, 10.3260, 53.9644 | 8.26, 53.24, 10.48, 54.12 |
| `DE-NI` | 03 | Niedersachsen (Lower Saxony) | 6.6393, 51.2952, 11.5981, 53.8923 | 6.48, 51.14, 11.75, 54.05 |
| `DE-HB` | 04 | Bremen | 8.4817, 53.0110, 8.9909, 53.6101 | 8.33, 52.86, 9.15, 53.77 |
| `DE-NW` | 05 | Nordrhein-Westfalen (North Rhine-Westphalia) | 5.8663, 50.3230, 9.4615, 52.5314 | 5.71, 50.17, 9.62, 52.69 |
| `DE-HE` | 06 | Hessen (Hesse) | 7.7725, 49.3954, 10.2360, 51.6575 | 7.62, 49.24, 10.39, 51.81 |
| `DE-RP` | 07 | Rheinland-Pfalz (Rhineland-Palatinate) | 6.1124, 48.9666, 8.5084, 50.9423 | 5.96, 48.81, 8.66, 51.10 |
| `DE-BW` | 08 | Baden-Württemberg | 7.5119, 47.5324, 10.4957, 49.7915 | 7.36, 47.38, 10.65, 49.95 |
| `DE-BY` | 09 | Bayern (Bavaria) | 8.9759, 47.2701, 13.8396, 50.5642 | 8.82, 47.12, 13.99, 50.72 |
| `DE-SL` | 10 | Saarland | 6.3569, 49.1119, 7.4038, 49.6394 | 6.20, 48.96, 7.56, 49.79 |
| `DE-BE` | 11 | Berlin | 13.0883, 52.3382, 13.7605, 52.6754 | 12.93, 52.18, 13.92, 52.83 |
| `DE-BB` | 12 | Brandenburg | 11.2657, 51.3590, 14.7657, 53.5587 | 11.11, 51.20, 14.92, 53.71 |
| `DE-MV` | 13 | Mecklenburg-Vorpommern | 10.5937, 53.1103, 14.4124, 54.6850 | 10.44, 52.96, 14.57, 54.84 |
| `DE-SN` | 14 | Sachsen (Saxony) | 11.8715, 50.1715, 15.0418, 51.6850 | 11.72, 50.02, 15.20, 51.84 |
| `DE-ST` | 15 | Sachsen-Anhalt (Saxony-Anhalt) | 10.5612, 50.9380, 13.1871, 53.0418 | 10.41, 50.78, 13.34, 53.20 |
| `DE-TH` | 16 | Thüringen (Thuringia) | 9.8770, 50.2048, 12.6541, 51.6490 | 9.72, 50.05, 12.81, 51.80 |

AGS is the official state key (Amtlicher Gemeindeschlüssel, first two digits), as in VG250's `SN_L` field.

## Sources, layer by layer

### Nationwide

| Layer (file) | US source today | Proposed for Germany | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP, 1 arc-second | Each state's open DGM1, resampled to the size the app uses today (see the state table); Copernicus DEM GLO-30 where a state has no usable bulk download | the states; ESA / Airbus | see the state table; Copernicus licence as in REGIONS.md | see below |
| Terrain, coarse national | | BKG DGM200 (200 m, GeoTIFF, about 36 MB) | BKG | dl-de/by-2-0 | opened |
| Water (`water.sqlite`) | NHD | OSM waterways and water areas (Geofabrik's Germany extract); BKG DLM250 water features as a cross-check | OSM contributors; BKG | ODbL; dl-de/by-2-0 | Geofabrik opened; DLM250 opened, its water layer names not confirmed |
| Dams | NID | OSM `waterway=dam` and reservoir areas; no open German dam inventory found | OSM contributors | ODbL | tag wiki opened |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | Thünen-Institut "Agricultural land use" raster 2024; CORINE Land Cover 5 ha 2018 (CLC5) from BKG as fallback | Thünen-Institut; BKG | CC BY 4.0; dl-de/by-2-0 | both opened; classes not confirmed (see notes) |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | OSM buildings or Overture buildings; the states' open building outlines (Hausumringe) where a state publishes them in bulk | OSM contributors; Overture; the states | ODbL; see the state table | Overture attribution opened |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | BKG GN250 (about 170,000 names); VG250 municipalities; GeoNames postcode points (`DE.zip`); OSM named places | BKG; GeoNames; OSM contributors | dl-de/by-2-0; CC BY 4.0; ODbL | GN250 and VG250 opened; GeoNames search only (linked from suche-postleitzahl.org, file not opened) |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **Overture addresses, which already hold 15 of the 16 states** (all but Bavaria); OSM `addr:*` for Bavaria | Overture Maps Foundation, from the states through OpenAddresses | per state, see the state table | opened |
| Points of interest (`poi` rows) | OSM | OSM, as today | OSM contributors | ODbL | taginfo counts read |

What is not open nationwide, and so not proposed: BKG's DGM25, DGM5 and DGM1 (public bodies only, or a licence fee),
the nationwide house outlines HU-DE, the 3D building models LoD1-DE and LoD2-DE, and the nationwide house coordinates
HK-DE and address data GA. All of these were opened on BKG's product pages, which say they go to a restricted group of
users. Search results from BKG's pages mention a new AdV fee directive (AdV-GR 4.1) in force from 1 January 2027 that may
open nationwide products for wider use; the directive itself was not read, and which products it covers is not
confirmed.

### State by state

These are the states' own open datasets. "Overture" is the licence Overture's attribution page gives for that state's
address source (opened, accessed by Overture 15 October 2026).

| Code | Elevation | Building outlines | Addresses | Licence | Bulk download | Overture | Checked |
|---|---|---|---|---|---|---|---|
| `DE-BW` | DGM1 | Hausumringe, LoD1, LoD2 | Hauskoordinaten, without postal data | dl-de/by-2-0 for all open geodata | portal is a JavaScript app; per-area ZIPs, bulk not confirmed | dl-de/by-2-0 | LGL page and product list opened |
| `DE-BY` | DGM1 | Hausumringe, LoD2 | Hauskoordinaten **still paid** (FAQ) | CC BY 4.0 | yes, Metalink by polygon or municipality | **not listed** | FAQ and terms opened; DGM1 resolution search only |
| `DE-BE` | DGM1 (2 km sheets) | INSPIRE buildings, LoD2 | INSPIRE addresses | dl-de/zero-2.0 | yes, Atom feeds | dl-de/zero-2.0 | opened |
| `DE-BB` | DGM1 | Hausumringe (statewide shapefile) | Georeferenzierte Adresse | dl-de/by-2-0 | yes, through GEOBROKER; registration not confirmed | dl-de/by-2-0 | product pages opened |
| `DE-HB` | DGM1, DGM5 | Hausumringe, LoD1, LoD2 | Hauskoordinaten, without postcode | CC BY 4.0, **in conflict** (see notes) | through MetaVer, format not confirmed | CC BY 4.0 | letter and product pages opened |
| `DE-HH` | DGM1 (whole-city ZIPs) | LoD2, ALKIS "selected data" including buildings | only a 2014/15 archive as a plain download | dl-de/by-2-0 | yes | dl-de/by-2-0 | opened |
| `DE-HE` | DGM1 (GeoTIFF) | LoD2; Hausumringe not found | Hauskoordinaten | "free of cost and licence" on the shop page; no named licence opened | self-service download centre; registration may be needed | dl-de/zero-2.0 | product sheets opened; Hauskoordinaten search only |
| `DE-MV` | DGM1 (2 km tiles) | Hausumringe, ALKIS stock, LoD2 | contradictory | CC BY 4.0 (press release of 18 Feb 2026 for buildings) | yes, Atom and a state ZIP | CC BY 4.0 | buildings opened; DGM licence and LoD2 search only |
| `DE-NI` | DGM1 | Hausumringe, LoD1, LoD2 | Hauskoordinaten, openness not confirmed | CC BY 4.0 since 9 June 2024 | bulk tool with GeoPackage per district | CC BY 4.0 | licence opened (LGLN presentation); portals are JavaScript apps |
| `DE-NW` | DGM1 (GeoTIFF tiles with `index.json`) | simplified ground plans (GeoPackage, 53 ZIPs, about 7.1 GB), LoD1, LoD2 | building reference `gebref` (one ZIP, 92.5 MB) | dl-de/zero-2.0 | yes, plain file directories | dl-de/zero-2.0 | opened; LoD licence not read |
| `DE-RP` | DGM1 | Hausumringe, 3D model | building reference | dl-de/by-2-0 in metadata; the site also names CC BY-SA 4.0 | **no**, shop and viewer only | dl-de/by-2-0 | pages opened; licence search only |
| `DE-SL` | DGM1; DGM5 paid | Hausumringe as WFS only; LoD2 restricted | Hauskoordinaten as WFS | dl-de/by-2-0 | **no**, services only | dl-de/by-2-0 | search only |
| `DE-SN` | DGM1 | Hausumringe | Hauskoordinaten (CSV, about 20 MB, quarterly) | dl-de/by-2-0 | yes | dl-de/by-2-0 | Hauskoordinaten page opened (no licence on it); rest search only |
| `DE-ST` | DGM1 | Hausumringe, LoD1, LoD2 | Hauskoordinaten as WMS only | dl-de/by-2-0 | yes for elevation and buildings | dl-de/by-2-0 | terms (v5.0, 1 March 2024) opened; products search only |
| `DE-SH` | DGM1, DGM2 | Hausumringe, LoD1, LoD2 | Hauskoordinaten | CC BY 4.0 | download portal refused its certificate | CC BY 4.0 | licence page and product list opened |
| `DE-TH` | DGM1 | Hausumringe, LoD1, LoD2 | Hauskoordinaten without postal data | dl-de/by-2-0 | yes, per a 2022 TLBG talk | dl-de/by-2-0 | talk opened; geoportal behind a CAPTCHA, not read |

Notes:

- **Terrain.** The US map uses USGS 3DEP at 1 arc-second, about 30 m. Copernicus GLO-30 matches that size and covers all
  of Germany in one source, but it is a surface model: in forest and towns, contours follow the canopy and the roofs. The
  states' DGM1 models are bare-earth models from airborne laser scanning; resampled to 30 m they give the ground itself,
  at the cost of 16 different downloads and licences. Rhineland-Palatinate and Saarland offer no bulk download of DGM1,
  so GLO-30 would fill those two. Whether GLO-30's Germany tiles are complete was not checked.
- **Crops.** `tools/build_crops.py` keeps orchards, vineyards and berries. The Thünen raster's class list is in legend
  files that were not read, and its Zenodo record says the data URL is "available on request", which may rule out a
  repeatable build. CLC5 follows the CORINE nomenclature, which in general has "vineyards" and "fruit trees and berry
  plantations"; that was not confirmed in BKG's documentation. JRC's EUCROPMAP was looked at and is not proposed: it
  puts permanent crops into woodland and shrubland.
- **Buildings.** OSM building coverage in Germany is dense, and Overture's buildings theme blends OSM with Microsoft and
  others under the ODbL. Microsoft's own repository says CDLA Permissive 2.0 while Overture lists it under the ODbL; that
  is the same question REGIONS.md raises for Guyana. How much Microsoft data covers Germany was not measured.
- **Addresses.** This is where Germany is closest to the US: `tools/build_addresses.py` already reads Overture, and
  Overture's guide gives about 19.3 million German addresses with "partial coverage". Bavaria is missing because its house
  coordinates are still sold, not published. For Bavaria, OSM `addr:*` is the only open source found; the last published
  completeness figure is from 2014 (about 74 %), so coverage would have to be measured from the extract.
- **Hamburg's elevation dataset** on the transparency portal carries a notice that it will be deleted and moved to a
  MetaVer record ("Geländemodelle Hamburg - DGM").

## Help points

OSM is the practical source for help points across Germany: no national open list with coordinates was found for
hospitals, pharmacies, fire stations, police or the federal relief agency (THW). Counts from taginfo for Geofabrik's
Germany extract, data until 16 November 2026 21:22 UTC (opened):

| Tag | Count | Notes |
|---|---|---|
| `amenity=pharmacy` | 17,141 | |
| `amenity=fire_station` | 29,226 | inflated: many stations are drawn as building and node; needs deduplication |
| `amenity=police` | 3,895 | |
| `amenity=hospital` | 2,347 | |
| `amenity=drinking_water` | 9,160 | |
| `man_made=water_well` | 15,967 | |
| `emergency=water_tank` | 7,887 | firefighting water, not drinking water |
| `emergency=drinking_water` | 1,952 | emergency wells; an Overpass count at 2026-11-17 07:47 UTC gave the same number |

Three German kinds of point are worth a decision:

- **Emergency drinking water wells (Trinkwassernotbrunnen).** Germany keeps hand-pump wells under the Water Security Act
  for when the mains fail. No national list is published; search results from Berlin's parliament say the federal
  agency (BBK) does not allow the federal wells to be published (search only). In OSM they are tagged
  `emergency=drinking_water` with `man_made=water_well`, `water_well=pump` and `pump=manual` (OSM wiki, opened). Most of
  the 1,952 are in Berlin, so this would be a Berlin-heavy layer, not national coverage. It fits Lastbook's purpose
  better than almost any other layer, and the map should say plainly where it has no data.
- **Emergency information points ("Katastrophenschutz-Leuchttürme", "Notfall-Treffpunkte").** Berlin, Stuttgart and
  Nuremberg publish the places where people can get help and report emergencies during a long power cut. Each is a web
  map or a PDF, with no licence stated (opened), and the sites open only in a crisis. They would need each city's
  permission before use.
- **Public shelters.** Not proposed. No list of locations is published; the federal shelter concept has been a draft
  since 2024, and municipalities were asked to identify shelters during 2026 (Correctiv, 13 May 2026, opened).

The national hospital register from the statistical offices (Krankenhausverzeichnis, as of 31 December 2024) can be
downloaded as XLSX and reused with a source note (opened), but it has no coordinates; it could cross-check OSM's
hospitals, not replace them.

## Licence notes and attribution

All proposed licences allow redistribution in a free offline library, including commercial reuse. What each asks:

- **Datenlizenz Deutschland - Namensnennung - 2.0 (dl-de/by-2-0).** Name the provider, add a note if the data was
  changed, and link the licence. BKG's terms for VG250 (opened, document of 19 August 2025) ask for "© BKG (year of last
  download) dl-de/by-2-0", a link to its list of data sources, and a visible note of changes. The states each give their
  own credit line, for example "© GeoBasis-DE/LGB, dl-de/by-2-0" (Brandenburg), "© GeoBasis-DE / LVermGeo ST"
  (Saxony-Anhalt) and "Datenquelle: LGL, www.lgl-bw.de, dl-de/by-2-0" (Baden-Württemberg).
- **Datenlizenz Deutschland - Zero - 2.0 (dl-de/zero-2.0).** No conditions (Berlin, North Rhine-Westphalia, and Hesse
  per Overture). A credit is still courteous.
- **CC BY 4.0** (Bavaria, Lower Saxony, Mecklenburg-Vorpommern, Schleswig-Holstein, Thünen). Credit, link, note
  changes: for example "© GeoBasis-DE/LVermGeo SH/CC-BY 4.0" and "Bayerische Vermessungsverwaltung -
  www.geodaten.bayern.de".
- **ODbL** (OSM, Overture buildings). As for the US map.
- **Overture addresses.** Overture asks for "Overture Maps Foundation, overturemaps.org" and the credit of each source,
  here the 15 states above.

Two licences need a closer look before anything is built:

- **Bremen.** A decree of 22 May 2024 (opened) puts Bremen's open geodata under CC BY 4.0, but the footer of
  geo.bremen.de puts the site's content under a non-commercial, no-derivatives Creative Commons licence "unless otherwise
  stated". The decree is the more specific text; it should be confirmed with Bremen's geodata service.
- **Rhineland-Palatinate** names both dl-de/by-2-0 and CC BY-SA 4.0 for its open data without saying which applies
  where. Share-alike would add a condition the other states do not have.

These notices would belong wherever the map already credits its sources, and in `THIRD_PARTY_NOTICES.md` if that is
where the maintainers keep data licences.

## How addresses are written

- **Order.** Street, then house number, then postcode and town: "Hauptstraße 5, 10115 Berlin". The number comes after
  the street, and the postcode before the town. House numbers often carry a letter or a range ("12a", "12-14").
- **Postcode.** Five digits, the same shape as a US ZIP code. Leading zeros are common (Saxony and Thuringia start at
  `01`), so a postcode must stay text.
- **Street words.** Street names are mostly single compound words ending in *-straße* (often written *-str.*), *-weg*,
  *-platz*, *-allee*, *-gasse* or *-damm*; "Straße" is also written as a separate word ("Berliner Straße"). *ß* is often
  typed as *ss*, and umlauts as *ae*, *oe*, *ue* when a keyboard lacks them.
- **What the current code does with that** (read in this repository and tried on examples on 17 November 2026):
  - `normalize()` in `engine/address_search.py` and `norm()` in `tools/build_addresses.py` keep only `a-z` and `0-9`,
    so "Müllerstraße" becomes `m llerstra e`. Umlauts and *ß* need folding (ü to u or ue, ß to ss) on both sides, and
    "str." needs to match "straße".
  - `is_address_query()` needs a number first, so "Hauptstraße 5, 10115 Berlin" is not treated as an address.
  - `_parts()` takes a postcode only as the last word, while German addresses put the town after it.
  - `tools/build_addresses.py` keeps only `country = 'US'` and the first two letters of the region, so `DE-BY` would
    become `DE`. How Overture fills the region field for German rows was not checked.
  - The five-digit postcode rule itself fits Germany unchanged.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md and
REGIONS-AR.md.

1. **Codes in setup.** Whether `DE-BY` and the others are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup groups 16 German regions.
2. **The box rule**, as in REGIONS.md, here from VG250 land areas.
3. **City-states.** Whether the Brandenburg and Lower Saxony maps should also carry Berlin's and Bremen's addresses.
4. **Terrain.** Sixteen bare-earth state models, or one surface model (GLO-30) for all.
5. **Bavaria's addresses**, with no open official source.
6. **New help-point kinds**: emergency wells, and whether hand-collected city lists of emergency information points are
   worth the permissions they need.
7. **Lake Constance (Bodensee).** VG250 keeps the lake as separate "Bodensee" polygons for Baden-Württemberg and Bavaria
   because Germany, Austria and Switzerland have never agreed a border on the lake. This belongs with the disputed
   boundaries question in REGIONS.md.

## What was checked, and what was not

- Opened on 17 November 2026: BKG's product pages for DGM200, DGM1000, DGM25, DGM5, DGM1, DLM250, CLC5 2018, GN250,
  VG250, HU-DE and HK-DE; BKG's VG250 terms (PDF in the download); Overture's attribution page and address guide; the
  Thünen raster's Zenodo record; Geofabrik's Germany page; the LGL open data page and product list; Bavaria's open data
  FAQ and terms; Berlin's GDI records and Atom feeds; Brandenburg's product pages; Bremen's decree and product pages;
  Hamburg's transparency portal records; Hesse's product sheets; Mecklenburg-Vorpommern's buildings page and press
  release; Lower Saxony's presentation on free products; North Rhine-Westphalia's open data directories; Saxony's house
  coordinates page; Saxony-Anhalt's terms; Schleswig-Holstein's licence page; a 2022 Thuringia talk; the OSM wiki on
  emergency wells; taginfo for the counts above; Berlin's, Stuttgart's and Nuremberg's pages on emergency points; the
  statistical offices' hospital register page; Correctiv's article on shelters.
- Computed on 17 November 2026: the 16 boxes, from VG250 as described above.
- Seen only in search results: the licences for Saarland, Saxony's elevation and buildings, Thuringia,
  Rhineland-Palatinate's metadata and Mecklenburg-Vorpommern's elevation; Hesse's house coordinates; the AdV-GR 4.1 directive; the
  BBK position on publishing emergency wells; GeoNames' licence.
- Not checked: the Thünen legend files and CLC5 documentation (crop classes), DLM250's water layer names, GLO-30
  completeness for Germany, the Copernicus licence text (see REGIONS.md), Schleswig-Holstein's download portal
  (certificate error), Thuringia's geoportal (CAPTCHA), the licence of North Rhine-Westphalia's LoD folders, current OSM
  address coverage, and the ISO 3166-2:DE codes against the ISO site.
