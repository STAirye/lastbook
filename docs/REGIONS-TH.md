# Detailed maps for Thailand: a proposal

This is a proposal for discussion, not a decision. It answers, for Thailand, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a "state"
is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) and
[REGIONS-AR.md](REGIONS-AR.md) and is meant to feed the same design discussion (issues #25 and #31). Bangkok and the five
provinces around it are the worked example. The machine-readable version is
[regions-th-proposed.json](regions-th-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026. Each source carries one of three marks:

- **opened**: the dataset page, file, licence page or the portal's public API answer was opened and read;
- **search only**: the fact was seen in a search result, but the page itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

Thailand's open data portals (data.go.th, data.bangkok.go.th, catalog.disaster.go.th, opendata.gistda.or.th) all run
CKAN, so licences, file lists and column headers were read through their public APIs. Row counts marked "about" are line
counts of a CSV and can be too high where cells hold line breaks.

Two findings shape the rest:

- **Licence labels are vague.** Most Thai datasets carry a free-text label such as "Open Data Common" or "Creative
  Commons Attributions", with no version and no link. See "Licence notes".
- **Most Bangkok datasets state no licence.** On data.bangkok.go.th, 1,289 of 1,531 datasets say "License not
  specified", and that includes nearly every point layer with coordinates. A dataset with no stated licence is treated
  here as not yet usable, as in REGIONS-AR.md.

So for Thailand the dependable base is OpenStreetMap plus global open datasets, with a short list of national files
that do state a licence.

## What a region is

Thailand has 76 provinces (*changwat*) and Bangkok, which is not a province but a special form of local government.
The National Statistical Office's draft area standard says so in those words (opened). Datasets still treat Bangkok as
the 77th first-level unit: OCHA's boundaries and geoBoundaries both have 77 (opened). The proposal is one region per
province plus Bangkok, 77 in all, the same level as a US state.

### Codes

ISO 3166-2:TH gives each one two digits after `TH-`: `TH-10` Bangkok, `TH-11` Samut Prakan, `TH-12` Nonthaburi,
`TH-50` Chiang Mai, `TH-83` Phuket, and so on. The ISO site refused automated reading, so the list was read from
Wikipedia's copy and from the `shapeISO` field of geoBoundaries' province file, which carries all 77 (opened; ISO itself
not checked).

- The two digits are the Ministry of Interior's province code, the one Thai data already uses: the Department of
  Provincial Administration's subdistrict file has `91` for Satun, Bangkok's district codes run `1001` to `1050`, and
  OCHA's codes start `TH10` (opened; seen in samples, not compared row by row).
- The same two digits open the postcode of most addresses in the province (see "How addresses are written"), so the
  code and the address usually agree.
- No bare two-letter code is proposed, so nothing collides with a US state in `STATE_CODES`
  (`engine/address_search.py`).
- ISO also lists `TH-S` for Pattaya, a special city inside Chon Buri (`TH-20`). It is not proposed as a region.

### One place that needs a decision: Bangkok and its neighbours

The city does not stop at Bangkok's boundary. The National Statistical Office publishes "Bangkok and Vicinities"
(*Krung Thep Maha Nakhon lae Parimonthon*) as Bangkok, Samut Prakan, Nonthaburi, Pathum Thani, Nakhon Pathom and Samut
Sakhon: 7,761.66 km², 79 districts and 488 subdistricts (Statistical Yearbook 2025, table 1.23; opened).

Two options, the same choice REGIONS-AR.md describes for Buenos Aires:

- ship the six separately, which is simple, but someone who picks `TH-10` loses whatever lies across the boundary; or
- let the `TH-10` map hold all six, as one box.

This proposal suggests the second. The box for the six together is 99.8069, 13.4282, 100.9639, 14.2760, and with the
0.15° margin 99.65, 13.27, 101.12, 14.43: about 1.5° by 1.2°, smaller than most US states.

A different official grouping exists, the "Vicinity" provincial cluster of 30 May 2024, with only Nonthaburi, Pathum
Thani, Nakhon Pathom and Samut Prakan (same NSO draft standard; opened). It is an administrative grouping that leaves
out Bangkok itself, so it is not the one used here.

### Boxes

The boxes below were computed from **geoBoundaries' first-level file for Thailand** (gbOpen, THA, ADM1; 77 features;
built 12 December 2023 from OpenStreetMap boundaries; ODbL 1.0), using the full-resolution GeoJSON on 17 November 2026.
Each box is the extent of every vertex of the province, then minus and plus 0.15° and rounded outward to 0.01°, the
same margin `map_sets.state` uses for US states.

- **The official boundary is a better source for a build.** OCHA's COD-AB for Thailand comes from the Royal Thai Survey
  Department, under CC BY-IGO, with 77 provinces, 928 districts and 7,425 subdistricts (reviewed 30 October 2025; read
  through the HDX API). Its files are 175 to 437 MB and were not downloaded for this proposal, so the boxes here were
  not cross-checked against it. That check should come before anything is built.
- **Coastal boxes may be loose.** OpenStreetMap province boundaries can run out to sea, so a coastal box may hold more
  water than land needs. How far each box reaches offshore was not measured.

| Code | Name | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|
| `TH-10` | Bangkok | 100.3279, 13.4934, 100.9384, 13.9552 | 100.17, 13.34, 101.09, 14.11 |
| `TH-11` | Samut Prakan | 100.4448, 13.4791, 100.9639, 13.7185 | 100.29, 13.32, 101.12, 13.87 |
| `TH-12` | Nonthaburi | 100.2624, 13.7892, 100.5676, 14.1408 | 100.11, 13.63, 100.72, 14.30 |
| `TH-13` | Pathum Thani | 100.3316, 13.9163, 100.9521, 14.2760 | 100.18, 13.76, 101.11, 14.43 |
| `TH-14` | Phra Nakhon Si Ayutthaya | 100.2210, 14.1094, 100.8231, 14.6858 | 100.07, 13.95, 100.98, 14.84 |
| `TH-15` | Ang Thong | 100.1950, 14.4381, 100.5181, 14.7992 | 100.04, 14.28, 100.67, 14.95 |
| `TH-16` | Lopburi | 100.4327, 14.6558, 101.4098, 15.4975 | 100.28, 14.50, 101.56, 15.65 |
| `TH-17` | Sing Buri | 100.1914, 14.7248, 100.4936, 15.1675 | 100.04, 14.57, 100.65, 15.32 |
| `TH-18` | Chai Nat | 99.7161, 14.9072, 100.3091, 15.4203 | 99.56, 14.75, 100.46, 15.58 |
| `TH-19` | Saraburi | 100.5711, 14.2434, 101.4553, 15.0000 | 100.42, 14.09, 101.61, 15.15 |
| `TH-20` | Chon Buri | 100.6630, 12.5082, 101.7178, 13.5908 | 100.51, 12.35, 101.87, 13.75 |
| `TH-21` | Rayong | 100.9842, 12.5217, 101.8306, 13.1542 | 100.83, 12.37, 101.99, 13.31 |
| `TH-22` | Chanthaburi | 101.6850, 12.2970, 102.5359, 13.3362 | 101.53, 12.14, 102.69, 13.49 |
| `TH-23` | Trat | 102.2496, 11.5615, 102.9142, 12.7513 | 102.09, 11.41, 103.07, 12.91 |
| `TH-24` | Chachoengsao | 100.8490, 13.1716, 101.9989, 13.9766 | 100.69, 13.02, 102.15, 14.13 |
| `TH-25` | Prachin Buri | 101.1327, 13.5814, 102.1197, 14.4617 | 100.98, 13.43, 102.27, 14.62 |
| `TH-26` | Nakhon Nayok | 100.9136, 13.9612, 101.5155, 14.5061 | 100.76, 13.81, 101.67, 14.66 |
| `TH-27` | Sa Kaeo | 101.9439, 13.1578, 102.9410, 14.1881 | 101.79, 13.00, 103.10, 14.34 |
| `TH-30` | Nakhon Ratchasima | 101.1850, 14.0867, 103.0196, 15.8086 | 101.03, 13.93, 103.17, 15.96 |
| `TH-31` | Buri Ram | 102.4355, 14.1317, 103.5054, 15.7892 | 102.28, 13.98, 103.66, 15.94 |
| `TH-32` | Surin | 103.0896, 14.3302, 104.0797, 15.4829 | 102.93, 14.18, 104.23, 15.64 |
| `TH-33` | Si Sa Ket | 103.9150, 14.3411, 104.9175, 15.5645 | 103.76, 14.19, 105.07, 15.72 |
| `TH-34` | Ubon Ratchathani | 104.3839, 14.2096, 105.6368, 16.0979 | 104.23, 14.05, 105.79, 16.25 |
| `TH-35` | Yasothon | 103.9976, 15.2847, 104.8128, 16.3453 | 103.84, 15.13, 104.97, 16.50 |
| `TH-36` | Chaiyaphum | 101.3002, 15.2133, 102.4614, 16.7050 | 101.15, 15.06, 102.62, 16.86 |
| `TH-37` | Amnat Charoen | 104.4241, 15.5502, 105.0600, 16.2793 | 104.27, 15.40, 105.21, 16.43 |
| `TH-38` | Bueng Kan | 103.2433, 17.7653, 104.1879, 18.4486 | 103.09, 17.61, 104.34, 18.60 |
| `TH-39` | Nong Bua Lam Phu | 101.9450, 16.7597, 102.6884, 17.6809 | 101.79, 16.60, 102.84, 17.84 |
| `TH-40` | Khon Kaen | 101.7499, 15.6206, 103.1947, 17.0764 | 101.59, 15.47, 103.35, 17.23 |
| `TH-41` | Udon Thani | 102.0219, 16.8247, 103.6586, 18.0882 | 101.87, 16.67, 103.81, 18.24 |
| `TH-42` | Loei | 100.8817, 16.7544, 102.1539, 18.2203 | 100.73, 16.60, 102.31, 18.38 |
| `TH-43` | Nong Khai | 102.0583, 17.5908, 103.4094, 18.3040 | 101.90, 17.44, 103.56, 18.46 |
| `TH-44` | Maha Sarakham | 102.8483, 15.4059, 103.5111, 16.6434 | 102.69, 15.25, 103.67, 16.80 |
| `TH-45` | Roi Et | 103.2953, 15.4034, 104.3559, 16.4728 | 103.14, 15.25, 104.51, 16.63 |
| `TH-46` | Kalasin | 103.1130, 16.1867, 104.2461, 17.1011 | 102.96, 16.03, 104.40, 17.26 |
| `TH-47` | Sakon Nakhon | 103.2455, 16.7761, 104.4447, 18.0647 | 103.09, 16.62, 104.60, 18.22 |
| `TH-48` | Nakhon Phanom | 103.9864, 16.8054, 104.8066, 18.0248 | 103.83, 16.65, 104.96, 18.18 |
| `TH-49` | Mukdahan | 104.0722, 16.1897, 104.9777, 16.8989 | 103.92, 16.03, 105.13, 17.05 |
| `TH-50` | Chiang Mai | 98.0808, 17.2483, 99.5917, 20.1476 | 97.93, 17.09, 99.75, 20.30 |
| `TH-51` | Lamphun | 98.6676, 17.4238, 99.3153, 18.7072 | 98.51, 17.27, 99.47, 18.86 |
| `TH-52` | Lampang | 98.8795, 17.2019, 100.1255, 19.5089 | 98.72, 17.05, 100.28, 19.66 |
| `TH-53` | Uttaradit | 99.8964, 17.1617, 101.1927, 18.3813 | 99.74, 17.01, 101.35, 18.54 |
| `TH-54` | Phrae | 99.3103, 17.6764, 100.5422, 18.8346 | 99.16, 17.52, 100.70, 18.99 |
| `TH-55` | Nan | 100.3359, 18.0125, 101.3572, 19.6341 | 100.18, 17.86, 101.51, 19.79 |
| `TH-56` | Phayao | 99.6872, 18.8066, 100.6342, 19.7355 | 99.53, 18.65, 100.79, 19.89 |
| `TH-57` | Chiang Rai | 99.2597, 19.0000, 100.5785, 20.4648 | 99.10, 18.85, 100.73, 20.62 |
| `TH-58` | Mae Hong Son | 97.3438, 17.5668, 98.6553, 19.8143 | 97.19, 17.41, 98.81, 19.97 |
| `TH-60` | Nakhon Sawan | 99.0880, 15.0603, 100.8350, 16.3381 | 98.93, 14.91, 100.99, 16.49 |
| `TH-61` | Uthai Thani | 98.9853, 14.9379, 100.0723, 15.7828 | 98.83, 14.78, 100.23, 15.94 |
| `TH-62` | Kamphaeng Phet | 98.9844, 15.7825, 100.0331, 16.8889 | 98.83, 15.63, 100.19, 17.04 |
| `TH-63` | Tak | 97.9100, 15.1808, 99.3458, 17.7519 | 97.76, 15.03, 99.50, 17.91 |
| `TH-64` | Sukhothai | 99.2669, 16.6880, 100.1322, 17.8172 | 99.11, 16.53, 100.29, 17.97 |
| `TH-65` | Phitsanulok | 99.8853, 16.3471, 101.0953, 17.7481 | 99.73, 16.19, 101.25, 17.90 |
| `TH-66` | Phichit | 99.9761, 15.9089, 100.7730, 16.5987 | 99.82, 15.75, 100.93, 16.75 |
| `TH-67` | Phetchabun | 100.6272, 15.3020, 101.7964, 17.1172 | 100.47, 15.15, 101.95, 17.27 |
| `TH-70` | Ratchaburi | 99.1636, 13.1417, 100.0783, 13.9444 | 99.01, 12.99, 100.23, 14.10 |
| `TH-71` | Kanchanaburi | 98.1817, 13.7261, 99.8922, 15.6630 | 98.03, 13.57, 100.05, 15.82 |
| `TH-72` | Suphan Buri | 99.2726, 14.0603, 100.2841, 15.0758 | 99.12, 13.91, 100.44, 15.23 |
| `TH-73` | Nakhon Pathom | 99.8069, 13.6491, 100.3376, 14.1778 | 99.65, 13.49, 100.49, 14.33 |
| `TH-74` | Samut Sakhon | 100.0347, 13.4282, 100.4203, 13.7211 | 99.88, 13.27, 100.58, 13.88 |
| `TH-75` | Samut Songkhram | 99.8542, 13.2367, 100.0881, 13.5122 | 99.70, 13.08, 100.24, 13.67 |
| `TH-76` | Phetchaburi | 99.0994, 12.5425, 100.1061, 13.3333 | 98.94, 12.39, 100.26, 13.49 |
| `TH-77` | Prachuap Khiri Khan | 99.1434, 10.9536, 100.0200, 12.6348 | 98.99, 10.80, 100.17, 12.79 |
| `TH-80` | Nakhon Si Thammarat | 99.2397, 7.8011, 100.3361, 9.3231 | 99.08, 7.65, 100.49, 9.48 |
| `TH-81` | Krabi | 98.6245, 7.3997, 99.3475, 8.6750 | 98.47, 7.24, 99.50, 8.83 |
| `TH-82` | Phangnga | 97.6374, 7.8876, 98.7133, 9.4636 | 97.48, 7.73, 98.87, 9.62 |
| `TH-83` | Phuket | 98.2580, 7.4887, 98.4727, 8.2003 | 98.10, 7.33, 98.63, 8.36 |
| `TH-84` | Surat Thani | 98.4533, 8.3089, 100.0904, 10.1269 | 98.30, 8.15, 100.25, 10.28 |
| `TH-85` | Ranong | 98.3791, 9.3061, 98.9783, 10.7886 | 98.22, 9.15, 99.13, 10.94 |
| `TH-86` | Chumphon | 98.6287, 9.6011, 99.5200, 11.0313 | 98.47, 9.45, 99.67, 11.19 |
| `TH-90` | Songkhla | 100.0305, 6.2894, 101.1091, 7.9362 | 99.88, 6.13, 101.26, 8.09 |
| `TH-91` | Satun | 99.1538, 6.4227, 100.2203, 7.1467 | 99.00, 6.27, 100.38, 7.30 |
| `TH-92` | Trang | 99.2327, 7.0556, 100.0464, 7.9933 | 99.08, 6.90, 100.20, 8.15 |
| `TH-93` | Phatthalung | 99.7442, 7.0916, 100.4286, 7.9056 | 99.59, 6.94, 100.58, 8.06 |
| `TH-94` | Pattani | 101.0361, 6.5419, 101.7266, 6.9521 | 100.88, 6.39, 101.88, 7.11 |
| `TH-95` | Yala | 100.8347, 5.6129, 101.6169, 6.6800 | 100.68, 5.46, 101.77, 6.83 |
| `TH-96` | Narathiwat | 101.3791, 5.7329, 102.0933, 6.6365 | 101.22, 5.58, 102.25, 6.79 |

Names are romanised as in the source file, with the word "Province" removed.

## Sources, layer by layer

| Layer (file) | US source today | Proposed for Thailand | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | Copernicus DEM GLO-30, 30 m | ESA / Airbus | Copernicus WorldDEM-30 | opened; the page names no exclusion for Thailand |
| Terrain, national | | no open national elevation model found (see notes) | | | GISTDA's portal searched; Royal Thai Survey Department and Land Development Department not checked |
| Water (`water.sqlite`) | NHD | OSM waterways and water areas, from Geofabrik's Thailand extract | OSM contributors | ODbL 1.0 | opened |
| Water, national | | Department of Water Resources layers: natural water bodies, reservoirs, weirs, flood areas, gauging stations (Shapefiles) | Department of Water Resources | "Creative Commons Attributions" (no version) | file lists read; attributes not read; files dated September 2018 |
| Dams | NID | The dam point layer in the same set (about 1,087 points, worked out from the index file's size) | Department of Water Resources | as above | file list read; attributes not read |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | ESA WorldCover 2021, 10 m (land cover, not crop types) | ESA WorldCover consortium | CC BY 4.0 | opened |
| Crops, national | | Present land use at 1:25,000, one file per province, latest update 2023 | Land Development Department | CC BY-NC-ND on the data.go.th record | record opened; files not opened; **not usable as labelled** (see notes) |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | Google Open Buildings v3; Microsoft Global ML Building Footprints to fill gaps; OSM heights | Google; Microsoft; OSM contributors | CC BY 4.0 or ODbL (the user's choice); CDLA Permissive 2.0; ODbL | opened; Thailand is in both country lists; no count read |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | Subdistrict centre points with Thai and romanised names of the subdistrict, district and province (7,769 rows, XLSX); OSM named places | Department of Provincial Administration; OSM contributors | "Creative Commons Attributions"; ODbL | file opened; it holds visible duplicate rows |
| Places, boundaries | Census boundary files | COD-AB Thailand: provinces, districts, subdistricts | OCHA, from the Royal Thai Survey Department | CC BY-IGO | read through the HDX API |
| Roads (base map) | OSM | OSM, as today | OSM contributors | ODbL 1.0 | opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **no address points found** (see notes) | | | see notes |
| Points of interest (`poi` rows) | OSM | OSM, plus the lists below where a licence allows | | | below |

### Help and resource points

National lists first, then Bangkok's. "Coordinates" says whether the file read has latitude and longitude columns.

| Kind | Proposed source | Publisher | Coordinates | Licence | Checked |
|---|---|---|---|---|---|
| Shelters | Shelter list with capacity, power, water and toilets (about 10,976 rows, CSV; 26 May 2025) | Department of Disaster Prevention and Mitigation | yes | "Open Data Common" | header read through the API; Bangkok coverage not checked |
| Warning towers | Install points of warning towers (CSV; 1 August 2025) | Department of Disaster Prevention and Mitigation | not read | "Open Data Common" | record only |
| State hospitals | CITIZENinfo hospital list: Ministry of Public Health, Bangkok, military and university hospitals (CSV) | Digital Government Development Agency | yes, some rows blank | "Creative Commons Attributions" | header read; record dated 2021 |
| All state service points | CITIZENinfo locations, over 80,000 points by the record's description (CSV, 35 MB) | Digital Government Development Agency | yes | "Creative Commons Attributions" | header read; data from March 2020 |
| Health, from OSM | Thailand healthsites export (GeoJSON, CSV, Shapefile; 29 September 2026) | healthsites.io on HDX | yes | ODbL | read through the HDX API |
| Health registry | Health facility registry extract for Bangkok: codes, type, beds, address, postcode | Ministry of Public Health | **no** | "Creative Commons Attributions" | header read; the live registry was not checked |
| Schools, police, fire, pharmacies, fuel (national) | no national file with coordinates found; only province-by-province lists | various | | | search of data.go.th only |
| Bangkok health centres | Public health centres (about 70 rows; 14 May 2026) | Bangkok Metropolitan Administration (BMA) | yes | "Creative Commons Non-Commercial (Any)" | header read; **non-commercial** |
| Bangkok pharmacies | The Health Department's pharmacy network only (about 204 rows; 16 April 2026) | BMA | yes | "Open Data Common" | header read |
| Bangkok flood watch points | Flood risk and watch points (20 August 2023) | BMA | not read | "Creative Commons Attributions" | record only |
| Bangkok hospitals | Government (about 35), private (about 129) and BMA (about 11) hospitals | BMA | yes | **not specified** | headers read |
| Bangkok fire and police | Fire stations (about 48), metropolitan police stations (about 88) | BMA | yes | **not specified** | headers read |
| Bangkok schools | BMA schools (about 437) and a second school list (about 159) | BMA | yes | **not specified** | headers read |
| Bangkok drainage | Pumping stations (about 144), pumping stations and floodgates with capacity and control levels, flood risk points for 2025 (about 215) | BMA Drainage Department | yes | **not specified** | headers read |
| Bangkok canals | Canal list with water quality (about 303 canals) | BMA | **no geometry** | **not specified** | header read |
| Bangkok fuel | Fuel stations (ZIP and GML; 9 March 2021) | BMA | not read | **not specified** | record only |
| Bangkok shelters | none found: searches for shelter and evacuation words returned nothing | BMA | | | portal search |

Notes:

- **Terrain.** GISTDA's open data portal returned no elevation dataset for "DEM" or the Thai word for height. The
  Hydro-Informatics Institute publishes lidar terrain for 60 small reservoirs in 8 provinces under a non-commercial
  label, which is not a national model. Copernicus GLO-30 is a surface model, so it reads high in forest and in
  Bangkok's built-up areas.
- **Flooding matters more here than relief.** Bangkok is flat and low, and its hazards are flood and drainage. The
  pumping station, floodgate and flood risk files are the most useful Bangkok layers found, and none states a licence.
  Asking BMA to label them is the single most valuable step for a Bangkok map.
- **Water.** The Department of Water Resources set is the only national vector hydrography found. Its files are from
  2018, one resource link points at the dam archive by mistake, and the feature counts here were worked out from file
  sizes. The Royal Irrigation Department's large reservoir API gives storage and flow for about 35 reservoirs and has
  **no coordinates**. Bangkok's canal list has no geometry, so canals (*khlong*) come from OSM.
- **Crops.** The Land Development Department's land use map is the right dataset, but its data.go.th record says
  "Creative Commons Attribution Non-Commercial No-Derivs", and the department's own download page states no licence.
  Turning it into map tiles makes a derivative, so it cannot be used as labelled. GISTDA publishes rice, maize and
  cassava areas only as a query service by point or shape, with no bulk download. WorldCover is the fallback, as for
  Guyana.
- **Buildings.** Google's v3 covers South-East Asia and lists Thailand; inference is from May 2023. Microsoft's index
  of 13 August 2026 has 142 Thailand files, about 1.84 GB compressed. Microsoft's README says CDLA Permissive 2.0,
  while Overture's attribution page lists the same source under ODbL.
- **Places.** Three counts of subdistricts disagree: 7,425 in COD-AB, 7,435 in the Statistical Yearbook (at 31
  December 2024) and 7,769 rows in the Department of Provincial Administration's file. Bangkok's own subdistrict file
  has about 169 rows against the yearbook's 180, so it is out of date. COD-AB notes one wrong Thai name, for `TH1008`.
- **Addresses.** Overture's address theme covers 41 countries and Thailand is not one of them (opened). A search of
  data.go.th for house numbers with coordinates returned nothing. OSM has 70,470 objects with a house number in all of
  Thailand (taginfo, data to 16 November 2026), which is far too few for address search. Until that changes, search
  would be by place, road and *soi* name, not by house number.
- **Geofabrik.** The Thailand extract of 16 November 2026 is 315 MB as `.osm.pbf`, 698 MB as Shapefiles and 718 MB as
  the GeoPackage `tools/build_map.py` reads. The page says "License: ODbL 1.0".

## Licence notes and attribution

- **ODbL 1.0** (OSM through Geofabrik, geoBoundaries' province file, healthsites, Google Open Buildings if taken under
  ODbL). The same as for the US map: "© OpenStreetMap contributors", the data is under the ODbL, and a database built
  from it is offered under the ODbL.
- **Copernicus WorldDEM-30.** Free and open with fixed notices, as for Guyana. The notice begins "© DLR e.V. 2010-2014
  and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS", and changed data must say it was "produced
  using Copernicus WorldDEM-30".
- **CC BY 4.0** (ESA WorldCover; Google Open Buildings if taken under CC BY). Credit the publisher, link the licence and
  say if the data was changed.
- **CDLA Permissive 2.0** (Microsoft footprints, by its README).
- **CC BY-IGO** (OCHA's COD-AB). Credit OCHA and its source, the Royal Thai Survey Department.
- **DGA Open Government License 1.0** (10 June 2021; English text read in full). It gives a non-exclusive right, free
  of charge and without limit of territory or time, to copy, publish, distribute and process the data. The user must
  state the source at all times and must not change "substantive definitions" so that the data misleads. Logos,
  military insignia and third-party rights are excluded, and there is no warranty. It rests on the Digitalization of
  Public Administration and Services Delivery Act of 2019.
- **The labels on the portals.** The DGA terms say they bind any agency that publishes on data.go.th, yet only 5 of its
  44,567 datasets carry that label. 27,427 say "Open Data Common", 8,977 "Creative Commons Attributions" and 6,749
  "License not specified". None gives a version or a link, and "Open Data Common" does not say which Open Data Commons
  licence. No page was found that says which prevails. Until the maintainers decide, this proposal reads "Creative
  Commons Attributions" as credit required and treats "Open Data Common" as unclear.
- **data.bangkok.go.th.** Of 1,531 datasets: 1,289 "License not specified", 158 "Open Data Common", 60 "Creative
  Commons Attributions", 7 "DGA Open Government License", 5 non-commercial. No terms page for the whole portal was
  found. Bangkok's datasets are mirrored on data.go.th and still say "License not specified" there.
- **Non-commercial and no-derivatives labels** (the land use map, Bangkok's health centres, the Hydro-Informatics
  Institute's files). Not proposed for packs.

## How addresses are written

- **Levels.** Three are required: province; district (*amphoe*, or *khet* in Bangkok); subdistrict (*tambon*, or
  *khwaeng* in Bangkok). In rural areas a fourth, the village number (*moo*), is needed. The level words are optional
  and are written in English or Thai (Universal Postal Union addressing sheet for Thailand, September 2017; opened).
- **Order.** House number and road first, then subdistrict and district, then province and postcode, the same broad
  order as a US address. The sheet's examples: "491 Rangsit-Nakhon Nayok 4 Road, Prachathipat / Amphoe Tanyaburi,
  Pathumthani / 12130", and for a village "151 Moo 4, Tambon Paikongdin / Amphoe Bangplama, Suphanburi / 72150".
- **House numbers can hold a slash.** The sheet has "10/42", and Bangkok's own files have "34/40 ถนนแจ้งวัฒนะ
  แขวงทุ่งสองห้อง เขตหลักสี่ กรุงเทพฯ 10210". What the two parts mean was not checked; search should treat the whole
  string as the number.
- **Soi.** Addresses in Bangkok's files name a side street (*soi*, ซอย) as well as, or in place of, a road: "777 ซอย
  นวลจันทร์", "130/4 ถนนประชาราษฎร์ สาย 1 แยก 12".
- **Abbreviations.** Road is ถนน or ถ., soi is ซอย or ซ., moo is หมู่ or ม., and outside Bangkok the levels are
  shortened to ต., อ. and จ. Bangkok itself is written กรุงเทพมหานคร, กรุงเทพฯ or กทม. Village numbers also occur in
  outer Bangkok.
- **Postcode.** Five digits, written after the province. The sheet's diagram labels the leading part "province" and
  the rest "post office". That the split is two digits and three was seen only in a news article (search only;
  Thailand Post's own site was not reached).
- **Two scripts.** Official sources romanise the same name differently: "Pathumthani" and "Pathum Thani", "Klongtoey"
  and "Khlong Toei". The Royal Thai General System of Transcription is the official scheme and leaves out tones and
  vowel length (search only). Search needs Thai script as written, plus forgiving matching of Latin spellings.
- **Buddhist-era years.** Thai datasets date things in the Buddhist era: 2567 is 2024. Subtract 543. Titles shorten it
  further, as in "flood risk points 68" for 2568.
- **What the current code does with that.** `engine/address_search.py` reads a postcode as five digits, which fits.
  It expects the number before the street, which also fits. It would need to accept a slash inside the number, Thai
  script, and the soi and moo words.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md.

1. **Codes in setup.** Whether `TH-10` style codes are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup groups 77 Thai regions.
2. **The box rule**, as in REGIONS.md, and whether the official COD-AB boundary replaces the OSM-derived one used here.
3. **Bangkok and its five neighbours**: one map that holds all six, or six maps.
4. **Thai licence labels**: whether "Open Data Common" and "Creative Commons Attributions" with no version are
   acceptable for packs, and whether the DGA licence can be relied on for data.go.th datasets that carry another label.
5. **Unlicensed Bangkok layers**: whether to ask BMA to label its hospital, fire, police, drainage and flood files,
   and who asks.
6. **Search without address points**: place, road and soi search in two scripts, in place of house-number search.
7. **New help-point kinds**: shelters with capacity, pumping stations, floodgates and flood risk points, and how they
   map to the kinds `web/map.js` already draws.
8. **Language**: whether map labels and place names are stored in Thai, in Latin letters, or both. This ties to the
   language questions already open for other regions.

## What was checked, and what was not

- Opened on 17 November 2026: Copernicus' COP-DEM page, Geofabrik's Thailand page, ESA WorldCover's data access page,
  Google's Open Buildings page, Microsoft's footprints README and file index, Overture's attribution and address
  pages, the DGA Open Government License (English PDF), the National Statistical Office's draft area standard and
  Statistical Yearbook 2025 table 1.23, the Universal Postal Union sheet for Thailand, and the Department of Provincial
  Administration's subdistrict file.
- Read through public APIs on 17 November 2026: data.go.th, data.bangkok.go.th, catalog.disaster.go.th and
  opendata.gistda.or.th (licences, file lists and CSV headers), HDX (COD-AB, healthsites), geoBoundaries, and taginfo
  for `addr:housenumber`.
- Computed on 17 November 2026: the 77 boxes and the six-province box, from geoBoundaries' province file.
- Read a second time, separately: Geofabrik's file sizes and licence line, and the licence counts on
  data.bangkok.go.th. Both matched.
- Seen only in search results or on Wikipedia: the ISO 3166-2:TH list, the two-and-three split of the postcode, and
  the transcription system.
- Not checked: the boxes against COD-AB; ISO's own site (refused); Thailand Post's site; elevation data from the Royal
  Thai Survey Department and the Land Development Department; the land use files and any terms inside them; the
  attributes of the Department of Water Resources layers; building counts for Thailand; whether the shelter list
  covers Bangkok; the Thai FDA's drug premises file; Bangkok's fuel station geometry; the live health facility
  registry; and OSM counts for hospitals, pharmacies and fuel (taginfo timed out).
