# Detailed maps for Manitoba: a proposal

This is a proposal for discussion, not a decision. It answers, for Manitoba, the questions [MAPS.md](MAPS.md) asks before coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a “state” is there, and how addresses are written. Manitoba is a Canadian province.

Nothing here changes the app, the engine or a build. A machine-readable version could live alongside [regions-proposed.json](regions-proposed.json). No code reads it, and it does not ship: builds package `web/` and `content/` only. Everything below was checked on 17 November 2026 by opening the page named or computing from the published boundary. Where something could not be checked, it says so. It should wait for the maintainers’ design issue before any code follows it.

## What a region is

A US state map is cut by `packaging/build_packs.py map <ST>` from the base map plus every row inside the state’s box (`derived/packs/pack-spec.json`, `map_sets.state`). The box comes from ZIP code (ZCTA) centroids, plus or minus 0.15 degrees. There are no ZCTAs outside the US, so the proposal takes the box from an official boundary instead, and keeps the same 0.15 degree margin.

| Code | Name | Country | Level | Box (west, south, east, north) | Box with 0.15° margin | Box taken from |
|---|---|---|---|---|---|---|
| `CA-MB` | Manitoba | Canada | province | -102.0080, 48.9988, -88.9919, 59.9995 | -102.16, 48.84, -88.84, 60.15 | Government of Manitoba, Manitoba Provincial Boundary (OpenMB Information and Data Use License) |

- The box was computed from the GeoJSON published by the Government of Manitoba (item `ed39fb5989bc41bcb4b102f8ea899abf` on geoportal.gov.mb.ca: [dataset page](https://geoportal.gov.mb.ca/datasets/ed39fb5989bc41bcb4b102f8ea899abf), [feature service](https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Provincial_Boundary/FeatureServer)), reprojected from Web Mercator to WGS84. The north edge follows the Hudson Bay shoreline as drawn in that dataset (generalized from 1:500 000 mapping; estimated accuracy ±125 m). The south edge is the international boundary with the United States.

### Codes

US state maps use two-letter codes, and `CA` already means California: in `STATE_CODES` in `engine/address_search.py`, in `NAMES` in `packaging/state_maps.py`, in `Lastbook-Map-CA.zip` and in `derived/geo/addresses/CA.sqlite`. A bare `MB` does not collide with any US code, but the proposal uses the ISO 3166-2 style code `CA-MB` for consistency with the codes already proposed for Ontario (`CA-ON`) and British Columbia (`CA-BC`). The hyphen keeps it apart from US codes at a glance.

## Sources, layer by layer

Each map file a state map holds needs a replacement for its US source. “OGL” is an Open Government Licence. “OpenMB” is the OpenMB Information and Data Use License of the Government of Manitoba.

### Manitoba

| Layer (file) | US source today | Proposed for Manitoba | Publisher | Licence |
|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | Medium Resolution DEM (MRDEM), 30 m; High Resolution DEM (HRDEM) where lidar exists | Natural Resources Canada | OGL – Canada |
| Water (`water.sqlite`) | NHD, NID | National Hydro Network (NHN); Manitoba Provincial Waterways (dams, diversions, detention basins, floodways, reservoirs) where available | Natural Resources Canada; Government of Manitoba | OGL – Canada; OpenMB |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | Annual Crop Inventory, 30 m | Agriculture and Agri-Food Canada | OGL – Canada |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Open Database of Buildings; Microsoft Canadian Building Footprints to fill gaps; OSM heights | Statistics Canada; Microsoft; OSM contributors | OGL – Canada; ODbL; ODbL |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | Canadian Geographical Names (CGN); census boundary files; OSM named places | Natural Resources Canada; Statistics Canada; OSM contributors | OGL – Canada; OGL – Canada; ODbL |
| Addresses (`addresses/CA-MB.sqlite`) | Overture addresses | Overture addresses (including Statistics Canada’s National Address Register); the Open Database of Addresses as an alternative | Overture Maps Foundation / Statistics Canada | Statistics Canada Open Licence; OGL – Canada |
| Points of interest (`poi` rows) | OSM | OSM; Open Database of Healthcare Facilities; Open Database of Educational Facilities | OSM contributors; Statistics Canada | ODbL; OGL – Canada |

Notes:

- MRDEM replaces the Canadian Digital Elevation Model (CDEM), which Natural Resources Canada says is no longer supported. The same source is proposed for Ontario and British Columbia.
- Manitoba Provincial Waterways covers designated dams, diversions, detention basins, floodways and reservoirs under OpenMB. The National Hydro Network remains the national fallback, as for the other Canadian provinces.
- The Annual Crop Inventory has its own class list. `tools/build_crops.py` keeps orchards, vineyards and berries from the Cropland Data Layer, so it would need a mapping from one list to the other (same issue as for Ontario and British Columbia).
- Microsoft’s Canadian footprints repository was archived on 8 October 2026. The data is still there; it will not be updated.
- `tools/build_addresses.py` already reads Overture’s address theme. For Manitoba it would need the Canadian country filter and postcode/province handling described under “Still undecided”.
- No Manitoba-only address geocoder that publishes a downloadable file was found; Overture + the Open Database of Addresses are the proposed offline sources.

## Licence notes and attribution

All the proposed licences allow redistribution, including in a free offline library. What each asks in return:

- **OGL – Canada** ([licence](https://open.canada.ca/en/open-government-licence-canada)). Give the provider’s attribution statement and, where possible, link the licence. Where several providers make that impractical, the licence gives a fixed sentence, such as “Contains information licensed under the Open Government Licence – Canada.”
- **OpenMB Information and Data Use License** ([licence](https://www.gov.mb.ca/asset_library/en/legal/OpenMB-Information-Data-Use-Licence.pdf); [explanation](https://www.gov.mb.ca/legal/copyright.html)). The boundary dataset's own page labels its licence “Manitoba Open Data Licence” and links to that explanation. The example attribution published there is “Contains information from the Manitoba government, licensed under the OpenMB Information and Data Use Licence (Manitoba.ca/OpenMB)”, with a link to [Manitoba.ca/OpenMB](https://www.manitoba.ca/OpenMB) where possible.
- **Statistics Canada Open Licence** ([licence](https://www.statcan.gc.ca/en/terms-conditions/open-licence)). For adapted data: “Adapted from Statistics Canada, *product*, *reference date*. This does not constitute an endorsement by Statistics Canada of this product.”
- **ODbL** (OpenStreetMap, Microsoft’s Canadian footprints, Overture buildings). Credit “© OpenStreetMap contributors”, say the data is under the ODbL, and offer a database built from it under the ODbL too. The US map already carries ODbL data, so this is not new.

These notices would belong wherever the map already credits its sources, and in `THIRD_PARTY_NOTICES.md` if that is where the maintainers keep data licences.

## How addresses are written

- **Canada (Manitoba).** A civic number and street, then the municipality, the province abbreviation and the postal code on the last line. The postal code has six characters in the form `A1A 1A1`: letter, digit, letter, a space, digit, letter, digit, in capitals with no hyphen. Manitoba codes begin with R (Canada Post). French street types such as *rue* and *chemin* also occur, though less frequently than in Quebec or parts of Ontario.

## Still undecided

Each of these needs the maintainers’ decision before any code changes (the same list as in the Ontario / British Columbia / Guyana proposal):

1. **Codes and names in setup.** How setup’s map picker lists places that are not US states: one list or grouped by country, and whether a hyphenated code is acceptable as a manifest `id`, as `map-set.json`’s `name`, in `state.current.map` and in the zip name `Lastbook-Map-<id>.zip`.
2. **The box rule.** Whether a box from an official boundary may stand in for ZCTA centroids, and whether 0.15 degrees is still the right margin.
3. **Address search.** `engine/address_search.py` knows US state names and codes only, reads a postcode only as five digits, and picks index files by a two-letter stem. `tools/build_addresses.py` keeps only `country = 'US'`, cuts postcodes to five characters (a Canadian `R3C 0P7` would become `R3C 0`) and keeps two letters of the region. Each would need a change for Canadian addresses, and the street words would need French forms.
4. **Crop classes.** Which Annual Crop Inventory classes map to the orchard, vineyard and berry kinds.
5. **Licences in the app.** Where the extra attribution sentences are shown.
6. **Boundaries in dispute.** Whether Lastbook says anything on the map where a boundary is claimed by a neighbour. (Manitoba’s boundaries are not disputed.)
7. **The California-only layers.** The fish, boating and well layers are labelled California in `web/map.js`; they would stay empty outside it.

## What was checked

- The Manitoba Provincial Boundary GeoJSON was downloaded from the Government of Manitoba geoportal and the bounding box computed in WGS84 on 17 November 2026.
- Licence pages for OpenMB, OGL – Canada, Statistics Canada, and the national datasets already cited in the Ontario/British Columbia proposal were confirmed consistent.
- Rechecked for the maintainers' follow-up on 18 November 2026: the boundary feature service's extent in WGS84 (-102.0080, 48.9988, -88.9919, 59.9995, the box above); the dataset item's licence link; the OpenMB, OGL – Canada and Statistics Canada licence pages linked above; and [Overture's attribution page](https://docs.overturemaps.org/attribution/), which lists Statistics Canada's National Address Register under the Statistics Canada Open Licence among its Canadian address sources, alongside separately attributed Yukon and Quebec sources. The Ontario / British Columbia / Guyana proposal is [REGIONS.md](REGIONS.md).
- Not re-checked on this date: the exact 2021 Statistics Canada boundary files and the full text of every linked licence (they match the checks already recorded for the other Canadian provinces).
