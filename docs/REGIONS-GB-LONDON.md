# Detailed maps for London: a proposal

This is a proposal for discussion, not a decision. It answers, for Greater London, the questions [MAPS.md](MAPS.md)
asks before coverage can go beyond the United States: which open source replaces each federal list, under what
licence, what a "state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md) and
[REGIONS-DE.md](REGIONS-DE.md) and is meant to feed the same design discussion (issues #23, #25 and #31). The
machine-readable version is [regions-gb-london-proposed.json](regions-gb-london-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only. It covers London only. The rest of the United Kingdom is left for a later proposal.

**How things were checked.** Research was done on 17 November 2026 by an AI research agent reading the publishers' own
pages. The pages were read through a fetch tool that returns an extract of each page, not the raw page, and no person
has yet opened each source again. Each source carries one of three marks:

- **opened**: the dataset page, product page or the service's own answer was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site or catalogue record, but the page
  itself was not opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

Two findings shape the rest:

- **Britain has no open address file.** Overture's address theme has no rows for the United Kingdom, and Ordnance
  Survey's open products stop at the street and the postcode. See "Addresses".
- **Almost everything else is open under one licence.** Ordnance Survey, the Environment Agency, the Rural Payments
  Agency, the Office for National Statistics and the Home Office all publish under the Open Government Licence. See
  "Licence notes".

## What a region is

Greater London is the 32 London boroughs and the City of London. The Office for National Statistics (ONS) publishes it
as one of the nine regions of England, named "London". The proposal is one region for the whole of it, the same level
as a US state. The city-states in the other proposals are the nearest cases: Berlin in REGIONS-DE.md, Bangkok in
REGIONS-TH.md.

### Codes

ISO 3166-2:GB has no code for Greater London. It codes each borough on its own (`GB-CMD` Camden, `GB-BNE` Barnet and so
on), and `GB-LND` means the City of London, the single square mile at the centre, not the city most people mean. This
was read from Wikipedia's copy of the list (search only; the ISO site was not checked).

- The proposal is `GB-LON`. **This is not an ISO code.** It is made up here, in the ISO style, because `GB-LND` would
  be wrong and there is nothing else short.
- The official identifier is the ONS region code `E12000007`. The boundary file's feature service lists nine regions,
  `E12000001` North East to `E12000009` South West, with London seventh (opened). It is recorded in the JSON so a build
  can select the region by it.
- Neither `GB` nor `LON` is one of the entries in `STATE_CODES` (`engine/address_search.py`), so nothing collides with a
  US state.
- If the rest of England follows, the nine ONS regions are one consistent level to cut it by, and London is already one
  of them.

### Box

The box is the extent of the feature named "London" in ONS's **Regions (December 2024) Boundaries EN BFC** (full
resolution, clipped to the coastline at mean high water). It was read from the dataset's own feature service, asked
for the extent in WGS 84 (opened).

| Code | ONS code | Name | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|
| `GB-LON` | `E12000007` | London (Greater London) | -0.5160, 51.2788, 0.3414, 51.6976 | -0.67, 51.12, 0.50, 51.85 |

- The margin is the 0.15° that `map_sets.state` uses for US states, rounded outward to 0.01°.
- The source data is in British National Grid (EPSG:27700). The service did the conversion. If it converted the corners
  of the grid box and not every vertex, an edge can be off by a few thousandths of a degree. Recompute from the vertices
  before a build.
- London is small. The box is about 59 km by 47 km. At this latitude the margin adds about 10 km to the east and west
  and about 17 km to the north and south, which makes the box about 80 km by 80 km, well over twice the area. That is
  probably right for London: people who live just outside the boundary use the same hospitals, roads and rivers.
  Whether the M25 orbital motorway falls wholly inside the margin was not measured.

## Sources, layer by layer

"OGL" is the UK Open Government Licence version 3.0. "OS" is Ordnance Survey, Great Britain's mapping agency.

| Layer (file) | US source today | Proposed for London | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Base map and help points (`poi` rows) | OSM | OSM, Geofabrik's Greater London extract | OSM contributors | ODbL | extract page refused automated reading; its taginfo instance opened |
| Terrain (`terrain.sqlite`) | USGS 3DEP, 1 arc-second | Environment Agency LIDAR Composite DTM, 1 m, resampled to the size the app uses today; OS Terrain 50 as the simple fallback | Environment Agency; OS | OGL | LIDAR search only (the platform page is a JavaScript app); OS Terrain 50 opened |
| Water (`water.sqlite`) | NHD | OS Open Rivers for river lines; OSM water areas and reservoirs | OS; OSM contributors | OGL; ODbL | OS product list opened; OS Open Rivers' own page not opened |
| Dams | NID | OSM reservoirs and dams; no open inventory was looked for | OSM contributors | ODbL | not checked |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | Crop Map of England (CROME) 2024; allotments from OSM or OS Open Greenspace (see notes) | Rural Payments Agency; OSM contributors; OS | OGL; ODbL; OGL | CROME record opened, its class list not read |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | OSM buildings or Overture buildings; OS OpenMap – Local as a cross-check | OSM contributors; Overture; OS | ODbL; ODbL; OGL | OS product list opened; building coverage not measured |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | OS Open Names (settlements, roads, postcodes); Code-Point Open (postcode units); ONS borough names; OSM named places | OS; ONS; OSM contributors | OGL; OGL; ODbL | OS Open Names and Code-Point Open opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | **No open source for full addresses.** Street and postcode from OS Open Names and Code-Point Open; house numbers from OSM `addr:*` where they exist | OS; OSM contributors | OGL; ODbL | Overture guide opened; OSM counts read |

Notes:

- **Terrain.** London is low and nearly flat, so the fine detail matters more here than in most places: it decides which
  streets flood. The Environment Agency's LIDAR composite is a bare-earth model at 1 m. Its catalogue records give the
  licence as OGL, and the OpenStreetMap wiki gives the 2022 composite as covering more than 95 % of England (both search
  only). OS Terrain 50 is a bare-earth grid at 50 m for the whole of Great Britain, updated yearly (opened); that is
  coarser than the 30 m the US map uses. Copernicus GLO-30, proposed elsewhere, is a surface model: in a city its
  contours follow the roofs.
- **Crops.** CROME is about 32 million hexagonal cells for England, classed into more than 15 main crop types plus
  grassland and non-farm cover, made each year, and split for download by ceremonial county (opened).
  `tools/build_crops.py` keeps orchards, vineyards and berries. Whether CROME has those classes was not confirmed: its
  class list is in a spreadsheet that was not read. Inside London the food-growing land that matters is allotments. OSM
  has 881 of them in the Greater London extract, and OS Open Greenspace lists allotments among its kinds (opened).
  Whether an allotment belongs in the crops layer is a decision.
- **Buildings.** Microsoft's footprints for the UK were not checked, and REGIONS.md already raises which licence
  applies to them. No open building height data from OS was found in its open product list.
- **Places.** OS Open Names holds more than 870,000 named and numbered roads, nearly 44,000 settlements and more than
  1.6 million postcodes for Great Britain, updated quarterly (opened). Code-Point Open holds about 1.7 million current
  postcode units for Great Britain, also quarterly (opened). How many of either fall inside London was not counted.

### Addresses

This is London's largest gap, and it is the same for all of Great Britain.

- **Overture has no British addresses.** Its address guide for release 2026-10-21.0 lists 41 countries and about 475
  million addresses. `GB` is not among them (opened). `tools/build_addresses.py` reads only Overture, so today it would
  find nothing.
- **OS Open UPRN is points without words.** It gives every addressable location in Great Britain a number and a
  coordinate: `UPRN`, `X_COORDINATE`, `Y_COORDINATE`, `LATITUDE`, `LONGITUDE`, and nothing else (opened). There is no
  street, house number or postcode in it.
- **OS says so itself.** Its OS Open Names page says that work needing the full postal address should use its paid
  AddressBase products (opened).
- **OSM has some house numbers.** In the Greater London extract, 627,550 objects carry `addr:housenumber` and 668,125
  carry `addr:postcode` (taginfo, data until 16 November 2026 21:18 UTC, opened). How that compares with the true number
  of addresses in London was not measured.

So the proposal is a search that is honest about what it has:

1. **Postcode.** A British postcode unit covers a short stretch of street, so finding the postcode gets a person
   close. Code-Point Open gives a point for each one.
2. **Street.** OS Open Names gives named roads.
3. **House.** An exact house only where OSM has that number on that street. `find_addresses` already promises "never a
   guessed house"; that rule would stay.

## Help points

OSM is the practical source. Counts from taginfo for Geofabrik's Greater London extract, data until 16 November 2026
21:18 UTC (opened):

| Tag | Count | Notes |
|---|---|---|
| `amenity=pharmacy` | 1,290 | |
| `amenity=hospital` | 200 | |
| `amenity=police` | 134 | |
| `amenity=fire_station` | 111 | 105 are drawn as buildings and 6 as points |
| `amenity=drinking_water` | 560 | |
| `landuse=allotments` | 881 | |

The extract's clipping line was not read, so the counts may include places just outside the boundary.

Official lists that were looked at:

- **Fire stations.** The Home Office publishes a dataset of fire stations in England with name, address, postcode and
  grid coordinates, under OGL v3.0. Its guidance note counts 1,398 stations, as of July 2020 (opened). It is six years
  old, and London's rows were not counted. It would serve as a cross-check on OSM, not as the source.
- **Hospitals, GPs, pharmacies, dentists.** The NHS website offers these lists only on request by email, or through a
  feed that needs a developer account (opened). A list that has to be asked for does not suit a build anyone can
  repeat. NHS England's organisation codes were not looked at.
- **Cool Spaces.** The Greater London Authority publishes the places where people can shelter on very hot days, with
  seating and free drinking water (CSV, GeoPackage and GeoJSON, last updated 11 December 2025). The page states no
  licence, only a copyright line (opened). A dataset with no stated licence is treated here as not yet usable, as in
  REGIONS-AR.md and REGIONS-TH.md. It is worth asking the publisher.

One London kind of information is worth a decision:

- **Flood areas.** The Thames through London is tidal. The Environment Agency publishes Flood Warning Areas: the areas
  where it expects flooding and gives a warning service, from rivers, the sea and in places groundwater. They are under
  OGL v3.0, revised 9 July 2025, and come as GeoPackage, GeoJSON and Shapefile (opened). Its "Risk of Flooding from
  Rivers and Sea" map, in 50 m cells, is listed under OGL too (search only). The areas are fixed shapes that fit an
  offline map. The warnings themselves are live and do not. This would be a new kind of layer, so it is a question, not
  a proposal.

## Licence notes and attribution

- **OGL v3.0** (OS, Environment Agency, Rural Payments Agency, ONS, Home Office). OS's open data page says its open
  products are for "unrestricted, free commercial and personal reuse" under OGL version 3 (opened). The licence text
  itself could not be opened on the day (the National Archives page returned an error), so what it asks for is taken
  from the publishers' pages:
  - OS products: "Contains OS data © Crown copyright and database right" with the year (search only, from OS's support
    page).
  - Environment Agency: "© Environment Agency copyright and/or database right 2025. All rights reserved." (opened, on
    the Flood Warning Areas record).
  - Rural Payments Agency: "© Rural Payments Agency copyright and/or database right 2024. All rights reserved."
    (opened, on the CROME record).
  - ONS boundaries: the record says the file contains both Ordnance Survey and ONS intellectual property rights (search
    only).
- **Code-Point Open** needs two more lines, for Royal Mail and for National Statistics data (search only, from a
  council's guide to OS open data; OS's own wording was not opened).
- **ODbL** (OSM, Overture buildings). As in REGIONS.md. The US map already carries ODbL data.
- **Not open, so not proposed:** Royal Mail's Postcode Address File and OS's AddressBase (full addresses), and OS's
  larger-scale and height products outside the open list.

These notices would belong wherever the map already credits its sources.

## How addresses are written

A British address is a house number and street, then the post town, then the postcode on its own line.

- **The postcode is letters and digits in two parts.** OS's Code-Point guide gives six valid shapes (opened):

  | Outward part | Inward part | Example | Characters with the space |
  |---|---|---|---|
  | AN | NAA | M2 5BQ | 6 |
  | ANN | NAA | M34 3AB | 7 |
  | AAN | NAA | DN5 7XY | 7 |
  | AANN | NAA | DN16 9AA | 8 |
  | ANA | NAA | W1A 4WW | 7 |
  | AANA | NAA | EC1A 1HQ | 8 |

  The outward part is two to four characters and the inward part is always three. The last two shapes, with a letter
  after the digit, are used in central London districts such as W1, EC1 to EC4, WC and SW1 (search only).
- **People type it loosely.** `sw1a1aa`, `SW1A 1AA` and `sw1a 1aa` are the same postcode. Search would have to accept
  all three.
- **Flats and named houses.** Many London addresses start with "Flat 3" or a building name, not a number. That part
  comes from general knowledge and was not checked against a source.
- **The post town is not always London.** Outer boroughs often use another post town and postcode area, such as
  Croydon (CR) or Romford (RM), and people there may write a county, not "London". This too is general knowledge and
  was not checked. It means a search that expects the word "London" would miss a large share of London.

## Still undecided

Each of these needs the maintainers' decision before any code changes:

1. **A code that is not ISO.** Whether `GB-LON` is acceptable, or whether the id should be the ONS code, or whether
   London should wait for a scheme for the whole United Kingdom. And, as REGIONS.md asks, whether a hyphenated code can
   be a manifest `id`, `map-set.json`'s `name` and part of `Lastbook-Map-<id>.zip`.
2. **The margin.** Whether 0.15° is right for a region this small, where it more than doubles the area.
3. **Address search without addresses.** Whether a British region may ship a postcode and street finder in place of
   an address index, with exact houses only where OSM has them.
4. **Postcodes in the code.** `engine/address_search.py` reads a postcode only as five digits (`\d{5}`), and treats a
   query as an address only when it starts with a digit, so "Flat 3, 12 …" is not one. `tools/build_addresses.py` keeps
   only `country = 'US'` and cuts postcodes to five characters, which would turn `SW1A 1AA` into `SW1A` and a space. The
   street words in `WORDS` are American short forms; British street names also end in Close, Gardens, Mews, Crescent,
   Grove and Way, which have no entry.
5. **State names.** Address search looks for a US state name at the end of a query. A London query ends in a post town
   or a postcode.
6. **Allotments.** Whether they belong in the crops layer, in a layer of their own, or nowhere.
7. **Flood areas.** Whether Lastbook wants a flood layer at all, and what it would say about its age.
8. **The California-only layers.** As in REGIONS.md: the fish, boating and well layers would stay empty.

## What was checked, and what was not

- **Opened:** the ONS feature service's extent for London and its list of the nine regions and their codes; Overture's
  address guide; OS's open data product list and its pages for OS Terrain 50, Code-Point Open, OS Open Names, OS Open
  UPRN and the Code-Point postcode shapes; the data.gov.uk record for CROME 2024; the Environment Agency's Flood Warning
  Areas record; the Home Office fire stations guidance note; the NHS website datasets page; the London Datastore record
  for Cool Space Data 2025; taginfo's answers for the Greater London extract.
- **Search only:** the Environment Agency LIDAR composite's licence and coverage; the ISO 3166-2:GB list (Wikipedia's
  copy); which districts use the two central London postcode shapes; the attribution lines for OS products and
  Code-Point Open; the licence of "Risk of Flooding from Rivers and Sea".
- **Not checked:** the text of the Open Government Licence v3.0; Geofabrik's Greater London page and its `.poly` file
  (the site refuses automated reading); CROME's class list; OS Open Rivers, OS OpenMap – Local and OS Open Greenspace
  beyond their one-line entries in OS's list; Microsoft's and Overture's building coverage for London; any open
  inventory of dams or reservoirs; Metropolitan Police and London Fire Brigade station lists; how many postcodes, roads
  and addresses London has.
- The taginfo counts were read through a tool that reformats the service's answer. The numbers are as it returned them.
- No file was downloaded and no build was run. The box is the only figure computed here, and it is the service's own.
