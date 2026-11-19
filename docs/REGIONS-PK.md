# Detailed maps for Pakistan: a proposal

This is a proposal for discussion, not a decision. It answers the questions [MAPS.md](MAPS.md) asks before coverage can
go beyond the United States, for Pakistan: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md),
[REGIONS-TH.md](REGIONS-TH.md) and [REGIONS-LK.md](REGIONS-LK.md), and is meant to feed the same design discussion
(issues #25 and #31). The worked example is Islamabad and Rawalpindi. The machine-readable version is
[regions-pk-proposed.json](regions-pk-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026. Each source carries one of three marks:

- **opened**: the dataset page, file, licence page or the portal's public API answer was opened and read;
- **search only**: the fact was seen in a search result, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

Three findings shape the rest:

- **Almost no government geodata carries an open licence.** NDMA's terms allow "personal, non-commercial use only". The
  Pakistan Bureau of Statistics (PBS), the Survey of Pakistan and its NSDI portal, and SUPARCO state copyright or "All
  Rights Reserved" and give no licence. The largest open data portal, opendata.com.pk, is run by a university centre
  (NCBC at LUMS, with the Higher Education Commission), not a ministry, and 1,443 of its 1,505 datasets state no
  licence. (All opened.) So, as for Thailand and Sri Lanka, the dependable base is OpenStreetMap plus global open
  datasets, with OCHA's boundaries.
- **Sources disagree about Kashmir**, and a build has to choose its files with that in mind. See "Disputed areas".
- **There are no open address points.** See "How addresses are written".

## What a region is

Pakistan has seven first-level units: four provinces (Balochistan, Khyber Pakhtunkhwa, Punjab and Sindh), the
Islamabad Capital Territory, and Azad Jammu and Kashmir and Gilgit-Baltistan, two areas Pakistan administers that are
part of the Kashmir dispute. OCHA's COD-AB and geoBoundaries both have these seven at the first level and no others
(opened). The proposal is one region per unit, seven in all, the same level as a US state.

The units are about the size of the larger US states. Balochistan has the largest box, about 9.4° by 7.2°, which is
smaller than California's (about 10.3° by 9.5°). Punjab, where about half the population lives, has a box of about 6.1°
by 6.3°.

### Codes

ISO 3166-2:PK codes: `PK-BA` Balochistan, `PK-GB` Gilgit-Baltistan, `PK-IS` Islamabad, `PK-JK` Azad Jammu and Kashmir,
`PK-KP` Khyber Pakhtunkhwa, `PK-PB` Punjab, `PK-SD` Sindh. All seven are in the `shapeISO` field of geoBoundaries'
province file and in Wikipedia's copy of the ISO list (both opened). ISO's own site was not read: it asks visitors to
accept its terms of use first.

- Wikipedia's copy gives `PK-JK` and `PK-GB` the category "Pakistan administered area", `PK-IS` "federal capital
  territory", and the other four "province". `PK-TA`, for the former Federally Administered Tribal Areas, was deleted
  in 2019; those areas are now part of Khyber Pakhtunkhwa.
- COD-AB has its own codes, `PK1` to `PK7`. They are listed in the JSON beside the ISO codes.
- No bare two-letter code is proposed, and the full hyphenated codes collide with nothing in `STATE_CODES`
  (`engine/address_search.py`). The part after the hyphen is not safe on its own: `SD` (Sindh) is also South Dakota.
  The other six (`BA`, `GB`, `IS`, `JK`, `KP`, `PB`) are not US codes. The current builder keeps only the first two
  characters of a region (`state.upper()[:2]` in `tools/build_addresses.py`): passing `PK-SD` directly would produce
  `PK`, not `SD`. Stripping the country prefix first is not a solution either, because `SD` would collide with
  South Dakota. An address index is accepted only under a two-letter name (`[A-Z]{2}` in
  `engine/setup/manifest.py` and `engine/setup/install.py`). The full `PK-` code needs to be preserved throughout,
  and those two-letter restrictions updated before Pakistani address indexes can be built or installed. A bare `PK` would not collide, if the maintainers prefer one region for the whole
  country, as REGIONS-LK.md proposes for Sri Lanka.
- PR #35 names its Islamabad city map `pk-isl`, in lower case and with a three-letter city part. That is a city box of
  OSM data, not a region, so the two schemes can live side by side. How setup lists both is a question for the
  maintainers (see "Still undecided").

### One place that needs a decision: Islamabad and Rawalpindi

The capital does not stop at the boundary of its territory. Rawalpindi, in Punjab, lies directly south of Islamabad,
and the two are one urban area, joined by main roads and a metro bus line. The Islamabad Capital Territory alone is
small: its box is about 0.6° by 0.3°.

The two options are the same as for Bangkok in REGIONS-TH.md:

- ship `PK-IS` on its own, which is simple, but someone who picks it loses Rawalpindi; or
- let the `PK-IS` map hold Rawalpindi District as well, as one box.

This proposal suggests the second. Together, COD-AB's Islamabad (`PK401`) and Rawalpindi (`PK630`) districts have the
box 72.6322, 33.0644, 73.6317, 34.0183, and with the 0.15° margin 72.48, 32.91, 73.79, 34.17: about 1.3° on each side.
In the JSON this group is called `PK-ISR`. That is not an ISO code, only a label for the group, like `TH-BMR` in the
Thailand proposal.

Karachi and Lahore need no group of their own. Each lies well inside its province's box (Sindh and Punjab).

### Disputed areas

Three stretches of Pakistan's boundary are disputed, and a map has to draw something along them:

- **Kashmir.** Azad Jammu and Kashmir and Gilgit-Baltistan are administered by Pakistan and claimed by India. India
  administers the rest of the former princely state, which Pakistan claims. The Line of Control divides the two sides.
  North of its last point, NJ9842, the two countries claim different lines, and India has held the Siachen Glacier
  since 1984. China administers areas to the east and north-east that India also claims.
- **Sir Creek**, at the seaward end of the boundary between Sindh and the Indian state of Gujarat.
- **The border with Afghanistan** (the Durand Line), which Afghanistan has not formally accepted.

REGIONS.md already lists "Boundaries in dispute" as an open question for the maintainers (item 6). This proposal does
not answer it. It suggests only this much: offer `PK-JK` and `PK-GB` as regions, because the people who live there need
a map as much as anyone, and draw whatever the maintainers decide along every disputed line.

What the sources do in Kashmir (all opened):

- **Both boundary files follow Pakistan's claim north of NJ9842.** Gilgit-Baltistan's eastern-most vertex is at
  77.834°E, 35.502°N in COD-AB and 77.815°E, 35.471°N in geoBoundaries, each within about 5 km of the Karakoram Pass.
  That fits the line Pakistan claims, which takes in the Siachen Glacier. So the `PK-GB` box follows one side's claim
  there, not the ground each side holds.
- **For Azad Jammu and Kashmir the two files disagree.** geoBoundaries reaches 75.49°E; COD-AB stops at 74.86°E.
  Neither was compared with the Line of Control, but they cannot both follow it.
- **COD-AB** lists "Azad Kashmir" (`PK1`) and "Gilgit Baltistan" (`PK3`) as two of its seven first-level units, with
  nothing to mark them apart from the provinces.
- **ISO 3166-2** gives both the category "Pakistan administered area".
- **Geofabrik's extracts follow who holds the ground.** Test points in Muzaffarabad, Mirpur, the Neelum valley, Gilgit,
  Skardu and Khunjerab fall inside `pakistan.poly` and outside `india.poly`. Points in Srinagar, Jammu and Leh fall the
  other way round. The Pakistan outline is coarse, 200 points: it stops at 77.22°E, splits the Siachen Glacier, and
  takes in a test point in the Shaksgam Valley, which China administers.
- **Microsoft's building footprints file Gilgit-Baltistan under India.** See "Buildings" in the notes below.

### Boxes

The boxes below were computed from **OCHA's COD-AB for Pakistan** (`pak_admin1.geojson` in HDX's GeoJSON zip, SHA-256
`dc56da20…08dee45c`; source World Food Programme SDI; boundaries created 2 September 2022, valid from 9 September 2022,
reviewed 27 September 2024; CC BY-IGO), on 17 November 2026. Each box is the extent of every vertex of the unit. The
margin is 0.15° on each side, rounded outward to 0.01°, the same as `map_sets.state` uses for US states.

They were then compared with **geoBoundaries' first-level file** (gbOpen, PAK, ADM1; source given as "geoBoundaries,
Wikipedia"; data updated 19 January 2023, built 12 December 2023; Public Domain). The last column gives the largest
difference between the two boxes on any edge.

- **Six of the seven agree to within 0.10°**, which the 0.15° margin absorbs.
- **Azad Jammu and Kashmir does not.** geoBoundaries' polygon reaches 0.63° further east (see "Disputed areas").
- **COD-AB is the finer file**: 685 to 4,981 vertices per unit, against 95 to 926 in geoBoundaries. The zip also holds
  an edge-matched set (`*_em.geojson`), whose boxes differ from these by at most 0.008°.
- **Coastal boxes may be loose.** How far the Sindh and Balochistan boxes reach out to sea was not measured.
- **geoBoundaries' districts are out of date.** Its second-level file has 126 districts; COD-AB has 160.

| Code | Name | Box (west, south, east, north) | Box with 0.15° margin | Largest difference from geoBoundaries |
|---|---|---|---|---|
| `PK-BA` | Balochistan | 60.8786, 24.8907, 70.2948, 32.1006 | 60.72, 24.74, 70.45, 32.26 | 0.09° |
| `PK-GB` | Gilgit-Baltistan | 72.5128, 34.5158, 77.8340, 37.0894 | 72.36, 34.36, 77.99, 37.24 | 0.09° |
| `PK-IS` | Islamabad Capital Territory | 72.8139, 33.4897, 73.3894, 33.8119 | 72.66, 33.33, 73.54, 33.97 | 0.09° |
| `PK-JK` | Azad Jammu and Kashmir | 73.3980, 32.7692, 74.8649, 35.1347 | 73.24, 32.61, 75.02, 35.29 | **0.63°** |
| `PK-KP` | Khyber Pakhtunkhwa | 69.2388, 31.1655, 74.1274, 36.9076 | 69.08, 31.01, 74.28, 37.06 | 0.10° |
| `PK-PB` | Punjab | 69.3213, 27.7051, 75.3819, 34.0183 | 69.17, 27.55, 75.54, 34.17 | 0.04° |
| `PK-SD` | Sindh | 66.5961, 23.6947, 71.1244, 28.4850 | 66.44, 23.54, 71.28, 28.64 | 0.08° |
| `PK-ISR` | Islamabad and Rawalpindi (group) | 72.6322, 33.0644, 73.6317, 34.0183 | 72.48, 32.91, 73.79, 34.17 | |
| `PK` | All of Pakistan, for reference | 60.8786, 23.6947, 77.8340, 37.0894 | 60.72, 23.54, 77.99, 37.24 | |

Names follow ISO 3166-2. COD-AB writes "Azad Kashmir", "Gilgit Baltistan" and "Islamabad".

## Sources, layer by layer

| Layer (file) | US source today | Proposed for Pakistan | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, 30 m | ESA / Airbus | Copernicus WorldDEM-30 | as in REGIONS.md; not re-checked for Pakistan |
| Terrain, national | | none found | Survey of Pakistan; NSDI | "All Rights Reserved" on NSDI; no licence on the Survey's site | opened |
| Water (`water.sqlite`) | NHD | OSM waterways and water areas, from Geofabrik's Pakistan extract | OSM contributors | ODbL 1.0 | opened |
| Dams | NID | Global Dam Watch database (GDW) v1.0, which supersedes GRanD | Global Dam Watch | CC BY 4.0 | record opened (published 25 July 2024); dams in Pakistan not counted |
| Dams, national | | WAPDA's lists | WAPDA | | not checked: the site reset every connection |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | ESA WorldCover 2021, 10 m (land cover, not crop types) | ESA WorldCover consortium | CC BY 4.0 | as in REGIONS.md |
| Crops, partial | | ESA WorldCereal 2021 v100: winter cereals, maize, temporary crops and irrigation | ESA WorldCereal consortium | CC BY 4.0 | record opened; see notes |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Microsoft Global ML Building Footprints (Pakistan's files, plus the India files that hold Gilgit-Baltistan, clipped); OSM heights | Microsoft; OSM contributors | CDLA Permissive 2.0; ODbL | opened; see notes |
| Buildings, alternative | | Overture buildings (from OSM, Esri, Microsoft and Google) | Overture Maps Foundation | ODbL, version not stated | guide opened; Pakistan not named |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | OSM named places, through HOT's populated places export (updated 16 November 2026, refreshed every 30 days) | OSM contributors, via HOT on HDX | ODbL | read through the HDX API |
| Places, boundaries | Census boundary files | COD-AB: 7 provinces and territories, 160 districts, 577 tehsils | OCHA, from WFP's SDI | CC BY-IGO | read through the HDX API; files downloaded and read |
| Roads (base map) | OSM | OSM, as today | OSM contributors | ODbL 1.0 | opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **none found** (see "How addresses are written") | | | opened |
| Points of interest (`poi` rows) | OSM | OSM, plus healthsites.io's Pakistan export (29 September 2026) | OSM contributors; healthsites.io on HDX | ODbL | read through the HDX API |
| Flood context (new) | | UNOSAT flood extents for the 2022 floods | UNOSAT, on HDX | "CC BY-SA", no version | read through the HDX API |

### Help and resource points in OSM

Counts for all of Pakistan from Geofabrik's taginfo (data until 16 November 2026; opened):

| Tag | Objects |
|---|---|
| `amenity=hospital` | 2,560 |
| `amenity=clinic` | 936 |
| `amenity=pharmacy` | 891 |
| `amenity=fuel` | 3,806 |
| `amenity=police` | 797 |
| `amenity=fire_station` | 66 |
| `amenity=shelter` | 254 |

- 66 fire stations for the whole country is very likely an undercount: Rescue 1122 alone runs stations across Punjab
  and Khyber Pakhtunkhwa. No open list of its stations with coordinates was searched for.
- In OSM, `amenity=shelter` mostly marks small weather shelters (bus stops, huts), not evacuation centres.

Notes:

- **Geofabrik.** The Pakistan extract of 16 November 2026 is 150 MB as `.osm.pbf` and 360 MB as the GeoPackage
  `tools/build_map.py` reads, under ODbL 1.0 (opened). Its outline covers Azad Jammu and Kashmir and Gilgit-Baltistan
  (see "Disputed areas").
- **Terrain.** No open national elevation model was found. GLO-30 is a surface model, as REGIONS.md notes.
- **Buildings.**
  - Google Open Buildings v3 lists 110 countries, India among them, but not Pakistan. Its page says sensitive areas,
    including conflict zones, were left out (opened).
  - Microsoft's file index of 13 August 2026 has 225 Pakistan rows, about 2.69 GB compressed (opened).
  - Gilgit-Baltistan's tiles are filed under India. Quadkey `123101232` (74.53–75.23°E, 36.60–37.16°N, around Sost in
    Hunza) is listed only under India (opened, and checked a second time separately). That tile holds 3,363
    footprints. The Gilgit tile is also listed under India only, and 47 quadkeys appear under both countries.
  - Whether Azad Jammu and Kashmir's tiles are filed the same way was not checked.
  - Microsoft's README says CDLA Permissive 2.0, while Overture's attribution page lists the same source under ODbL, as
    REGIONS.md notes.
- **Dams.** WAPDA's site could not be reached, and HDX has no Pakistan dams dataset (opened). GRanD's licence was not
  read (SEDAC timed out); GDW replaces it in any case.
- **Crops.** ESA WorldCereal places Pakistan's plains in a zone with winter cereal, maize, temporary crop and irrigation
  layers, but it has no rice, cotton or sugarcane, and it is published only as global files of 3.8 to 25 GB (Zenodo
  record opened). FAO's WaPOR v3 has no crop-type map for Pakistan, and SUPARCO publishes no open data (both opened).
  WorldCover remains the fallback, as for Guyana.
- **Places.** OCHA also hosts an older settlements layer from NGA (2017, labelled CC BY-IGO). PBS's 2023 census tables
  list rural localities for the four provinces and Islamabad, with no coordinates, nothing for Azad Jammu and Kashmir or
  Gilgit-Baltistan, under "All Rights Reserved" (opened). No open list of *mauzas* (revenue villages) was found
  (search only).
- **Floods.** UNOSAT has 18 datasets for the 2022 floods, dated 10 August 2022 to 7 March 2023. All are labelled "CC
  BY-SA" with no version. The VIIRS water extents for 1 to 29 August 2022 (`FL20220808PAK`, 31 August 2022) show about
  75,000 km² flooded, of about 793,000 km² analysed (read through the HDX API). Flooding is Pakistan's most damaging
  hazard, so this is useful context, but the share-alike licence needs a decision first.

## Licence notes and attribution

- **ODbL 1.0** (OSM through Geofabrik, HOT's export, healthsites.io; Overture buildings). The same as for the US map:
  "© OpenStreetMap contributors", the data is under the ODbL, and a database built from it is offered under the ODbL.
- **Copernicus WorldDEM-30**: as in REGIONS.md.
- **CC BY 4.0** (ESA WorldCover, ESA WorldCereal, GDW). Credit the publisher, link the licence and say if the data was
  changed.
- **CDLA Permissive 2.0** (Microsoft footprints, by its README), with the ODbL question above.
- **CC BY-IGO** (COD-AB). Credit OCHA and its source, the World Food Programme's SDI.
- **Public Domain** (geoBoundaries' Pakistan files, by its metadata). Used here only to compare boxes.
- **"CC BY-SA" with no version** (UNOSAT's flood layers). A share-alike licence that would sit beside the ODbL.
- **Not usable as published**:
  - NDMA's website terms: "personal, non-commercial use only", and reproduction is not allowed (opened).
  - PBS, the Survey of Pakistan, NSDI and SUPARCO: copyright or "All Rights Reserved", with no licence (opened).
  - Pakistan Post's postcode list: no licence (opened).
  - opendata.com.pk datasets that state no licence (1,443 of 1,505).
- **A policy to watch.** PBS's Official Statistics and Data Dissemination Policy (August 2026) says its open products
  shall be released under "a standard open government license" allowing adaptation and commercial use with
  acknowledgement, but it names no licence yet. It classifies shapefiles and block-level data as PBS assets, and census
  maps carry a published rate (opened).
- **Pakistan's mapping law.** The Surveying and Mapping Act 2014, as amended in 2020, is reported to require maps to be
  vetted by the Survey of Pakistan before publication (search only; the Act's text was not read). Whether that bears on
  a free offline map distributed from outside Pakistan is a legal question this proposal does not answer.

## How addresses are written

- **Order.** Name, house number, street number, sector, then locality and postcode on one line, then PAKISTAN, all
  left-aligned (Universal Postal Union addressing sheet for Pakistan, dated September 2004; opened). The locality and
  postcode are joined by a dash: `ISLAMABAD–44000`.
- **Postcode.** Five digits: the first two give the routeing district and the last three the post office (same sheet).
  Pakistan Post's own list has 2,298 delivery and 848 non-delivery post offices by province, including Azad Kashmir
  and Gilgit Baltistan, with no coordinates and no licence (opened).
- **Planned cities use sectors and blocks.** Islamabad is laid out in lettered and numbered sectors, written like
  `F-7/2` or `G-9/4`, and an address there is usually a house number, a street number and a sector:
  "House 12, Street 34, F-7/2, Islamabad". Housing schemes in Lahore, Karachi and Rawalpindi use phases, blocks and
  sectors in the same way. In older city areas and villages, people give a landmark, a *mohalla* (neighbourhood) or a
  village, then the *tehsil* and the district.
- **Two scripts.** Addresses and street names are written in English and in Urdu (Nastaliq script). Names in OSM are
  mostly in Latin letters, and some carry `name:ur`. Latin spellings of the same name vary between sources.
- **Few address points.** Overture's address theme covers 41 countries and Pakistan is not one of them (release
  2026-10-21.0; opened). OSM has 104,601 objects with `addr:housenumber`, 153,925 with `addr:street` and 10,504 with
  `addr:postcode` in all of Pakistan (Geofabrik's taginfo, data until 16 November 2026; opened). That is far too few for
  house-number search in a country of about 240 million people.
- **What the current code does with that.**
  - `engine/address_search.py` treats a query as an address only when it starts with a digit (`is_address_query`), so
    "House 12, Street 34, F-7/2" is read as a place search.
  - It removes every character outside `a-z`, `0-9` and spaces before matching. So an address typed in Urdu is removed
    completely, and `F-7/2` becomes `f 7 2`.
  - A five-digit postcode at the end is read as a postcode, which fits Pakistan's, even when it is written
    `ISLAMABAD–44000` with a dash.
  - Until there are address points, search in Pakistan would be by place, sector, block and road name, not by house
    number. Searching for a sector would need `F-7/2` kept together as one word.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md.

1. **Codes in setup.** Whether `PK-PB` style codes are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup lists them beside PR #35's city maps (`pk-isl`).
2. **The box rule**, as in REGIONS.md. This proposal takes its boxes from COD-AB, not geoBoundaries.
3. **Islamabad and Rawalpindi**: one map holding both, or the capital territory on its own.
4. **Disputed boundaries.** REGIONS.md's item 6 applies to the Line of Control and the line north of NJ9842, Sir Creek
   and the Durand Line: what the map draws along each, what setup calls `PK-JK` and `PK-GB`, and whether the app says
   anything about the claims.
5. **Kashmir in the source files.** Whether footprints for `PK-GB` may be taken from files Microsoft labels India, and
   which boundary decides what goes into each region's pack.
6. **Search without address points**: place, sector, block and road search in Latin letters and in Urdu, in place of
   house-number search.
7. **Language.** Whether map labels and place names are stored in Latin letters, in Urdu, or both. Urdu is written
   right to left in Nastaliq, which needs a font that can draw it. This ties to the translation work in issue #54.
8. **Flood layers.** Whether UNOSAT's 2022 flood extents, under an unversioned CC BY-SA, may sit in a pack beside ODbL
   data.
9. **Pakistan's mapping law**, as above: whether it matters for Lastbook at all.

## What was checked, and what was not

- Opened on 17 November 2026:
  - Geofabrik's Pakistan page, and its `pakistan.poly` and `india.poly`.
  - geoBoundaries' API answers, and its first- and second-level Pakistan files.
  - Microsoft's footprints README and file index, and one tile.
  - Google's Open Buildings page, and Overture's buildings and address guides.
  - The UPU addressing sheet for Pakistan, and Pakistan Post's postcode list.
  - NDMA's terms; the sites of the Survey of Pakistan, NSDI, SUPARCO and PBS; and PBS's dissemination policy.
  - opendata.com.pk, through its CKAN API.
  - Wikipedia's copy of ISO 3166-2:PK.
  - The GDW, GRanD and GROD records, ESA WorldCereal's record and FAO's WaPOR v3 catalogue.
- Read through public APIs: HDX (COD-AB and its attribute table, UNOSAT's flood datasets, healthsites.io, HOT's
  populated places, OCHA's settlements) and Geofabrik's taginfo for Pakistan.
- Downloaded and read: COD-AB's GeoJSON zip (29 MB) and geoBoundaries' two Pakistan GeoJSON files.
- Computed: the seven boxes, the Islamabad and Rawalpindi box and the country box from COD-AB; the same from
  geoBoundaries for comparison; the extent of quadkey `123101232`; and where each Kashmir polygon reaches furthest east.
- Checked a second time, separately: Microsoft's Pakistan row count and the India listing of `123101232`, Google's
  country list, and COD-AB's levels, licence and dates.
- Seen only in search results: the Surveying and Mapping Act's vetting rule, and that no open *mauza* list exists.
- Not checked:
  - ISO's own site (it asks visitors to accept its terms first).
  - WAPDA (connection reset), and the provincial open data portals for Punjab, Sindh and Khyber Pakhtunkhwa (not
    reachable).
  - GRanD's licence (SEDAC timed out) and the number of GDW dams in Pakistan.
  - How Microsoft files Azad Jammu and Kashmir's buildings.
  - Either boundary file against the Line of Control.
  - OSM's coverage of Rescue 1122 stations, and the Surveying and Mapping Act's text.
