# Detailed maps for France: a proposal

This is a proposal for discussion, not a decision. It answers, for France, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS-DE.md](REGIONS-DE.md),
[REGIONS-AR.md](REGIONS-AR.md) and [REGIONS-TH.md](REGIONS-TH.md) and is meant to feed the same design discussion (issue
#31). The machine-readable version is [regions-fr-proposed.json](regions-fr-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 17 November 2026, with AI research agents reading the publishers' own
pages and a person reviewing the result. Region boxes, extract sizes and file listings were then fetched the same day
from public APIs and by HTTP HEAD requests, without an account and without downloading any dataset. Separately, the
sources were tried end to end in a local build for three départements (see "What a trial build showed"). Each source
carries one of three marks:

- **opened**: the dataset page, licence page, API answer or download listing was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read, or the question was not looked at; the row says what is
  missing.

A second contributor checked several points first listed as gaps, the same day and with the same kind of AI research
agents plus their own review. Those facts carry the mark **second check**, with **measured** where a query or script
was run.

## Why France is a different case

Germany's layers come from 16 state agencies under four licences. In France most layers have one national source under
one licence, the Licence Ouverte 2.0 (Etalab): IGN's BD ALTI (elevation), BD TOPO (buildings with heights, water, place
names) and RPG (farm parcels) for every département, and the Base Adresse Nationale (BAN), updated daily. So the
question is less "is there an open source" and more how Lastbook reads French projections, French addresses and a
permissive licence next to OpenStreetMap's share-alike one. Those questions were tested in a trial build, not only on
paper.

## What a region is

France has 18 regions: 12 metropolitan regions, Corsica, and 5 overseas regions (Guadeloupe, Martinique, Guyane, La
Réunion, Mayotte). The proposal is one map region per region, 18 in all, the level closest to a US state. Each region is
made of départements (101 in all), listed in the tables below.

ISO 3166-2 files Corsica and the five overseas units as collectivities of various kinds, not as regions; INSEE and the
State's geography API list all 18 as regions (opened), and so does this proposal.

### Codes

ISO 3166-2:FR gives the metropolitan regions three letters after `FR-` (`FR-ARA`, `FR-NOR` and so on), Corsica `FR-20R`,
and the overseas units three digits (`FR-971` Guadeloupe, `FR-972` Martinique, `FR-973` Guyane, `FR-974` La Réunion,
`FR-976` Mayotte). Départements have their own codes, such as `FR-14`, `FR-2A` and `FR-2B` (Paris is `FR-75C`). These
were read from Wikipedia's copy of ISO 3166-2:FR (opened), then checked on ISO's Online Browsing Platform (entry `FR`),
opened in a browser after accepting its terms: all 18 codes are in its list. ISO files `FR-971`, `FR-974` and `FR-976`
as "overseas departmental collectivity", and `FR-972` and `FR-973` as "overseas unique territorial collectivity"
(second check).

- **A bare `FR` is safe; the part after the hyphen is the problem.** No part is two letters: `ARA` is three letters,
  `971` three digits, `20R` mixed. The engine accepts an address index only under a two-letter name:
  `engine/setup/manifest.py` line 72 and `engine/setup/install.py` line 267 both require `[A-Z]{2}`. So French regions
  cannot get address indexes under their ISO codes without a change to that rule.
- **No collision with US codes.** None of the 18 parts is in `STATE_CODES` (`engine/address_search.py`). The two-letter
  ISO 3166-1 codes of the overseas regions (`GP`, `MQ`, `GF`, `RE`, `YT`) are not in it either. Wikipedia's change
  history says ISO deleted `FR-GP`, `FR-MQ`, `FR-GF`, `FR-RE` and `FR-YT` as French subdivisions in 2021. ISO's own
  change history dates that deletion to 25 November 2021, and the change from `FR-COR` to `FR-20R` to 24 November 2020
  (second check).
- **The trial used a provisional stem.** To pass the `[A-Z]{2}` rule, the trial index was named with a two-letter code
  that is not an ISO code (`BN`). It is not proposed. The trial builder refuses a region code that equals a US state
  code, because the engine reads any `XX.sqlite` named like a state with US rules, without opening its `meta` table.
- **Départements as the unit instead.** Départements have numeric codes (`FR-14`), which fail `[A-Z]{2}` too, and 101
  maps would be a long list. For address indexes alone, one index per département is easy to cut: the first two digits
  of a postcode are the département, except Corsica (`2A` and `2B` both use `20`) and overseas (three digits, `971` to
  `976`). There are exceptions: 23 metropolitan communes use a neighbouring département's postcode prefix, and 6 of
  these cross a region boundary (for example Buxeuil, Vienne, with `37160`); Saint-Barthélemy and Saint-Martin, which
  are not part of these regions, use `971` postcodes (geo.api.gouv.fr, 34,969 communes, opened). The BAN's `code_insee`
  column gives the département without these exceptions, so an index should be cut by commune code, not by postcode.

### Boxes

Each box is the union of the bounding boxes of the region's communes, from the State's geography API
(`https://geo.api.gouv.fr/regions/{code}/departements`, then
`https://geo.api.gouv.fr/departements/{code}/communes?fields=code,bbox&format=json`; 34,875 communes, opened). Each box
was then widened by 0.15° and rounded outward to 0.01°, the margin `map_sets.state` uses for US states.

The limit of the method: the API's outlines are simplified, and its page does not state their source or licence. For
Calvados, Manche and Orne the API's north edge is 49.7276°, about 270 m south of IGN's ADMIN EXPRESS COG 2026
(49.7300°); west, south and east agree. For the whole of Normandy the box equals the ADMIN EXPRESS box to four decimals,
because the north edge then falls in Seine-Maritime. Boxes recomputed from ADMIN EXPRESS (IGN; Licence Ouverte 2.0 on
its data.gouv.fr record), as the trial did, agree: computed from every vertex of IGN's WFS layer
`ADMINEXPRESS-COG.2026:region`, they match the boxes below to 0.0001° for all 18 regions, and the boxes with the 0.15°
margin are identical (second check, measured). IGN's own page for ADMIN EXPRESS on cartes.gouv.fr names `etalab-2.0`
and links the Licence Ouverte text; neither that page nor the site's terms of use fixes a credit sentence (second
check).

| Code | INSEE region code | Name | Départements | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|---|
| `FR-ARA` | 84 | Auvergne-Rhône-Alpes | 01, 03, 07, 15, 26, 38, 42, 43, 63, 69, 73, 74 | 2.0629, 44.1155, 7.1856, 46.8043 | 1.91, 43.96, 7.34, 46.96 |
| `FR-BFC` | 27 | Bourgogne-Franche-Comté | 21, 25, 39, 58, 70, 71, 89, 90 | 2.8449, 46.1561, 7.1434, 48.4001 | 2.69, 46.00, 7.30, 48.56 |
| `FR-BRE` | 53 | Bretagne | 22, 29, 35, 56 | -5.1412, 47.2779, -1.0156, 48.9008 | -5.30, 47.12, -0.86, 49.06 |
| `FR-CVL` | 24 | Centre-Val de Loire | 18, 28, 36, 37, 41, 45 | 0.0527, 46.3469, 3.1287, 48.9410 | -0.10, 46.19, 3.28, 49.10 |
| `FR-20R` | 94 | Corse | 2A, 2B | 8.5347, 41.3336, 9.5600, 43.0276 | 8.38, 41.18, 9.71, 43.18 |
| `FR-GES` | 44 | Grand Est | 08, 10, 51, 52, 54, 55, 57, 67, 68, 88 | 3.3837, 47.4203, 8.2325, 50.1693 | 3.23, 47.27, 8.39, 50.32 |
| `FR-HDF` | 32 | Hauts-de-France | 02, 59, 60, 62, 80 | 1.3802, 48.8372, 4.2558, 51.0892 | 1.23, 48.68, 4.41, 51.24 |
| `FR-IDF` | 11 | Île-de-France | 75, 77, 78, 91, 92, 93, 94, 95 | 1.4463, 48.1201, 3.5590, 49.2415 | 1.29, 47.97, 3.71, 49.40 |
| `FR-NOR` | 28 | Normandie | 14, 27, 50, 61, 76 | -1.9550, 48.1799, 1.8029, 50.0722 | -2.11, 48.02, 1.96, 50.23 |
| `FR-NAQ` | 75 | Nouvelle-Aquitaine | 16, 17, 19, 23, 24, 33, 40, 47, 64, 79, 86, 87 | -1.7924, 42.7779, 2.6113, 47.1760 | -1.95, 42.62, 2.77, 47.33 |
| `FR-OCC` | 76 | Occitanie | 09, 11, 12, 30, 31, 32, 34, 46, 48, 65, 66, 81, 82 | -0.3272, 42.3329, 4.8456, 45.0467 | -0.48, 42.18, 5.00, 45.20 |
| `FR-PDL` | 52 | Pays de la Loire | 44, 49, 53, 72, 85 | -2.6254, 46.2667, 0.9167, 48.5680 | -2.78, 46.11, 1.07, 48.72 |
| `FR-PAC` | 93 | Provence-Alpes-Côte d'Azur | 04, 05, 06, 13, 83, 84 | 4.2302, 42.9820, 7.7190, 45.1268 | 4.08, 42.83, 7.87, 45.28 |
| `FR-971` | 01 | Guadeloupe | 971 | -61.8098, 15.8320, -61.0020, 16.5145 | -61.96, 15.68, -60.85, 16.67 |
| `FR-972` | 02 | Martinique | 972 | -61.2290, 14.3886, -60.8097, 14.8787 | -61.38, 14.23, -60.65, 15.03 |
| `FR-973` | 03 | Guyane | 973 | -54.6024, 2.1111, -51.6191, 5.7487 | -54.76, 1.96, -51.46, 5.90 |
| `FR-974` | 04 | La Réunion | 974 | 55.2165, -21.3896, 55.8367, -20.8718 | 55.06, -21.54, 55.99, -20.72 |
| `FR-976` | 06 | Mayotte | 976 | 45.0183, -13.0053, 45.3000, -12.6366 | 44.86, -13.16, 45.45, -12.48 |

**Boxes that reach another country.** A state map holds every row inside its box, so a box that crosses a border would
pick up foreign rows from any source that has them. The padded boxes were tested against the Natural Earth 1:110m
country outlines this repository ships in `web/world-context.json`, and against Geofabrik's outlines for Andorra, Monaco
and Luxembourg, which carry a buffer:

- `FR-GES` covers parts of Germany, Switzerland, Luxembourg and Belgium; `FR-HDF` covers part of Belgium, and the padded
  box reaches England; `FR-BFC` and `FR-ARA` reach Switzerland, and `FR-ARA` Italy; `FR-PAC` covers Monaco and part of
  Italy; `FR-OCC` covers Andorra and part of Spain; `FR-NAQ` covers part of Spain and reaches the north edge of Andorra;
  `FR-20R` reaches the north of Sardinia; `FR-973` covers parts of Suriname and Brazil.
- **Channel Islands.** The `FR-NOR` box reaches Les Écréhous before padding, and with the margin also the east of Jersey
  and part of Les Minquiers, but not Alderney. The `FR-BRE` padded box reaches Les Minquiers. These island boxes come
  from Nominatim (OpenStreetMap), not from an official boundary. Geofabrik's French extracts leave the Channel Islands
  out (checked on the `basse-normandie` outline), but a source cut by box would not.
- Small islands near Guadeloupe, Martinique and Mayotte (Dominica, Saint Lucia, Montserrat, the Comoros) are not in the
  1:110m outlines; whether the boxes reach them was not checked.
- **Saint-Martin and Saint-Barthélemy** use `971` postcodes (see "Codes") but lie outside Guadeloupe's box: IGN's BD
  TOPO layer `collectivite_territoriale` puts Saint-Barthélemy at 62.93° to 62.79° W, 17.87° to 17.97° N and
  Saint-Martin at 63.15° to 62.97° W, 18.05° to 18.13° N, at least 1.2° north and 0.8° west of the padded box (second
  check, measured). A Guadeloupe map would not show their streets.

The trial's fix: cut by département outlines, and keep the box for display and the spatial index. No region's box
contains another's (unlike Berlin in Brandenburg in REGIONS-DE.md), but neighbouring boxes overlap widely.

### Size of each region

Population is INSEE's municipal population of 1 January 2023, in force since 1 January 2026 (table "Populations des
régions", opened); INSEE's 2023 reference tables leave out Mayotte. Communes are counted from geo.api.gouv.fr. Address
numbers are from the BAN's commune summary (`https://plateforme.adresse.data.gouv.fr/api/communes-summary.csv`, composed
up to 17 November 2026, opened); for Paris, Lyon and Marseille it lists districts, not communes.

| Code | Départements | Communes | Population 2023 | BAN address numbers |
|---|---|---|---|---|
| `FR-ARA` | 12 | 4,025 | 8,205,557 | 2,989,836 |
| `FR-BFC` | 8 | 3,685 | 2,802,670 | 1,334,428 |
| `FR-BRE` | 4 | 1,202 | 3,449,370 | 1,754,716 |
| `FR-CVL` | 6 | 1,754 | 2,587,031 | 1,275,641 |
| `FR-20R` | 2 | 360 | 355,486 | 135,260 |
| `FR-GES` | 10 | 5,115 | 5,563,378 | 2,131,157 |
| `FR-HDF` | 5 | 3,782 | 5,992,194 | 2,543,096 |
| `FR-IDF` | 8 | 1,266 | 12,463,067 | 2,177,071 |
| `FR-NOR` | 5 | 2,644 | 3,345,842 | 1,548,301 |
| `FR-NAQ` | 12 | 4,293 | 6,150,451 | 3,235,717 |
| `FR-OCC` | 13 | 4,446 | 6,124,653 | 2,835,248 |
| `FR-PDL` | 5 | 1,228 | 3,907,156 | 1,799,822 |
| `FR-PAC` | 6 | 946 | 5,218,960 | 1,527,860 |
| `FR-971` | 1 | 32 | 384,160 | 163,474 |
| `FR-972` | 1 | 34 | 360,630 | 138,347 |
| `FR-973` | 1 | 22 | 293,996 | 62,266 |
| `FR-974` | 1 | 24 | 889,679 | 340,794 |
| `FR-976` | 1 | 17 | not checked | 52,982 |

### OpenStreetMap extracts

Geofabrik cuts France into the 22 regions that existed before 2016, plus the five overseas regions (France page opened;
data up to 2026-11-16T21:22:36Z). Each current region is a whole number of these extracts: the communes of every
département fall inside one extract's outline (tested point by point against Geofabrik's `.poly` files). Where a region
needs two or three extracts, they have to be merged (for example with osmium) before `tools/build_map.py`, and the
merged file keeps Geofabrik's buffer into neighbouring regions. Sizes are from HEAD requests on the `-latest` files,
which redirect to the files dated 16 November 2026 (opened):

| Code | Extracts (`https://download.geofabrik.de/europe/france/<name>-latest.osm.pbf`) | `.osm.pbf`, bytes | `-latest-free.gpkg.zip`, bytes |
|---|---|---|---|
| `FR-ARA` | `auvergne`, `rhone-alpes` | 690,202,363 | 1,280,694,399 |
| `FR-BFC` | `bourgogne`, `franche-comte` | 326,292,276 | 649,164,895 |
| `FR-BRE` | `bretagne` | 330,755,575 | 615,402,636 |
| `FR-CVL` | `centre` | 245,671,405 | 484,652,828 |
| `FR-20R` | `corse` | 34,540,890 | 74,580,156 |
| `FR-GES` | `alsace`, `champagne-ardenne`, `lorraine` | 409,747,508 | 776,398,156 |
| `FR-HDF` | `nord-pas-de-calais`, `picardie` | 375,141,932 | 733,854,818 |
| `FR-IDF` | `ile-de-france` | 340,430,258 | 563,159,234 |
| `FR-NOR` | `basse-normandie`, `haute-normandie` | 252,197,623 | 517,084,555 |
| `FR-NAQ` | `aquitaine`, `limousin`, `poitou-charentes` | 627,766,685 | 1,244,497,288 |
| `FR-OCC` | `languedoc-roussillon`, `midi-pyrenees` | 635,682,850 | 1,226,915,060 |
| `FR-PDL` | `pays-de-la-loire` | 374,315,248 | 693,609,053 |
| `FR-PAC` | `provence-alpes-cote-d-azur` | 391,878,638 | 675,207,117 |
| `FR-971` | `guadeloupe` | 24,765,563 | none |
| `FR-972` | `martinique` | 20,382,369 | none |
| `FR-973` | `guyane` | 14,426,214 | 33,390,133 |
| `FR-974` | `reunion` | 34,582,431 | none |
| `FR-976` | `mayotte` | 10,977,681 | none |

Sizes for regions with several extracts are sums; the JSON gives each file. Guadeloupe, Martinique, La Réunion and
Mayotte have only the `.osm.pbf`: their pages say the free shapefile "is not available for this region", and the
GeoPackage URL redirects to Geofabrik's home page. `tools/build_map.py` reads the free GeoPackage, so these four regions
would need another reader or a conversion first. A single France extract also exists (`france-latest.osm.pbf`,
5,117,018,657 bytes on the same day).

## Sources, layer by layer

These hold for the whole country. The detail, with methods and sizes for the trial départements, is in the JSON.

| Layer (file) | US source today | Proposed for France | Publisher | Licence | Checked |
|---|---|---|---|---|---|
| Terrain (`terrain.sqlite`) | USGS 3DEP | BD ALTI v2, 25 m, one file per département; Copernicus GLO-30 as fallback | IGN; ESA / Airbus | Licence Ouverte 2.0; Copernicus licence | opened; tried |
| Water (`water.sqlite`) | NHD | BD TOPO v3.5 hydrography (lakes, ponds, streams, springs); BD Topage as alternative | IGN; Sandre / OFB | Licence Ouverte 2.0 | opened; tried |
| Dams | NID | ROE, the national register of river obstacles (WFS, by département) | Sandre / OFB | Licence Ouverte 2.0 | opened; tried |
| Crops (`crops.sqlite`) | USDA Cropland Data Layer | RPG 2025 v4.0, declared farm parcels, one file per region | IGN, ASP | Licence Ouverte 2.0 | opened; tried |
| Buildings (`buildings.sqlite`) | Microsoft US footprints, OSM heights | BD TOPO v3.5 `batiment`, with height in metres | IGN | Licence Ouverte 2.0 | opened; tried |
| Places (`places.sqlite`) | GNIS, Census gazetteers, OSM | BD TOPO communes, delegated communes and hamlets; INSEE COG 2026 and populations | IGN; INSEE | Licence Ouverte 2.0 | opened; tried |
| Addresses (`addresses/<code>.sqlite`) | Overture addresses | BAN, one CSV per département; Overture (the same BAN, about a month older) as alternative | BAN; Overture | Licence Ouverte 2.0 | opened; tried (BAN) |
| Points of interest (`poi` rows) | OSM | OSM, as today; national lists for defibrillators, gendarmerie and fuel as supplements | OSM contributors; ministries | ODbL; Licence Ouverte 1.0 or 2.0 | opened; OSM tried |

**Overseas and Corsica.** IGN's download feeds (`https://data.geopf.fr/telechargement/resource/<product>?zone=...`,
opened) list a BD ALTI 25 m file and a BD TOPO file of 15 September 2026 for every one of the 101 départements, and an
RPG 2025 file for every one of the 18 regions; the BAN has a CSV for 971 to 976, 2A and 2B (HEAD). None of these was
tried outside the trial. Overseas files use local projections and height datums (for example UTM 20 with GUAD88 heights
for Guadeloupe, UTM 40 South with REUN89 for La Réunion), and Corsica's BD ALTI uses IGN78C heights, so the trial's
Lambert-93 conversion does not apply as it is. The ROE layer is named for metropolitan France (`ObstEcoul_FXX`), but
Sandre's WFS has one layer per territory beside it, `_GLP`, `_MTQ`, `_GUF`, `_REU` and `_MYT`, and `_all`. Counts on 17
November (`resultType=hits`): 120,038 in metropolitan France, 113 in Guadeloupe, 388 in Martinique, 741 in Guyane, 140
in La Réunion, 156 in Mayotte, 125,818 in all (second check, measured). The six sum to 121,576, and the 4,242 more in
`_all` are rows whose status is "Gelé" (frozen); the other 121,576 are "Validé" (second check, measured). Overture files
the overseas rows under `FR` (see "How addresses are written"). OSM coverage overseas was not checked.

Coverage of the five overseas regions differs by dataset (second check; opened unless marked):

| Dataset | Metropolitan France | 971 | 972 | 973 Guyane | 974 | 976 |
|---|---|---|---|---|---|---|
| BD ALTI, BD TOPO, RPG 2025 (as above); RGE ALTI, cadastre; ROE, Overture addresses (measured) | yes | yes | yes | yes | yes | yes |
| MNT LiDAR HD | planned "by 2026", progress not read | planned | planned | **excluded** | planned | planned |
| Copernicus GLO-30 | sample tiles | sample tile | sample tile | sample tiles | sample tile | sample tile |
| BD TOPAGE 2026, INPE 2023 | yes | yes | yes | **no** (INPE), **no file listed** (TOPAGE) | yes | yes |
| OSO (crops) | yes, Corsica included | no | no | no | no | no |
| CORINE Land Cover | 2018 | 2018 | 2018 | 2018, coastal and border-river strip only | 2018 | 2018 |
| GeoNames postcode files | `FR.zip`, without 971 to 976 | `GP.zip` | `MQ.zip` | `GF.zip` | `RE.zip` | `YT.zip` |

TOPAGE's absence in Guyane rests on Sandre's 2026 folder, which lists files for FXX, GLP, MTQ, MYT and REU and none for
Guyane (one listing, not a statement by the publisher); INPE's record says Guyane is "in progress". The ministry's
[CORINE page](https://www.statistiques.developpement-durable.gouv.fr/corine-land-cover-0) limits Guyane to a 20 km strip
along the coast and the lower reaches of the border rivers (second check).

Notes:

- **Terrain.** 25 m matches zoom 12 at 49° N, the deepest zoom `tools/build_terrain.py` writes. BD ALTI covers French
  land only; the sea is 0 m, and the Channel Islands are not in it. Copernicus GLO-30 covers them but is a surface
  model.
- **Water.** The ROE lists weirs and dams in rivers, not reservoirs: it has no storage volume and almost no structure
  heights, unlike the NID. BD TOPO's `detail_hydrographique` gives springs; `water.sqlite` has no spring kind today
  (the Springs layer reads OSM).
- **Crops.** The RPG is declared by farmers, so areas are exact sums rather than satellite pixels. It has no code for
  apple trees: cider orchards most likely fall under `VRG` ("other orchard"), which the data does not confirm, and
  orchards grazed as grassland can be declared as grassland.
- **Buildings.** BD TOPO's `hauteur` runs from the lowest ground point to the top of the eaves (the roof edge, or the
  top of the wall under a flat roof), not to the ridge (BD TOPO 3.5 content description, July 2026; second check).
- **Places.** `places.sqlite` has no population column; the trial put population, postcode and INSEE code in `detail`.
- **Points of interest.** Geofabrik puts `fuel` in its `traffic` tables, which `tools/build_map.py` does not read, so a
  map built by that tool has no fuel stations; this also affects US maps built with it. `chemist` (a shop selling
  personal care articles) is shown in the Pharmacies layer. `comms_tower` is a real Geofabrik class (53 points in the
  trial area).

## Help points

OpenStreetMap stays the base. Several national lists under Licence Ouverte add what OSM may lack (opened, counts from
data.gouv.fr's tabular API): Géo'DAE, the national defibrillator base (192,233 records); the gendarmerie units that
receive the public, with opening hours (3,681); fuel stations with live prices and shortages (9,833); the education
directory (68,555 entries). FINESS lists hospitals, clinics and pharmacies, but its counts were not obtained. No
national list was found for public drinking water, shelters, harbours, SAIP sirens or sea rescue stations; their absence
is not proven. IGN's BD TOPO is an official source for fire stations and more: its `zone_d_activite_ou_d_interet` layer
holds 6,710 fire and rescue centres, 3,775 gendarmerie posts, 960 police entries, 718 mountain refuges and 1,854
mountain shelters, with geometry, overseas included, under the same licence as the buildings (WFS counts; second check,
measured). France's emergency numbers include 112, 15, 17, 18, 114 and 196 for rescue at sea (service-public.gouv.fr,
opened).

OSM counts for all of metropolitan France (taginfo for Geofabrik's extract, data until 2026-11-16 21:22 UTC, all object
types; second check): `amenity=pharmacy` 19,141; `amenity=fire_station` 6,124; `amenity=police` 5,979;
`amenity=hospital` 2,494; `amenity=drinking_water` 26,740; `emergency=defibrillator` 28,328; `emergency=fire_hydrant`
246,264.

## Licence notes and attribution

- **Licence Ouverte 2.0** (IGN, INSEE, BAN, Sandre, Géo'DAE, fuel prices; opened). Name the source, at least the
  licensor, and the date of the last update of the data reused, for example "Source: IGN – BD TOPO®, 2026-09-15" or
  "Source : Insee". No share-alike. The licence says it is compatible with licences that require attribution, naming the
  OGL, CC-BY and ODC-BY.
- **Licence Ouverte 1.0** (FINESS, gendarmerie units, the administration directory, as named on data.gouv.fr; the 1.0
  text was not checked).
- **ODbL** (OSM). As for the US map. The app and the packs have no link to the ODbL text today, and nothing answers
  article 4.6 (offer the derived database).
- **Copernicus WorldDEM-30**, only if GLO-30 is used: the two notices given in REGIONS.md. Overture names the BAN under
  Licence Ouverte 2.0 for its French addresses.

New with France: Licence Ouverte points merged with OSM points in one `poi` table probably make a derived database under
the ODbL; one file or table per licence avoids that (a question, not legal advice). `MAP_CREDIT` in
`packaging/build_packs.py` is a fixed US list, while the Licence Ouverte asks for a date per source.

## How addresses are written

- **Order.** Number, then an optional repetition index (*bis*, *ter*, or a letter), then street type and name; then the
  postcode and the commune on the last line, in capitals in postal use: "14 bis Rue Écuyère, 14000 Caen". La Poste's
  specification, which cites the paid standard NF Z 10-011, allows six lines of 38 characters (opened).
- **Postcode.** Five digits, usually starting with the département (see "Codes"). A postcode can serve several communes,
  and a commune can have several postcodes. A CEDEX code and label can replace them on the last line.
- **Merged communes.** Many communes are *communes nouvelles* made of former *communes déléguées*. The BAN keeps the
  former commune in its own column; duplicate street names inside one merged commune are told apart in the street name,
  for example "Rue de la République (Cherbourg-Octeville)".
- **Street words.** *rue*, *avenue*, *boulevard*, *chemin*, *impasse*, *allée*, *route*, *place*; abbreviations such as
  BD, AV, IMP and RTE; *Saint* and *Sainte* written St and Ste. The AFNOR form drops accents, and the BAN itself is not
  consistent ("Place de la Republique" and "Rue de la République" in one commune).
- **What the current code does with that** (read in this repository on 17 November 2026): `normalize()` keeps only `a-z`
  and `0-9`, so "Église" becomes `glise`; `_parts()` reads the postcode only as the last word, while it comes before the
  commune in France; a last word equal to a state code is taken for a US state, which removes Bellême (`me`), Ri and
  Bonnœil (`il`) among ten communes of the trial area; `tools/build_addresses.py` keeps only `country = 'US'`.
- **Overture's French rows** (second check, measured with DuckDB on release 2026-10-21.0). There are 26,052,116 rows
  with `country = 'FR'`, all with a five-digit postcode. `postal_city` is empty in every row, and `address_levels` has
  one entry, the commune. So `tools/build_addresses.py` as written would store an empty city and the commune's first two
  letters as the state: 351 values, with 6,894,553 rows (26 %) equal to a real US code. 7.8 % of numbers carry a
  suffix, mostly fused ("12bis"). `sources[0].dataset` names the département (`fr/59`, `fr/2A`), which gives an exact
  cut without postcodes. The five overseas regions are under `FR`, and so are Saint-Barthélemy, Saint-Martin and
  Saint-Pierre-et-Miquelon; there are no rows under `GP`, `MQ`, `GF`, `RE` or `YT`.

## What a trial build showed

The sources above were built into a local map set for three départements, Calvados (14), Manche (50) and Orne (61), and
shown in the app's map from the repository sources. **The code is not in this pull request.** It is local, it was
written against the current formats, and it will be adapted to the common region format when the maintainers publish it
(in issue #31 the maintainers say they are coordinating the overlapping approaches and will follow up with the agreed
direction). Every figure below was measured in that build on 17 November 2026.

| File | Contents | Size, bytes | Build time |
|---|---|---|---|
| `national.sqlite` | 598,144 features (roads, land, water, coast and sea), 13,916 help points | 129,593,344 | 7.9 s, plus 3.3 s for the coast |
| `addresses/<code>.sqlite` | 796,608 addresses from the BAN, plus 97,105 rows for named localities | 129,368,064 (41,226,378 with gzip) | 8.1 s |
| `buildings.sqlite` | 1,539,916 buildings, IGN height for 97.9 % | 57,966,592 | 27 s |
| `places.sqlite` | 85,921 places, including 1,352 communes with population and 529 delegated or associated communes | 13,312,000 | 3 s |
| `water.sqlite` | 158 dams, 218 reservoirs, 272 lakes, 1,391 ponds, 1,283 springs, 96,854 stream segments | 30,412,800 | 17 s |
| `terrain.sqlite` | 1,002 terrain tiles, zooms 4 to 12 | 51,044,352 | 8 s |
| `crops.sqlite` | 1,918 blocks, 5,360.17 ha of orchards, vines and berries | 1,818,624 | 12 s |

The map set came to 414 MB on disk and about 209 MB with gzip. Among the help points: 73 hospitals, 397 pharmacies and
386 fuel stations (read from the `traffic` tables). What the build showed:

- **Addresses.** Of 28 test queries for addresses that exist, the unchanged engine found 1 and the trial engine 28,
  including "35 r st jean caen", "11 rue du Marais Ri", postcodes before the commune, missing accents, abbreviations and
  delegated communes. Search took 0.2 ms at the median. 152 BAN rows were left out because their repetition field held a
  flat or door number. The US behaviour was compared with the original engine on 30 queries and is unchanged.
- **How the engine knows an index is French.** The index declares `meta.country = 'FR'` and is searched only with its
  own rules. #79 (Berlin) declares its rule in the same table (`norm = de-1`), according to its description; the two are
  compatible in spirit, and one shared key would be better than two.
- **Projections.** The Lambert-93 conversion was checked against 797,760 BAN addresses that carry both coordinate
  systems: 7 mm at most. Terrain tiles agree with the source grid to 0.18 m at the median.
- **Coast and sea.** `tools/build_coast.py` closes the sea at longitude -125, for California. The trial closed it along
  a box, with the Channel Islands' coastline from Geofabrik's `guernsey-jersey` extract. East of 0° and south of 48.75°
  N the sea stops at a straight edge: the neighbouring coasts were not in the build.
- **Buildings.** The server drops buildings whose outline starts at the same point; BD TOPO's terraced houses share
  corners, and 4.9 % disappeared until each outline was given a unique first point.
- **Units.** The file formats store acres and feet. The trial kept those columns, added metric ones beside them and
  showed metres and hectares in a region.
- **Tests.** The repository's tests passed with the trial code in place: 327 tests, 3 skipped, Python 3.11.

Known defects of the trial: the 3D view drops to a cliff at the edge of the data; a click on a crop patch does not
always open its card; IGN's streams replaced OSM's, losing about 12 % of OSM lines with no IGN match; 5 of 158 dams have
a height and none a volume; a place mapped as point and area in OSM can count twice; it was not tried in the installed
app.

## Still undecided

Each of these needs the maintainers' decision before any code changes.

1. **Codes and index names.** Whether `FR-ARA`, `FR-20R` and `FR-971` are acceptable as a manifest `id`, in
   `map-set.json` and in `Lastbook-Map-<id>.zip`, and how address indexes are named when `[A-Z]{2}` does not fit; or
   whether France is cut by département instead. Either way, a region code must never equal a US state code.
2. **The box and the cut.** Whether boxes come from ADMIN EXPRESS, and whether every source is cut by département
   outlines rather than by the box, as Jersey and the borders above require.
3. **Address indexes.** The BAN directly (daily, with repetition index and former commune) or the BAN through Overture
   (the US pipeline; French fields in "How addresses are written", second check); one shared `meta` key for the
   spelling rule (`country = 'FR'` here, `norm = de-1` in #79); the delegated commune in `city` in brackets or in a new
   column; extra rows for named localities; whether a numbered query with no address should fall back to place search;
   and whether US indexes should fold accents too, which means rebuilding them.
4. **Licences in one file.** One table or file per licence, or OSM and Licence Ouverte points merged under the ODbL; an
   answer to ODbL article 4.6; per-region credits with dates.
5. **Units.** Metric columns (`height_m`, `area_ha`) in the common format, or imperial columns converted on display.
6. **Water.** Streams as lines in `water.sqlite`; a `spring` kind; the ROE as the dam layer (dams only, or weirs too).
7. **Crops.** A vector reader for the RPG; the 1.8 ha block threshold (the trial used none; with it, 15 % of the area
   would go); how to name `VRG`.
8. **Places.** A population column, or population in `detail`; English kinds for French places; how to show delegated
   communes.
9. **Terrain edges and overseas projections.** Mask the relief outside the data, or add the neighbouring départements;
   readers for the five overseas projections.
10. **Help points.** New kinds (defibrillators, gendarmerie); whether the `fuel` and `chemist` defects, which affect US
    maps too, go in a separate small pull request.

## Known gaps

- Not checked: the source and licence of geo.api.gouv.fr's outlines; Mayotte's population; whether the boxes reach small
  islands near Guadeloupe, Martinique and Mayotte; FINESS counts; the meaning of the ROE's `CdTypeOuvrage` codes; the
  vertical precision and overseas datums of BD ALTI; whether cider orchards are coded `VRG`; the texts of Licence
  Ouverte 1.0 and of NF Z 10-011; the licence of BD CARTO; every layer for Corsica and overseas beyond the presence of
  the files.
- The trial covered three départements of one region. Nothing was built for the other 98, for Corsica or overseas.
