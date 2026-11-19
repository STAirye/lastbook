# Detailed maps for the United Arab Emirates: a proposal

This is a proposal for discussion, not a decision. It answers, for the United Arab Emirates (UAE), the questions
[MAPS.md](MAPS.md) asks before coverage can go beyond the United States: which open source replaces each federal list,
under what licence, what a "state" is there, and how addresses are written. It follows the shape of
[REGIONS.md](REGIONS.md) and [REGIONS-TH.md](REGIONS-TH.md) and is meant to feed the same design discussion (issues #25
and #31). It covers all seven emirates. The machine-readable version is
[regions-ae-proposed.json](regions-ae-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026 by an AI assistant reading the pages named, for a
contributor based in Dubai. It has not yet had a second read by a person. Each source carries one of three marks:

- **opened**: the dataset page, file or licence page itself was opened and read;
- **search only**: the fact was seen in a search result, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

Several pages refused automated reading on the day: HDX, Geofabrik's download and taginfo pages, the Overpass API and
the government.ae document that holds the federal licence. So a fair number of rows are "search only", and no
OpenStreetMap counts could be taken. They need a second look before anything is built on them.

Three findings shape the rest:

- **The emirates do not sit side by side.** Five of the seven are in two or more separate pieces, and with the usual
  margin every emirate's box reaches into all six others. See "What a region is".
- **There are no postcodes, and no open address points were found.** Post goes to P.O. Boxes. Two official systems
  identify buildings instead, Makani and Onwani, and neither was found as a file that plainly fits an offline build.
- **Open data exists at three levels with three licences**: federal (bayanat.ae, CC BY 4.0), Dubai (Dubai Pulse, its
  own licence) and the other emirates. Few of the geographic files could be opened.

So for the UAE the dependable base is OpenStreetMap plus global open datasets, as for Thailand and Guyana.

## What a region is

The UAE is a federation of seven emirates: Abu Dhabi, Dubai, Sharjah, Ajman, Umm Al Quwain, Ras Al Khaimah and
Fujairah. The emirate is the level that matches a US state.

**The proposal is one region for the whole country, code `AE`, holding all seven emirates**, the approach REGIONS.md
takes for Guyana and REGIONS-LK.md for Sri Lanka. The seven boxes are given below so that seven maps stay possible.
The reasons:

- **The pieces are scattered.** In the boundary file used here, Ajman has three separate pieces of 10 km² or more,
  Fujairah three, Sharjah four, and Dubai and Ras Al Khaimah two each. Dubai's second piece lies about 34 km east of
  its main one.
- **The boxes overlap almost completely.** With the 0.15° margin, each emirate's box reaches into all six others.
  Sharjah's box already contains the whole of Ajman, Fujairah and Umm Al Quwain; Dubai's contains Ajman; Ras Al
  Khaimah's contains Fujairah. Because a state map holds every row inside its box, seven maps would ship the same
  towns several times over.
- **The lines run through built-up land.** Dubai, Sharjah and Ajman share boundaries in this file, so someone who
  picks Dubai would lose the streets next door unless the box brought them along anyway.
- **The country is small.** The whole box with its margin is 5.16° by 3.74°. The seven emirates' polygons in this file
  add up to about 71,000 km². How large the download would be is not known; no source was downloaded.

If one map proves too large, the middle option is two: Abu Dhabi alone (`AE-AZ`), and Dubai with the five northern
emirates as one box of 1.80° by 1.75°. "Dubai and the Northern Emirates" is a grouping the federal health service
already uses (search only). It has no ISO code.

### Codes

ISO 3166-2:AE gives each emirate two letters after `AE-`. The list was read from Wikipedia's copy and from the
`shapeISO` field of geoBoundaries' emirate file, which carries all seven (opened; ISO itself not checked).

- `AE` is not one of the entries in `STATE_CODES` (`engine/address_search.py`) or `NAMES`
  (`packaging/state_maps.py`), so `Lastbook-Map-AE.zip` and `derived/geo/addresses/AE.sqlite` collide with nothing.
- The part after the hyphen is not safe on its own: `AZ` already means **Arizona**. The other six (`AJ`, `DU`, `FU`,
  `RK`, `SH`, `UQ`) are not US codes. If emirates become regions, the full hyphenated code is needed.

### Boxes

The boxes were computed from **geoBoundaries' first-level file for the UAE** (gbOpen, ARE, ADM1; 7 features; source
data of 19 January 2023 from OpenStreetMap boundaries, built 12 December 2023; ODbL 1.0), using the full-resolution
GeoJSON on 17 November 2026 (SHA-256 `f6f0097b…1dd3d873`, in full in the JSON). Each box is the extent of every vertex
of the emirate, then minus and plus 0.15° and rounded outward to 0.01°, the same margin `map_sets.state` uses for US
states.

| Code | Name | Arabic | Pieces | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|---|
| `AE` | United Arab Emirates (all seven) | الإمارات العربية المتحدة | | 51.5318, 22.6316, 56.3816, 26.0695 | 51.38, 22.48, 56.54, 26.22 |
| `AE-AZ` | Abu Dhabi | أبو ظبي | 66 | 51.5318, 22.6316, 56.0174, 25.2528 | 51.38, 22.48, 56.17, 25.41 |
| `AE-DU` | Dubai | دبي | 9 | 54.8905, 24.6245, 56.2036, 25.3697 | 54.74, 24.47, 56.36, 25.52 |
| `AE-SH` | Sharjah | الشارقة | 9 | 55.3498, 24.7534, 56.3816, 25.6291 | 55.19, 24.60, 56.54, 25.78 |
| `AE-AJ` | Ajman | عجمان | 3 | 55.4229, 24.7395, 56.1056, 25.4507 | 55.27, 24.58, 56.26, 25.61 |
| `AE-UQ` | Umm Al Quwain | أم القيوين | 5 | 55.5211, 25.2756, 55.9281, 25.6568 | 55.37, 25.12, 56.08, 25.81 |
| `AE-RK` | Ras Al Khaimah | رأس الخيمة | 4 | 55.7310, 24.8203, 56.2717, 26.0695 | 55.58, 24.67, 56.43, 26.22 |
| `AE-FU` | Fujairah | الفجيرة | 3 | 55.9644, 24.8661, 56.3769, 25.6608 | 55.81, 24.71, 56.53, 25.82 |
| | Dubai and the Northern Emirates (six) | | | 54.8905, 24.6245, 56.3816, 26.0695 | 54.74, 24.47, 56.54, 26.22 |

"Pieces" is the number of separate polygons the file holds for the emirate, islands included. Abu Dhabi is one
piece of about 58,500 km² and 65 small ones.

- **Cross-check.** Natural Earth's 1:10m country outline gives 51.5693, 22.6209, 56.3836, 26.0748 for the UAE. The two
  agree to 0.04° on the west edge and to 0.011° on the other three.
- **The official boundary is a better source for a build.** OCHA lists a COD-AB for the UAE at levels 0 and 1, sourced
  from the Federal Competitiveness and Statistics Centre (search only; HDX could not be opened, so its licence and
  date are not confirmed). The boxes here were not checked against it.
- **The box holds neighbours.** The country box also covers parts of Oman and Saudi Arabia, as a US state box covers
  its neighbours.

### Boundaries that need a decision

REGIONS.md, item 6, asks whether Lastbook says anything on the map where a boundary is claimed by a neighbour. Nothing
here takes a side; these are listed only so the decision is made once.

- **Abu Musa and the Greater and Lesser Tunbs.** No polygon in the boundary file covers these three Gulf islands
  (tested at their approximate positions). They are administered by Iran and claimed by the UAE (general knowledge;
  not checked against a source in this change). Abu Musa lies inside the country box; the Tunbs lie just north of it.
- **Enclaves near the east coast.** An Omani enclave lies inside the UAE there, with a small piece of Sharjah inside
  it (general knowledge; not checked). The file has a 22 km² piece of Sharjah at about 56.20 to 56.25° E, 25.26 to
  25.31° N that would fit. A box cannot tell such pieces apart, which is one more reason for a single map.

## Sources, layer by layer

| Layer (file) | US source today | Proposed for the UAE | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, 30 m | ESA / Airbus | Copernicus WorldDEM-30 | AWS page opened; it says some countries' tiles are not public and does not name them, so UAE coverage is not confirmed |
| Water (`water.sqlite`) | NHD | OSM waterways and water areas, cut from Geofabrik's GCC States extract | OSM contributors | ODbL 1.0 | search only (page refused) |
| Dams | NID | OSM dams and reservoirs | OSM contributors | ODbL 1.0 | coverage not measured |
| Dams, national | | Dam points from the Ministry of Climate Change and Environment, as copied by NYU in December 2018 | the ministry; NYU Spatial Data Repository | **none seen** | search only; **not usable as found** |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | ESA WorldCover 2021, 10 m (land cover, not crop types) | ESA WorldCover consortium | CC BY 4.0 | as in REGIONS.md; not reopened |
| Crops, national | | Palm plantation areas from the same ministry, as copied by NYU in December 2018 | the ministry; NYU Spatial Data Repository | **none seen** | search only; **not usable as found** |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Overture buildings; Microsoft Global ML Building Footprints as an alternative; OSM heights | Overture; Microsoft; OSM contributors | ODbL; CDLA Permissive 2.0; ODbL | Overture's attribution page and Microsoft's README opened; no UAE count read |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | OSM named places with `name`, `name:ar` and `name:en` | OSM contributors | ODbL 1.0 | coverage not measured |
| Places, boundaries | Census boundary files | COD-AB United Arab Emirates, levels 0 and 1 | OCHA, from the Federal Competitiveness and Statistics Centre | CC BY-IGO (not confirmed) | search only |
| Roads (base map) | OSM | OSM, as today | OSM contributors | ODbL 1.0 | search only |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **no address points found** (see notes) | | | see notes |
| Points of interest (`poi` rows) | OSM | OSM, plus the lists below where a licence allows | | | below |

### Help and resource points

| Kind | Proposed source | Publisher | Coordinates | Licence | Checked |
|---|---|---|---|---|---|
| Hospitals, clinics, pharmacies, fire, police, fuel | OSM amenities, as the US map uses them | OSM contributors | yes | ODbL 1.0 | counts not measured |
| Public health facilities, Dubai and the Northern Emirates | Geospatial open data on the facilities page | Emirates Health Services | by its description | federal licence, not read on the page | search only |
| Licensed medical facilities, all emirates | Facilities by emirate, sector, type and location (2023) | Ministry of Health and Prevention | not known | federal licence | search only |
| Dams, national | 109 dams with over 90 million m³ of storage, by the government portal | Ministry of Energy and Infrastructure | no list with coordinates found | | search only |
| Wells, springs and dams, national | Hydrogeological map and geodatabase (December 2023) | Ministry of Energy and Infrastructure; Environment Agency – Abu Dhabi | by the announcement | no open download found | search only |
| Dubai transport stations, schools, parks and beaches | Point datasets on Dubai Pulse | Dubai government entities | yes for parks and beaches, by title | Dubai's Open Data Licence | search only; some show a "Request Permission" step |
| Shelters | none found | | | | not searched in depth |

Notes:

- **Terrain.** Copernicus GLO-30 is a surface model. In open desert that is close to the ground; in Dubai, Abu Dhabi
  and Sharjah relief will follow the towers. No open national elevation model was looked for beyond a search.
- **Water is the hard layer.** The government portal says surface water and rainwater are limited (search only). Most
  watercourses are wadis that run only after rain, so a line on the map is not a place to drink. The points that
  matter to a reader are wells, springs, public drinking water and the reservoirs behind dams. How well OSM covers
  them was not measured.
- **Dams.** The federal ministry's figure was 103 dams and about 80 million m³ in 2024 reports and 109 dams and over
  90 million m³ on the government portal (both search only). No list with coordinates and a licence was found. The
  NYU copy has coordinates but no licence and no collection date.
- **Crops.** `tools/build_crops.py` keeps orchards, vineyards and berries. Date palms are the obvious orchard kind
  here: one paper puts the country's palms at over 40 million. bayanat.ae has palm figures by emirate under CC BY 4.0,
  but for 2007 and as figures, not as a map (both search only). WorldCover is the fallback, as for Guyana.
- **Buildings.** Google's Open Buildings v3 does **not** cover the UAE: its country list has Africa, South Asia,
  South-East Asia, and Latin America and the Caribbean (opened). Microsoft's README gives 1.4 billion buildings and a
  file index of 13 August 2026 with 225 regions; the index could not be reached, so nothing is known about the UAE's
  share. Its README says CDLA Permissive 2.0, while Overture's attribution page lists the same source under ODbL, the
  question REGIONS.md raises for Guyana. Dubai Municipality publishes building tables on Dubai Pulse (usage, floors,
  community); whether any has outlines was not checked.
- **Addresses.** Overture's address theme lists 41 countries and territories, and the UAE is not one of them (opened;
  page last updated 15 May 2026). See "How addresses are written" for what exists instead.
- **Geofabrik.** There is no UAE extract. The UAE is inside "GCC States" (`gcc-states-latest.osm.pbf`), with Bahrain,
  Kuwait, Oman, Qatar and Saudi Arabia, so a build has to cut the country out first (search only; file name seen on
  the OSM wiki).

## Licence notes and attribution

- **ODbL 1.0** (OSM through Geofabrik, geoBoundaries' emirate file, Overture buildings). The same as for the US map:
  "© OpenStreetMap contributors", the data is under the ODbL, and a database built from it is offered under the ODbL.
- **Copernicus WorldDEM-30**, **CC BY 4.0** (ESA WorldCover) and **CDLA Permissive 2.0** (Microsoft, by its README):
  as in REGIONS.md.
- **CC BY 4.0 on bayanat.ae** (opened). The federal portal's terms of use say its data is under CC BY 4.0, for
  commercial and non-commercial use. The terms give no fixed credit wording.
- **UAE Federal Open Data Licence** (search only). Several federal entities' own open data pages name this licence;
  at least one names CC BY 4.0 instead. A summary seen in search results calls it worldwide, royalty-free, perpetual
  and non-exclusive. The full text is in a government.ae guideline that refused automated reading, so its conditions
  are not confirmed, and neither is how it relates to CC BY 4.0 on bayanat.ae.
- **Dubai's Open Data Licence** (opened; no date or version, and the file name says "DRAFT"). Worldwide, royalty-free
  and non-exclusive, for commercial and non-commercial use, including adapting. Four conditions matter for a pack:
  - credit the originator, keep any copyright notice and link the original where practicable;
  - **adapted material must be offered under the same licence**, which is a share-alike rule and would sit beside the
    ODbL's;
  - **original information may not be sold**, though work built on it may be;
  - the licensor's and the Dubai Government's names may not be used to suggest a link, and images, logos, trademarks
    and personal data are outside the licence.
- **Makani's own terms** (search only). Dubai Municipality asks to be named as the source and says Makani data may not
  be sold; for-profit applications are allowed where they serve the public interest of Dubai or the UAE.
- **No licence seen** (the NYU copies of ministry layers). Treated as not yet usable, as in REGIONS-AR.md.

Lastbook is free, so "may not be sold" is not a bar by itself. Whether such a term can travel with a library that
people copy for each other is for the maintainers; REGIONS.md turned down HydroRIVERS over terms of that kind.

## How addresses are written

- **Postal addresses are P.O. Boxes.** The Universal Postal Union's sheet for the UAE (September 2014; opened) says
  deliveries are made to P.O. Boxes only and shows no postcode. Its example is "MR. OMAR HUSSAIN / PO BOX 111 / DUBAI
  / UNITED ARAB EMIRATES". A P.O. Box says nothing about where a building is.
- **Makani (Dubai and four northern emirates).** A ten-digit number for each building entrance, written as two groups
  of five: "30032 95320". The app's own description calls it the official geographic addressing system of Dubai,
  Ajman, Umm Al Quwain, Fujairah and Ras Al Khaimah, and a trade press report says five digits are an easting and
  five a northing (both search only). Dubai Municipality offers Makani as an online service, which does not fit an
  offline build, and Dubai Pulse lists a building entrances file dated 23 April 2024 that was not opened.
- **Onwani (Abu Dhabi).** Building number, street name and city: "26, Al Seray Street, Khalifa City, Abu Dhabi".
  News reports give about 200,000 numbered buildings, 19,000 named streets and 240 districts, and say each location
  also has a postal code (search only). No open file of these addresses was found.
- **Sharjah** is in neither list above. How its buildings are addressed was not researched.
- **Two scripts.** Signs and data carry Arabic and Latin letters, and Latin spellings vary: the ISO list has "Abū
  Z̧aby", "Ash Shāriqah" and "Dubayy" for Abu Dhabi, Sharjah and Dubai (Wikipedia's copy; opened). Search needs Arabic
  as written, plus forgiving matching of Latin spellings.
- **What the current code does with that** (checked in this repository on 17 November 2026):
  - `normalize()` keeps only `a-z` and `0-9`, so Arabic script is dropped entirely and "Ra's al Khaymah" becomes
    "ra s al khaymah";
  - `is_address_query()` needs a number and then a space: "26 Al Seray Street" is read as an address, but the usual
    Onwani form with a comma, "26, Al Seray Street", is not, and neither is "Villa 27, …";
  - a Makani number typed with its space, "30032 95320", is read as house number 30032, and `_parts()` then takes
    95320 as a five-digit postcode, which leaves no street; typed without the space it is not an address query at
    all;
  - `tools/build_addresses.py` keeps only `country = 'US'` and two letters of the region.

If the grid behind a Makani number is public, the number could be turned into a point with no address file at all,
which would suit an offline library well. The grid was not found, so this is a question, not a proposal.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md.

1. **Codes in setup.** Whether `AE`, or `AE-DU` style codes, are acceptable as a manifest `id`, in `map-set.json` and
   in `Lastbook-Map-<id>.zip`.
2. **The box rule**, as in REGIONS.md, and whether the official COD-AB boundary replaces the OSM-derived one used
   here.
3. **One map, two or seven.** One `AE` map for all seven emirates, as proposed; Abu Dhabi plus one map for the other
   six; or seven maps whose boxes overlap.
4. **Search without address points.** Place, street and community search in two scripts in place of house-number
   search, and whether a Makani number is read as a place.
5. **Licences.** Whether Dubai's licence (share-alike on adapted material, no resale of the original) and Makani's
   terms are acceptable for packs, and which federal licence applies to a federal dataset: CC BY 4.0 or the Federal
   Open Data Licence.
6. **Unlicensed ministry layers.** Whether to ask the Ministry of Climate Change and Environment and the Ministry of
   Energy and Infrastructure for licensed copies of the dam, well, spring and palm layers, and who asks.
7. **Help-point kinds for a dry country.** Which water points the map shows, and how they map to the kinds
   `web/map.js` already draws (`water`, `spring`, `reservoir`, `dam`), given that a wadi is usually dry.
8. **Boundaries in dispute**, as in REGIONS.md item 6, for the islands and enclaves named above.
9. **Language and direction.** Whether map labels and place names are stored in Arabic, in Latin letters or both, and
   right-to-left text in the interface. This ties to the language questions already open for other regions.
10. **The California-only layers.** The fish, boating and well layers are labelled California in `web/map.js`; they
    would stay empty here, as REGIONS.md notes.

## What was checked, and what was not

- Opened on 17 November 2026: Overture's attribution page, Google's Open Buildings page, Microsoft's footprints
  README, the AWS registry page for the Copernicus DEM, bayanat.ae's terms of use, Dubai's Open Data Licence (PDF),
  the Universal Postal Union sheet for the UAE, Wikipedia's copy of ISO 3166-2:AE, geoBoundaries' metadata and
  emirate file, and issues #25 and #31.
- Computed on 17 November 2026: the seven boxes, the country box and the six-emirate box, from geoBoundaries' file;
  the piece counts and areas; which boxes contain which emirates; the cross-check against Natural Earth.
- Read in this repository: `STATE_CODES`, `normalize()`, `is_address_query()` and `_parts()` in
  `engine/address_search.py`, `NAMES` in `packaging/state_maps.py`, the country filter in
  `tools/build_addresses.py`, and the layer list in `web/map.js`.
- Seen only in search results: everything about Makani and Onwani, the federal licence, the dam figures, the NYU
  copies of ministry layers, the health facility datasets, Dubai Pulse's dataset lists, COD-AB for the UAE, and
  Geofabrik's GCC States extract.
- Not checked: HDX and COD-AB itself; the boxes against COD-AB; ISO's own site; any OpenStreetMap count for the UAE
  (taginfo and Overpass refused); Microsoft's file index and Overture's coverage for the UAE; whether every Copernicus
  tile for the UAE is public; the contents of any Dubai Pulse file; Sharjah's addressing; Abu Dhabi's open data
  platform and its licence; the positions and status of the islands and enclaves, which are from general knowledge;
  and the size of any download.
