# Detailed maps for Denmark: a proposal

This is a proposal for discussion, not a decision. It answers, for Denmark, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS-DE.md](REGIONS-DE.md),
[REGIONS-TH.md](REGIONS-TH.md) and [REGIONS-FR.md](REGIONS-FR.md) and is meant to feed the same design discussion (issue
#31). The machine-readable version is [regions-dk-proposed.json](regions-dk-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026 by reading the publishers' own pages and public APIs,
without an account. Region boxes were computed from the boundary files, populations were read from Danmarks Statistik's
API, extract sizes came from HTTP HEAD requests, and what the engine does with Danish addresses was found by calling
its functions. Each source carries one of three marks:

- **opened**: the dataset page, licence page, API answer or download listing was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read, or the question was not looked at; the row says what is
  missing.

## Why Denmark is a different case

Like France, most Danish layers have one national source under one licence: since 16 May 2024 the free geographic and
basic data of the Danish mapping agency (elevation, boundaries, buildings, water, place names and addresses) are under
CC BY 4.0. Two things changed in 2026, and they shape the rest of this proposal:

- **DAWA closed on 1 October 2026.** DAWA was the free, account-free API that most open Danish tooling used for
  addresses and boundaries. Its endpoints (`api.dataforsyningen.dk/regioner`, `/kommuner`, `/adresser`, and
  `dawa.aws.dk`) now answer HTTP 410 Gone (opened). The agency's notice of 2 July 2026 names the replacements:
  Adressevælger for address lookup and Datafordeler for everything else (opened).
- **Datafordeler needs a key.** Its boundary WFS and GraphQL services answer 401 without one (opened). A key is free
  with a login and lasts two years (search only). The elevation model, GeoDanmark and place names are listed as
  needing a key too (opened for the elevation model). A build machine can hold a key; the app never needs one,
  because data comes in through a build tool and ships as a file.

The agency's name also changes. SDFI became Klimadatastyrelsen on 14 August 2024, and Klimadatastyrelsen merges with
DMI on 1 December 2026 into "DMI, Kort og Grunddata" (opened). Credit lines written now will need the new name.

## What a region is

Denmark has 5 regions, made of 98 municipalities (*kommuner*). The proposal is one map region per region, 5 in all,
the level closest to a US state. The regions run health care, which matters here: each has its own number for the
out-of-hours doctor (see "Help points").

Greenland and the Faroe Islands are parts of the Danish realm with home rule. Geofabrik, Overture and the Danish
address register all keep them apart from Denmark (opened), and they are not proposed here. Ertholmene (Christiansø),
east of Bornholm, is outside the municipal division and run by the Ministry of Defence (lex.dk, an encyclopedia; opened), but Danmarks
Statistik counts it in Region Hovedstaden (code 411, 89 people), and so does this proposal.

### Codes

ISO 3166-2:DK gives each region two digits after `DK-`: `DK-81` Nordjylland, `DK-82` Midtjylland, `DK-83` Syddanmark,
`DK-84` Hovedstaden, `DK-85` Sjælland (search only: the ISO site refused automated reading, as REGIONS.md and
REGIONS-TH.md also note).

- **The digits are the national code.** They are the last two digits of the DAGI and CPR region codes 1081 to 1085,
  valid since 1 January 2007, and StatBank's 081 to 085 (Danmarks Statistik, opened). Danish data already uses them.
- **No collision with US codes.** A bare `DK` is not in `STATE_CODES` (`engine/address_search.py`).
- **The part after the hyphen is two digits, not two letters.** The engine accepts an address index only under a
  two-letter name: `engine/setup/manifest.py` line 72 and `engine/setup/install.py` line 267 both require `[A-Z]{2}`.
  This is the same question REGIONS-TH.md raises for `TH-10`, and one answer would serve both.

### Boxes

Each box is the extent of every vertex of the region in **Eurostat GISCO's NUTS 2024 level 2 file at 1:1 million**
(`https://gisco-services.ec.europa.eu/distribution/v2/nuts/distribution/DK0{1..5}-region-01m-4326-2024.geojson`;
NUTS level 2 in Denmark is the five regions; opened). Each box was then widened by 0.15° and rounded outward to 0.01°,
the margin `map_sets.state` uses for US states.

The limits of the method:

- GISCO's boundaries are credited "© EuroGeographics for the administrative boundaries", and its terms are read as
  non-commercial (search only). A box is four numbers, but before a build the boxes should be recomputed from DAGI,
  the national boundary register under CC BY 4.0, which now needs a Datafordeler key.
- A cross-check against OpenStreetMap's region relations (through Nominatim; ODbL) agrees within about 0.03° on every
  edge, except that OSM's Region Hovedstaden ends at 15.157° E and leaves out Ertholmene.

| Code | DAGI code | Name | Municipalities | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|---|
| `DK-81` | 1081 | Region Nordjylland | 11 | 8.2227, 56.5511, 11.1979, 57.7512 | 8.07, 56.40, 11.35, 57.91 |
| `DK-82` | 1082 | Region Midtjylland | 19 | 8.0989, 55.6700, 11.6446, 56.8468 | 7.94, 55.52, 11.80, 57.00 |
| `DK-83` | 1083 | Region Syddanmark | 22 | 8.0781, 54.7246, 10.9545, 55.9541 | 7.92, 54.57, 11.11, 56.11 |
| `DK-84` | 1084 | Region Hovedstaden | 29, and Ertholmene | 11.6958, 54.9876, 15.1943, 56.2008 | 11.54, 54.83, 15.35, 56.36 |
| `DK-85` | 1085 | Region Sjælland | 17 | 10.8896, 54.5625, 12.5540, 55.9964 | 10.73, 54.41, 12.71, 56.15 |

The municipalities of each region are listed in the JSON.

### One place that needs a decision: Bornholm

Bornholm, with 38,484 people, belongs to Region Hovedstaden but lies about 150 km east of Copenhagen (Rønne to the city hall), past the south of
Sweden. It makes the region's box 3.8° wide. Split in two, the region looks like this:

| Part | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|
| Hovedstaden west of 14° E (north-east Zealand) | 11.6958, 55.5552, 12.7913, 56.2008 | 11.54, 55.40, 12.95, 56.36 |
| Bornholm and Ertholmene | 14.6864, 54.9876, 15.1943, 55.3261 | 14.53, 54.83, 15.35, 55.48 |

The single box holds most of Skåne in Sweden: Malmö, Lund, Helsingborg, Landskrona, Trelleborg, Ystad and Kristianstad
fall inside it (tested against town coordinates). The Denmark extract stops at the Danish border, so Sweden would be
blank in a map built from it, not mapped; but a source cut by box would pick up Swedish rows. Three options:

- **one map, `DK-84`, cut by the region's outline** rather than its box, so the box is used only for display and the
  spatial index, as REGIONS-FR.md proposes for France;
- **two maps**, north-east Zealand and Bornholm, each with its own small box and id; or
- **Bornholm as an extra download** next to `DK-84`.

This proposal suggests the first, because the region is one unit for health care and emergency numbers.

### Boxes that reach another country, or each other

A state map holds every row inside its box. Tested against town coordinates:

- `DK-84` covers most of Skåne, as above.
- `DK-85` covers Helsingborg in Sweden and the north of Fehmarn in Germany. It also holds Copenhagen and most of
  Hovedstaden west of 14° E, the same way Brandenburg's box holds Berlin in REGIONS-DE.md.
- `DK-83` covers Flensburg and the island of Sylt in Germany.
- `DK-82`'s box holds Vejle, which is in `DK-83`.

The Denmark extract's outline (`denmark.poly`, 80 points; opened) has Christiansø inside it and Malmö, Helsingborg,
Ystad, Flensburg and Kiel outside, so foreign rows come only from sources cut by box.

### Size of each region

Population is Danmarks Statistik's table FOLK1A for 1 October 2026 (2026Q4, updated 10 November 2026; read through
`https://api.statbank.dk/v1/data`, opened). The five regions add up to the country's total, 6,044,001.

| Code | Name | Municipalities | Population, 1 October 2026 |
|---|---|---|---|
| `DK-81` | Region Nordjylland | 11 | 594,293 |
| `DK-82` | Region Midtjylland | 19 | 1,389,638 |
| `DK-83` | Region Syddanmark | 22 | 1,245,181 |
| `DK-84` | Region Hovedstaden | 29 | 1,954,759 |
| `DK-85` | Region Sjælland | 17 | 860,130 |

### OpenStreetMap extract

Geofabrik has one extract for Denmark and no sub-regions (opened; data up to 2026-11-16T21:22:36Z). Every region map
would be cut from it, as PR #80's tool does for Bangkok. Sizes from HEAD requests on 17 November 2026 (opened):

| File | Bytes |
|---|---|
| `denmark-latest.osm.pbf` (dated 17 November; its MD5 matched Geofabrik's `.md5`) | 498,163,345 |
| `denmark-latest-free.gpkg.zip` (dated 16 November) | 841,513,543 |
| `denmark-latest-free.shp.zip` (dated 16 November) | 814,578,465 |

Two open pull requests already cut maps from this extract: #84 lists all of Denmark as `eu-dk`, boxed by Geofabrik's
outline (7.7011, 54.4406, 15.6545, 58.0624), and #35 has a Copenhagen box, `dk-kob` (12.26, 55.38, 12.86, 55.98).

## Sources, layer by layer

These hold for the whole country. The detail is in the JSON.

| Layer (file) | US source today | Proposed for Denmark | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | Danmarks Højdemodel, DHM/Terræn, 0.4 m grid in 10 km tiles | Klimadatastyrelsen | CC BY 4.0 | opened |
| Water (`water.sqlite`) | NHD | GeoDanmark lakes (`Sø`) and watercourse centre lines (`Vandløbsmidte`) | Klimadatastyrelsen and the municipalities | CC BY 4.0 | licence opened; object pages search only |
| Dams | NID | No dam register; coastal dikes from Kystbeskyttelsesanlæg instead | Kystdirektoratet | CC BY 4.0 (metadata) | metadata opened; the WFS failed |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | Marker 2026, declared field parcels with crop code | Landbrugsstyrelsen | none found | download opened; licence not found |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | GeoDanmark `Bygning` outlines; heights from OSM | Klimadatastyrelsen | CC BY 4.0 | opened |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | Danske Stednavne, about 140,000 names; OSM | Klimadatastyrelsen | CC BY 4.0 | opened |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | DAR through Datafordeler; Overture (from DAR, March 2026) as alternative | Klimadatastyrelsen; Overture | CC BY 4.0 | opened |
| Points of interest (`poi` rows) | OSM | OSM, as today | OSM contributors | ODbL | opened |

Notes:

- **Terrain.** 0.4 m is far finer than zoom 12, the deepest zoom `tools/build_terrain.py` writes, so it would be
  resampled. About a fifth of the country is flown again each year (opened). The size of the whole-country download
  was not obtained: Dataforsyningen's pages need JavaScript.
- **Water.** Denmark is low and flat; its water risk is storm surge and coastal flooding more than dam failure.
  Kystdirektoratet's dike layer is the nearer equivalent of the NID, but it is described as "not dimension-true" and
  `water.sqlite` has no kind for a dike. Its flood-risk areas and a 40 cm watercourse-flood grid can be downloaded
  (search only; licence not checked).
- **Crops.** `Marker_2026.zip` (360,175,074 bytes, last modified 17 November 2026) downloads without an account, and
  years back to 2008 are listed, but no licence was found for it, so it is not yet usable. `Markblokke_2026.zip`
  answered 404. Which crop codes are orchards, berries and vines was not mapped.
- **Buildings.** GeoDanmark's `Bygning` has outlines, a building type and a link to BBR, but no height
  (object catalogue, opened). BBR, the building register, has storeys and construction year but no height either
  (search only). Heights would come from OSM, or from the surface model minus the terrain model.
- **Places.** Danske Stednavne has not been updated since September 2025 (opened).
- **Addresses.** DAR, the national address register, is under CC BY 4.0 ("Som bruger af frie grunddata er du underlagt
  CC BY 4.0", Datafordeler's terms of 16 May 2024; opened). Overture has 3,933,282 Danish addresses (release
  2026-10-21.0; opened). They come from OpenAddresses' `sources/dk/countrywide.json`, a single upload of 27 March 2026
  drawn from DAR (opened). With DAWA closed, that copy will not refresh by itself, and whether anyone will refresh it
  was not found. For a map that may be used for years, DAR directly is the safer source.

## Help points

OpenStreetMap stays the base. Counts for the Denmark extract (taginfo, data until 2026-11-16T21:17:39Z; opened):

| Tag | Count |
|---|---|
| `amenity=pharmacy` | 546 |
| `amenity=hospital` | 193 |
| `amenity=fire_station` | 256 |
| `amenity=police` | 154 |
| `amenity=drinking_water` | 1,022 |
| `emergency=defibrillator` | 2,775 |
| `emergency=siren` | 38 |
| `amenity=shelter` | 7,844 |
| `military=bunker` | 2,201 |

Over half of the shelters are lean-tos at nature camping sites (*shelterpladser*): 4,049 carry
`shelter_type=lean_to`, 1,841 are bus shelters and 1,455 picnic shelters. They are useful in an emergency, but they are
not the shelters a reader may expect from the name. PR #80's tool drops the bus shelters and keeps the rest under one
class, so a Danish map would need a word for them.

National lists that are **not open**:

- **Defibrillators.** hjertestarter.dk (TrygFonden) is the national register, but its terms allow reuse only by prior
  agreement (opened). OSM's 2,775 are the open alternative.
- **Warning sirens.** Beredskabsstyrelsen has about 1,000 sirens, covering about 80 % of the urban population, and
  publishes no list of where they are (page of 7 April 2025; opened). OSM has 38.
- **Shelters (*sikringsrum*).** No public list. A national survey by the agency for civil security and the
  municipalities began on 16 September 2026 and is due to finish in 2027 (opened).

**Emergency numbers.** 112 for ambulance, fire and police, and 114 for police that is not urgent (politi.dk; opened).
For a doctor out of hours each region has its own number, so a regional map is the right place to carry it:

| Region | Out-of-hours doctor | Checked |
|---|---|---|
| `DK-81` Nordjylland | 70 15 03 00 | opened |
| `DK-82` Midtjylland | 70 11 31 31 | opened |
| `DK-83` Syddanmark | 70 11 07 07 | opened |
| `DK-84` Hovedstaden | 1813 (Akuttelefonen, 24 hours) | search only |
| `DK-85` Sjælland | 1818 | opened |

## Licence notes and attribution

- **CC BY 4.0** (Klimadatastyrelsen: DAGI, the elevation model, GeoDanmark, Danske Stednavne, DAR; opened). It has
  applied since 16 May 2024 and replaced the 2022 "Vilkår for brug af frie geografiske data". Datafordeler's terms page
  asks only "Du skal kreditere Klimadatastyrelsen på et passende sted" (credit Klimadatastyrelsen in a suitable place)
  and gives no wording. The 2022 text fixed one, "Indeholder data fra Styrelsen for Dataforsyning og Infrastruktur,
  [dataset], [month year]", which Overture still links to. A credit with the dataset and its date, in that shape, fits
  both. From 1 December 2026 the agency is "DMI, Kort og Grunddata". No share-alike.
- **ODbL** (OSM). As for the US map. The app and the packs have no link to the ODbL text today, as REGIONS-FR.md notes.
- **GISCO** (the region boxes only): "© EuroGeographics for the administrative boundaries". Not proposed for any layer.
- **Not open**: hjertestarter.dk; the Marker crop parcels until a licence is found.

As in France, CC BY points merged with OSM points in one `poi` table probably make a derived database under the ODbL; one
file or table per licence avoids that (a question, not legal advice). `MAP_CREDIT` in `packaging/build_packs.py` is a
fixed US list.

## How addresses are written

- **Order.** Street name first, then the house number, then floor and door, then the postcode and town:
  "Rådhuspladsen 1, 1550 København V", or with a flat, "Nørrebrogade 20, 2. th, 2200 København N". A supplementary town
  name (*supplerende bynavn*), naming a village inside a postal area, goes on its own line between the street line and
  the postcode line (danmarksadresser.dk, the register's rules; opened).
- **House number.** 1 to 999, optionally followed by a capital letter with no space ("12B"). I, J, O and Q are not used
  in new numbers (opened). In the address data every number is digits (3,309,201) or digits and a letter (624,205).
- **Floor and door.** `st` is the ground floor, then 1 to 99; `kl` the basement. The door is `tv` (left), `th` (right) or
  `mf` (middle), or a number counted from the left (opened). 1,483,234 of 3,933,406 addresses have a floor or door.
- **Postcode.** Four digits, 1050 to 9990 in the data. Postcodes have "ingen automatisk sammenhæng" (no automatic
  connection) with administrative boundaries (opened). In the OpenAddresses copy of DAR (27 March 2026; 1,089
  postcodes), 38 cross a region boundary; the largest are 7100 Vejle, with 921 addresses in Midtjylland, and 9500 Hobro,
  with 789. An index per region must be cut by municipality code, not by postcode.
- **Postal districts.** In the four largest cities the town carries a district letter or two: København K, N, NV, S,
  SV, V and Ø; Aarhus C, N and V; Odense C, M, N, NV, NØ, S, SV, SØ and V; Aalborg SV, SØ and Øst (the `addr:city`
  values with more than 200 uses in the Denmark extract, taginfo; opened).
- **Letters.** Names use æ, ø and å, and older spellings write å as "aa": 695 street names contain "aa" and 4,499
  contain "å", and twenty postal towns use "Aa" (Aarhus, Aalborg, Aabenraa, Faaborg). The city is officially Aarhus,
  but "Århus" is still common in writing. Search should treat "aa" and "å" as the same letter.
- **What the current code does with that** (read in this repository on 17 November 2026, by calling its functions):

| Query | What happens |
|---|---|
| `Rådhuspladsen 1, 1550 København V` | Not treated as an address: `is_address_query` needs the query to start with a digit. |
| `Nørrebrogade 20, 2. th, 2200 København N` | The same. |
| `København`, `Århus`, `Ærøskøbing` | `normalize()` keeps only `a-z` and `0-9`: they become `k benhavn`, `rhus` and `r sk bing`. "Århus" never meets "Aarhus". |
| `12 Tomsgårdsvej 2400 København NV` | Searched in Nevada: `_parts()` takes a last word equal to a US state code for a state, and NV is a postal district in København and Odense. |
| `… 1550 København V` | `_parts()` reads only a five-digit postcode, so `1550` stays among the street words. |

  `tools/build_addresses.py` also keeps only `country = 'US'`. So a Danish address index needs its own rule, as #79
  proposes for German addresses (`norm = de-1` in the index's `meta` table): street before number, four-digit postcodes,
  the floor and door as optional words, `æ`, `ø`, `å` and `aa` folded, and no US-state guess.

## Still undecided

Each of these needs the maintainers' decision before any code changes.

1. **Codes and index names.** Whether `DK-84` style codes are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how address indexes are named when `[A-Z]{2}` does not fit. Thailand has the same
   question.
2. **Bornholm.** One `DK-84` map cut by the region's outline, two maps, or Bornholm as an extra download.
3. **The box source.** Boxes recomputed from DAGI, which needs a Datafordeler key on the build machine, in place of the
   GISCO boundaries used here.
4. **Addresses.** DAR directly through Datafordeler, or Overture's copy, which was last drawn from DAR in March 2026;
   the floor and door kept, or one row per house number; one shared `meta` key for the spelling rule.
5. **Credits.** The wording for CC BY 4.0 data from an agency that changes its name on 1 December 2026, and one table
   or file per licence, or CC BY and OSM points merged under the ODbL.
6. **Water.** Whether coastal dikes become a kind in `water.sqlite`, and whether storm-surge areas belong on the map.
7. **Help points.** A plain word for the nature lean-tos, and whether the regional out-of-hours doctor number is shown
   with the map.
8. **Crops.** Whether to ask Landbrugsstyrelsen to state a licence for the Marker files, and who asks.

## What was checked, and what was not

- Opened on 17 November 2026: Klimadatastyrelsen's notices on DAWA's closure (2 July 2026) and the licence change
  (16 May 2024); Datafordeler's terms page for the agency's data and its page for the elevation model downloads; the
  ministry's notice of the merger with DMI; the GeoDanmark object catalogue for `Bygning`; danmarksadresser.dk's rules
  for addresses and postcodes; Danmarks Statistik's region code page; Geofabrik's Denmark page and `denmark.poly`;
  Overture's attribution page; the OpenAddresses source file for Denmark; hjertestarter.dk's terms; Beredskabsstyrelsen's
  siren page; the notice of the shelter survey; Kystdirektoratet's dike metadata; the police page for 114; the
  out-of-hours doctor pages of four regions.
- Read through public APIs on 17 November 2026: StatBank (FOLK1A), GISCO (NUTS 2024), Nominatim (region relations),
  taginfo for the Denmark extract, and the HTTP answers of DAWA (410) and Datafordeler (401).
- Computed on 17 November 2026: the five boxes, the Bornholm split and the towns inside each box, from the GISCO files;
  postcode, house number and spelling counts from the OpenAddresses file for Denmark; the behaviour of
  `engine/address_search.py` on Danish queries.
- Seen only in search results: the ISO 3166-2:DK codes (ISO refused), GISCO's terms, the Datafordeler key's terms and
  lifetime, Kystdirektoratet's flood data, BBR's fields, and Region Hovedstaden's 1813 page (behind a security check).
- Not checked: the boxes against DAGI (it needs a key); the size of the elevation model; the contents and licence of
  the Marker files; BBR's terms; Kystdirektoratet's dike layer itself (its WFS answered HTTP 500); whether Overture's
  Danish addresses will be refreshed; when Datafordeler's older REST and file services finally close (a phase-out
  document says 30 June 2026, another page 15 January 2027); OSM counts per region.
