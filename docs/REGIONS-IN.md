# Detailed Maps for India: A Proposal

This is a proposal for discussion, not a final decision. It answers, for India, the questions that [MAPS.md](MAPS.md) and [REGIONS.md](REGIONS.md) pose before detailed offline map coverage can expand beyond the United States:
1. Which open and permissible sources replace each US federal dataset?
2. Under what licence?
3. What constitutes a "state" / region?
4. How addresses and postal codes are structured?
5. How boundaries and regional policies are treated?

Nothing in this document immediately alters the application codebase, engine, or build pipelines. It aligns with existing country proposals ([REGIONS-AR.md](REGIONS-AR.md), [REGIONS-DE.md](REGIONS-DE.md), [REGIONS-LK.md](REGIONS-LK.md), [REGIONS-TH.md](REGIONS-TH.md)) and feeds the shared map discussion (issues #23, #25, #31, and #96).

---

## 1. What a Region is: Nationwide vs. State-Wise

### Whole-Country vs. State Division
India encompasses approximately 3.287 million km² and over 1.4 billion residents. 

* **Whole-Country (`IN`):** Packaging nationwide road geometry, 30 m elevation raster tiles, all building footprints, water bodies, and points of interest into a single archive would yield an enormous download (tens of gigabytes of SQLite data). This exceeds the storage and memory capacity of typical offline installations and conflicts with the project's principle of modular, lightweight packs.
* **State-Wise (Recommended):** India is administratively divided into **28 States** and **8 Union Territories** (36 regional units in total). Packaging map sets state-by-state directly mirrors the US state map architecture (`packaging/build_packs.py map <ST>` and `packaging/state_maps.py`).

### Regional Codes (ISO 3166-2:IN)
In the US, two-letter postal codes are used (e.g. `CA`, `TX`, `NY`).
* A bare two-letter country code `IN` collides directly with **Indiana** in `STATE_CODES` ([engine/address_search.py](../engine/address_search.py)), `Lastbook-Map-IN.zip`, and `derived/geo/addresses/IN.sqlite`.
* Therefore, all Indian regional packages should use standard **ISO 3166-2:IN** codes with the `IN-` prefix:
  - `IN-MH`: Maharashtra
  - `IN-KA`: Karnataka
  - `IN-DL`: National Capital Territory of Delhi
  - `IN-TN`: Tamil Nadu
  - `IN-UP`: Uttar Pradesh
  - `IN-GJ`: Gujarat
  - `IN-WB`: West Bengal
  - *(and remaining 29 states and territories)*

---

## 2. Sample Placeholder Bounds

The coordinates in the table below are **preliminary sample placeholder bounds** provided to illustrate coverage areas. As established in [REGIONS.md](REGIONS.md), final tight bounding boxes should be computed from official administrative boundary polygons (such as Survey of India or OCHA COD-AB Level 1) with an added 0.15° margin before building production packages.

| Code | Name | Type | Sample Placeholder Box (W, S, E, N) | Sample Box with 0.15° Margin | Notes / Context |
|---|---|---|---|---|---|
| `IN-DL` | Delhi NCT | Union Territory / Capital | 76.838, 28.404, 77.348, 28.883 | 76.68, 28.25, 77.50, 29.04 | Enclave surrounded by Haryana and UP |
| `IN-MH` | Maharashtra | State | 72.639, 15.606, 80.898, 22.028 | 72.48, 15.45, 81.05, 22.18 | Central-western coast and plateau |
| `IN-KA` | Karnataka | State | 74.054, 11.593, 78.588, 18.450 | 73.90, 11.44, 78.74, 18.60 | Southern plateau and Malabar coast |
| `IN-TN` | Tamil Nadu | State | 76.230, 8.068, 80.347, 13.565 | 76.08, 7.91, 80.50, 13.72 | Coromandel coast and southernmost tip |
| `IN-GJ` | Gujarat | State | 68.106, 20.126, 74.476, 24.712 | 67.95, 19.97, 74.63, 24.87 | Western coast, peninsulas and Rann |
| `IN-WB` | West Bengal | State | 85.826, 21.539, 89.882, 27.221 | 85.67, 21.38, 90.04, 27.38 | Bay of Bengal coast north to Himalayas |

*(Enclave note: City-state territories such as Chandigarh or Delhi overlap neighboring regional boxes; bounding box queries naturally pull in adjacent roads for continuous navigation).*

---

## 3. Sources, Layer by Layer

Every database file inside `derived/geo/` requires an open, legally permissible replacement for its US data source:

| Layer (File) | Current US Source | Proposed Source for India | Publisher | Licence & Link | Status / Verification |
|---|---|---|---|---|---|
| **Base Map** (`national.sqlite`, `map.sqlite`) | OpenStreetMap US extract | Geofabrik India OSM extract (`india-latest.osm.pbf` or zonal extracts) | OpenStreetMap contributors via Geofabrik | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | **Verified.** Geofabrik India extract and ODbL 1.0 licence checked. |
| **Points of Interest** (`poi` table) | OpenStreetMap US POIs | OpenStreetMap India POIs (`amenity=hospital`, `pharmacy`, `police`, `fire_station`, `fuel`, `water_point`, `shelter`) | OpenStreetMap contributors | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | **Verified.** OSM POI tags and ODbL 1.0 licence checked. |
| **Gazetteer / Places** (`places.sqlite`) | USGS GNIS, US Census Gazetteers | OSM named places (`place=city`, `town`, `village`, `suburb`) + India Post PIN Code directory ([All India Pincode Directory](https://data.gov.in/resource/all-india-pincode-directory-till-last-month)) + OCHA COD-AB | OSM contributors; India Post / NIC; OCHA | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/); [GODL India](https://data.gov.in/government-open-data-license-india); pending (OCHA COD-AB) | **Proposed / pending verification.** Would let `/api/places` find towns, districts, villages and 6-digit PIN codes once the shared postcode design (section 4) is implemented. |
| **Terrain & Elevation** (`terrain.sqlite`) | USGS 3DEP (10–30 m) | Copernicus DEM GLO-30 (30 m global raster) or NASA SRTM / NASADEM | ESA / Airbus; NASA | [Copernicus WorldDEM-30](https://spacedata.copernicus.eu/documents/20123/122407/Copernicus_WorldDEM_30m_License.pdf); [Public Domain](https://earthdata.nasa.gov/data/open-data) | **Verified.** Copernicus DEM GLO-30 source and licence checked (Copernicus WorldDEM-30). |
| **Buildings** (`buildings.sqlite`) | Microsoft US Footprints + OSM heights | Microsoft Global ML Building Footprints (India) or Google Open Buildings (South Asia) | Microsoft; Google | [CDLA Permissive 2.0](https://github.com/microsoft/GlobalMLBuildingFootprints); [CC BY 4.0](https://sites.research.google/open-buildings/) | **Verified.** Microsoft Global ML Building Footprints repository and CDLA Permissive 2.0 licence checked. |
| **Water & Reservoirs** (`water.sqlite`) | USACE NID & USGS NHD | OSM water layers (`natural=water`, `water=reservoir`, `waterway=dam`, `waterway=river`) + Central Water Commission register | OSM contributors; CWC India | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/); Government data (pending) | **Partial / Pending verification.** OSM water features and ODbL 1.0 licence checked; dedicated CWC machine-readable open reuse terms are pending verification. |
| **Crops & Land Cover** (`crops.sqlite`) | USDA Cropland Data Layer (CDL) | ESA WorldCover 2021 (10 m global land cover) | ESA WorldCover consortium | [CC BY 4.0](https://worldcover2021.esa.int/) | **Verified (Partial replacement).** ESA WorldCover source and CC BY 4.0 licence checked; distinguishes vegetation and cropland, but lacks individual crop distinction. |
| **Address Indexes** (`addresses/<ID>.sqlite`) | Overture Maps address theme | Overture Maps (where present) + OSM address tags | Overture Maps Foundation; OSM contributors | Per source, pending ([Overture Attribution](https://docs.overturemaps.org/attribution/)); [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | **Pending verification / Data gap.** Door-to-door address numbers are sparse in open data. Locality and town search via `/api/places` is the primary mechanism. |

---

## 4. Addressing & Postal Requirements (Feeding Shared Design)

Detailed UI changes and parser refactoring are left to the shared internationalization design effort (issues #23, #25, and #31). However, the specific structural requirements for India are:

### Core Requirement: Six-Digit PIN Support with US ZIP Preservation
* **Indian PIN Codes:** India's Postal Index Number (PIN) system uses **6 digits** (e.g., `110001` New Delhi, `400001` Mumbai, `560001` Bengaluru, `600001` Chennai).
* **Preserving US ZIPs:** The current address search engine in [engine/address_search.py](../engine/address_search.py) expects 5-digit US ZIP codes (`\b\d{5}\b`).
* **Design Requirement:** Address search and gazetteer regexes must support 6-digit Indian PIN codes while fully preserving existing 5-digit US ZIP behavior without ambiguity or regressions.

### Address Structure in Practice
* Indian addresses follow a hierarchical descriptive format:
  `[Flat/Door No.], [Building/Society Name], [Cross/Main Road or Street], [Landmark], [Locality/Area], [City/Town/Taluk], [State] - [6-digit PIN]`
* Because door-to-door street numbering is uncommon outside planned colonies, search relies primarily on place names, landmarks, localities, and PIN codes handled by `/api/places`, with address search operating on a best-effort basis.

---

## 5. Disputed and Sensitive External Boundaries: An Open Design Question

As Lastbook expands internationally, handling disputed or sensitive international boundaries is a recognized open question (highlighted in [REGIONS.md](REGIONS.md) item 6 and [REGIONS-DE.md](REGIONS-DE.md) item 7 regarding Lake Constance).

### Context & Primary Sources
In India, the depiction of external national boundaries (particularly in Jammu & Kashmir, Ladakh, and Arunachal Pradesh) is subject to specific statutory guidelines:
* **The Criminal Law Amendment Act, 1961 (Act No. 23 of 1961):** [Primary text via India Code](https://www.indiacode.nic.in/bitstream/123456789/6798/1/criminal_law_amendment_act_1961.pdf) (Section 2: Questioning territorial integrity or frontiers). Its current statutory status, subsequent amendment history, and practical enforcement scope regarding offline international software distributions have not been independently confirmed; it is cited here as reference context rather than an established technical requirement.
* **National Geospatial Policy (2022):** [DST Notification PDF hosted by Survey of India](https://surveyofindia.gov.in/UserFiles/files/National%20Geospatial%20Policy.pdf), Government of India.
* **Survey of India Boundary Guidelines & Official Maps:** [Survey of India Portal](https://surveyofindia.gov.in).

### Open Decision for Maintainers
* Standard global OpenStreetMap extracts depict de facto control / Lines of Control (LoC / LAC).
* The maintainers must decide on the shared policy for all international regions:
  1. Whether regional extracts for India should clip to official Survey of India boundary polygons.
  2. Or display administrative state/territory lines with appropriate contextual disclaimer notices.

---

## 6. Licences & Required Attributions

Redistribution within Lastbook requires adding attribution notices in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and the app's *Sources & Permissions* screen:
* **OpenStreetMap Data:** `© OpenStreetMap contributors, ODbL 1.0` (https://opendatacommons.org/licenses/odbl/1-0/)
* **Copernicus DEM GLO-30:** `Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA.`
* **Microsoft Global ML Footprints:** `Microsoft Open Data, licensed under CDLA Permissive 2.0.`
* **Government Open Data (GODL India / Data.gov.in):** `National Data Sharing and Accessibility Policy (NDSAP) - Government of India.`
