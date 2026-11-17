# Detailed maps for Sri Lanka: a proposal

This is a proposal for discussion, not a decision. It answers, for Sri Lanka, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) and
[REGIONS-AR.md](REGIONS-AR.md) and is meant to feed the same design discussion (issues #23, #25 and #31). The
machine-readable version is [regions-lk-proposed.json](regions-lk-proposed.json); Sinhala and Tamil copies are [REGIONS-LK.si.md](REGIONS-LK.si.md) and [REGIONS-LK.ta.md](REGIONS-LK.ta.md).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026. Each source carries one of three marks:

- **opened**: the page or file itself was opened and read;
- **search only**: the fact was seen in a search result, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

Several pages could not be opened (HDX returned HTTP 403 and data.gov.lk had an expired certificate), so most
government-source rows are "search only" or "not checked". Those need a second look before anything is built on them.

## What a region is

Sri Lanka is one island and a small country (about 65,000 km²). The proposal is **one region for the whole island**,
code `LK`, the same approach REGIONS.md takes for Guyana. A bare `LK` collides with no US code in `STATE_CODES`.

Sri Lanka's own levels are 9 provinces, 25 districts and about 330 Divisional Secretariat divisions (search only; HDX's
COD-AB lists levels 0 to 4). A province or district split would cut the island into pieces smaller than most US
states' maps and make a person pick between maps they may move between, so it is not proposed. If the maintainers
prefer finer regions, ISO 3166-2:LK gives `LK-1` to `LK-9` for provinces (not checked against the ISO site).

### Box

| Code | Name | Box (west, south, east, north) | Box with 0.15° margin | Box taken from |
|---|---|---|---|---|
| `LK` | Sri Lanka | 79.1642, 5.6213, 82.6461, 10.0715 | 79.01, 5.47, 82.80, 10.22 | Geofabrik's `sri-lanka.poly` (opened) |

The box above is computed from the clipping polygon Geofabrik uses for its Sri Lanka extract (9 vertices, opened on
17 November 2026). It is **loose**: it includes sea around the island, so it is an upper bound, not a tight box. The
box rule in REGIONS.md takes the box from an official boundary instead. The tight box should be recomputed from OCHA's
COD-AB level 0 (Survey Department source) once someone can open it; the island lies roughly between 79.5° and 82°
east and 5.9° and 9.9° north (from general knowledge, not computed here).

Two decisions are tied to the box:

- **Offshore islands.** The north (Jaffna peninsula and the islands to its west) and Mannar are inside the box. India's
  coast is about 30 km from Mannar, so the 0.15° margin and the box edge will pull in a strip of Tamil Nadu around the
  Palk Strait. Whether to clip to Sri Lanka's land and territorial sea is left to the maintainers.
- **Disputed or sensitive boundaries.** Nothing here is claimed to be disputed; the item is listed only so it is
  decided once for every region (REGIONS.md item 6).

## Sources, layer by layer

Sri Lanka's government publishes little open geospatial data under a stated licence. data.gov.lk lists most datasets
with "License Not Specified" (search result, page not opened), so government sources below are proposed only where a
licence is known, and otherwise recorded as gaps.

| Layer (file) | US source today | Proposed for Sri Lanka | Publisher | Licence | Mark |
|---|---|---|---|---|---|
| Roads, water, land (base map) | OSM extract | OSM extract, `sri-lanka-latest.osm.pbf` (137 MB; the `.gpkg.zip` is 357 MB) | OSM contributors via Geofabrik | ODbL 1.0 | opened |
| Points of interest (`poi`) | OSM | OSM | OSM contributors | ODbL 1.0 | opened |
| Places (`places.sqlite`) | GNIS, Census, OSM | OSM named places; OCHA COD-AB names and p-codes | OSM contributors; OCHA / Survey Department of Sri Lanka | ODbL 1.0; not checked (HDX returned 403) | search only |
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30 (as proposed for Guyana in REGIONS.md) | ESA / Airbus | Copernicus WorldDEM-30 licence | as in REGIONS.md |
| Water: reservoirs, dams | NHD, NID | OSM `water=reservoir` and `waterway=dam` for the first build; Irrigation Department and Mahaweli Authority inventories if a licence is found | OSM contributors | ODbL 1.0 | not checked for government lists |
| Crops (`crops.sqlite`) | USDA CDL | ESA WorldCover 2021 (land cover, not crop types), as for Guyana | ESA WorldCover consortium | CC BY 4.0 | as in REGIONS.md |
| Buildings (`buildings.sqlite`) | Microsoft US footprints | Microsoft Global ML Building Footprints or Overture buildings; coverage of Sri Lanka not checked | Microsoft; Overture | see REGIONS.md for the CDLA and ODbL question | not checked |
| Addresses | Overture addresses | **None found.** Overture's address theme lists 41 countries and Sri Lanka is not among them | | | opened |

Notes:

- **Already in flight.** PR #35 adds a Colombo box cut from the same Geofabrik extract
  (`sri-lanka-latest-free.gpkg.zip`). A whole-island region would replace that box with the full extract; it needs no
  new source.
- **Copernicus GLO-30 is a surface model.** Under tree canopy, which covers much of the wet zone and the central hills,
  relief and contours follow the canopy, not the ground.
- **Flood and landslide context.** UNOSAT published baseline layers for the June 2024 floods
  (`FL20240603LKA`, search result only, licence not read). Disaster layers could be a later addition, once a stable
  licence is confirmed.
- **Government data.** OCHA's COD-AB cites the Survey Department of Sri Lanka as source and was last updated
  2 August 2022 (search result). Reuse terms for the Survey Department's own products were not found.

## Licence notes and attribution

- **ODbL** (OpenStreetMap): credit "© OpenStreetMap contributors", say the data is under the ODbL, and offer a database
  built from it under the ODbL too. The US map already carries ODbL data, so this is not new.
- **Copernicus WorldDEM-30 and CC BY 4.0 (WorldCover):** the attribution sentences are in REGIONS.md and are not
  repeated here.
- **OCHA boundaries:** HDX datasets of this kind are usually CC BY-IGO, but the Sri Lanka page was not opened, so this is
  not confirmed.

## How addresses are written

Not checked from an official source. From general knowledge: Sri Lankan addresses usually give a house number, street,
town, and a **five-digit postal code**, and are written in Sinhala, Tamil or English. The first checks to make are the
Sri Lanka Post's published format and whether OSM `addr:*` tags cover enough of the island. This part needs a native
reader's review.

Because Overture has no Sri Lankan addresses, address search would have nothing to index for a first build. The
proposal is to ship the map first and treat address search as a separate step: "clearly distinguish map detail from
street-address search", as the maintainers asked in #23.

## Still undecided

1. **Codes and names in setup.** As REGIONS.md item 1; `LK` alone is not a US code.
2. **The box rule.** Whether to recompute a tight box from COD-AB level 0, and whether to clip the strip of India near
   the Palk Strait.
3. **Language.** Place names exist in Sinhala, Tamil and English. Which name the map shows, whether `name:si` and
   `name:ta` are kept, and how search handles non-Latin scripts and transliteration (issues #3 and #54). The base map's
   fonts must also cover Sinhala and Tamil script; whether they do was not checked.
4. **Address search.** Which open source, if any, replaces Overture for Sri Lanka, and how a five-digit code and the
   Sinhala and Tamil forms are read (`engine/address_search.py` reads only US forms today).
5. **Crop classes.** Whether Sri Lanka gets WorldCover land cover only, as proposed for Guyana.
6. **Government data.** Which Sri Lankan lists (dams, tanks, hospitals) carry a licence that allows redistribution.
   Village irrigation tanks are a distinctive Sri Lankan water source and OSM's coverage of them was not measured.
7. **The California-only layers.** As REGIONS.md item 7.

## What was checked

- Opened: Geofabrik's Sri Lanka page (extract sizes, ODbL 1.0, data up to 16 November 2026), Geofabrik's
  `sri-lanka.poly`, and Overture's address documentation (41 countries, no Sri Lanka).
- Search only: OCHA COD-AB for Sri Lanka (levels, Survey Department source, 2 August 2022 update), data.gov.lk
  licensing, UNOSAT baseline layers.
- Not opened: HDX (HTTP 403), data.gov.lk (expired certificate), the Survey Department, Irrigation Department and
  Mahaweli Authority sites, Sri Lanka Post, the ISO site.
- Not computed: a tight land boundary box, OSM feature counts, and OSM coverage of Sri Lankan addresses.
