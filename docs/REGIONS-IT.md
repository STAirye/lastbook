# Detailed maps for Italy: a proposal

This is a proposal for discussion, not a decision. It answers, for Italy, the questions [MAPS.md](MAPS.md) asks before
coverage can go beyond the United States: which open source replaces each federal list, under what licence, what a
"state" is there, and how addresses are written. It follows the shape of [REGIONS.md](REGIONS.md),
[REGIONS-DE.md](REGIONS-DE.md), [REGIONS-FR.md](REGIONS-FR.md) and [REGIONS-ES.md](REGIONS-ES.md) and is meant to feed the
same design discussion. The machine-readable version is [regions-it-proposed.json](regions-it-proposed.json).

Nothing here changes the app, the engine or a build. No code reads the JSON, and nothing here ships: builds package
`web/` and `content/` only.

**How things were checked.** Research was done on 18 November 2026, with an AI research agent reading the publishers' own
pages and downloading the files named below, and a person reviewing the result. The boxes, the pharmacy counts and the
Lombardy address figures were computed from the data itself, as described in each section. Each source carries one of
three marks:

- **opened**: the dataset or licence page itself was opened and read;
- **search only**: the fact was seen in a search result from the publisher's own site, but the page itself was not
  opened;
- **not checked**: the page could not be reached or read; the row says what is missing.

**Relation to #84.** Pull request #84 (open on 18 November 2026) proposes one country-level map set per European
country, built from Geofabrik's whole-country extract, with Italy as `eu-it`. This proposal is the finer cut below it:
one map per region, for libraries that want street detail without carrying the whole country. The two do not clash: the
codes here are `IT-21` to `IT-88`, never `eu-it`, and both would read the same OSM extracts.

## Why Italy is a useful case

Italy has more open national data than its reputation suggests, but it is spread across many publishers rather than one
mapping agency:

- **Boundaries and names** come from ISTAT (the statistics office) under CC BY 4.0, refreshed every 1 January.
- **Addresses** have a national archive, ANNCSU, run by the Agenzia delle Entrate and ISTAT, with a CSV per region that
  anyone can download. It has coordinates for about two thirds of the rows in the one region measured, but **no
  postcode**.
- **Help points** are split: the Ministry of Health publishes every pharmacy with coordinates; there is no national open
  list of fire stations or civil protection assembly areas that could be opened.
- **Several official languages** in three regions: German (and Ladin) in South Tyrol, French in the Aosta Valley,
  Slovene in parts of Friuli Venezia Giulia.

## What a region is

Italy has 20 regions: 15 ordinary ones and 5 with a special statute (Aosta Valley, Trentino-South Tyrol, Friuli Venezia
Giulia, Sicily, Sardinia). The proposal is one map per region, 20 in all. A region is the level closest to a US state in
what it runs: health services, civil protection, and most open data portals are regional. By the area in ISTAT's layer,
the largest, Sicily (25,835 km²), is close to Vermont; the smallest, the Aosta Valley (3,261 km²), is smaller than Rhode
Island; Lombardy is 23,863 km².

The provinces are the other candidate: 110 in ISTAT's 2026 layer (provinces, metropolitan cities, the two autonomous
provinces, and Sardinia's restored provinces). They would give smaller downloads, and the postcode and the province
abbreviation (*sigla*) on every address follow them. But they run less than regions do, and the help-point data found
here is published by region or nationally. The view here is that provinces are
not needed as a map level. Trentino-South Tyrol is the one case for an exception (see "Still undecided"): its two
autonomous provinces, Bolzano/Bozen and Trento, do what regions do elsewhere. The JSON keeps each region's province list
so that either cut can be made later.

### Codes

ISO 3166-2:IT gives each region two digits after `IT-`: `IT-21` Piedmont, `IT-25` Lombardy, `IT-32` Trentino-South Tyrol,
`IT-88` Sardinia, and so on (taken from Wikipedia's copy of ISO 3166-2:IT, opened on 18 November 2026, and not checked
against the ISO site, as the other proposals also note for their codes). The two autonomous provinces also have codes,
`IT-BZ` and `IT-TN`.

- The part after `IT-` is digits, so no region code can equal a US code in `STATE_CODES` (`engine/address_search.py`).
  The hyphen still matters: it keeps `Lastbook-Map-<id>.zip` and `derived/geo/addresses/<id>.sqlite` apart from the US
  files.
- The province *sigle* would collide if used as ids: 18 of the 110 are also US codes (`AL` Alessandria, `AR` Arezzo,
  `CA` Cagliari, `CO` Como, `CT` Catania, `ME` Messina, `MI` Milano, `MN` Mantova, `MO` Modena, `MS` Massa-Carrara,
  `MT` Matera, `OR` Oristano, `PA` Palermo, `PR` Parma, `RI` Rieti, `TN` Trento, `VA` Varese, `VT` Viterbo). Bare `IT` is
  not a US code.

### Boxes

The boxes were computed from ISTAT's "Confini delle unità amministrative a fini statistici al 1° gennaio 2026", the
non-generalised version (`Limiti01012026.zip`, 98,536,297 bytes, last modified 6 March 2026, SHA-256
`a9075f8d839dcb2b409099703da7bdd37cc214f8967fa7372b32305875ad046f`; page and ISTAT's legal notice, which puts the site's
data under CC BY 4.0, opened). Every vertex of every polygon in the region layer `Reg01012026_WGS84` (WGS 84 / UTM zone
32N) was reprojected to longitude and latitude and the extremes taken; each box was then widened by 0.15° and rounded
outward to 0.01°, the same margin `map_sets.state` uses for US states.

As a check, the outer edges match Italy's known extreme points: the Vetta d'Italia in South Tyrol in the north
(47.09° N), Lampedusa in the south (35.49° N), the western Alps of Piedmont in the west (6.63° E) and the Otranto coast
of Apulia in the east (18.52° E). Sicily's west edge (11.93° E) is Pantelleria; Lazio's south edge (40.78° N) is the
Pontine islands.

| Code | ISTAT | Name | Box (west, south, east, north) | Box with 0.15° margin |
|---|---|---|---|---|
| `IT-21` | 01 | Piemonte (Piedmont) | 6.6266, 44.0601, 9.2142, 46.4644 | 6.47, 43.91, 9.37, 46.62 |
| `IT-23` | 02 | Valle d'Aosta/Vallée d'Aoste (Aosta Valley) | 6.8013, 45.4670, 7.9395, 45.9878 | 6.65, 45.31, 8.09, 46.14 |
| `IT-25` | 03 | Lombardia (Lombardy) | 8.4979, 44.6797, 11.4277, 46.6352 | 8.34, 44.52, 11.58, 46.79 |
| `IT-32` | 04 | Trentino-Alto Adige/Südtirol (Trentino-South Tyrol) | 10.3818, 45.6731, 12.4779, 47.0918 | 10.23, 45.52, 12.63, 47.25 |
| `IT-34` | 05 | Veneto | 10.6229, 44.7928, 13.1022, 46.6805 | 10.47, 44.64, 13.26, 46.84 |
| `IT-36` | 06 | Friuli-Venezia Giulia (Friuli Venezia Giulia) | 12.3209, 45.5809, 13.9189, 46.6478 | 12.17, 45.43, 14.07, 46.8 |
| `IT-42` | 07 | Liguria | 7.4948, 43.7757, 10.0710, 44.6764 | 7.34, 43.62, 10.23, 44.83 |
| `IT-45` | 08 | Emilia-Romagna | 9.1979, 43.7319, 12.7556, 45.1391 | 9.04, 43.58, 12.91, 45.29 |
| `IT-52` | 09 | Toscana (Tuscany) | 9.6867, 42.2377, 12.3714, 44.4727 | 9.53, 42.08, 12.53, 44.63 |
| `IT-55` | 10 | Umbria | 11.8919, 42.3641, 13.2642, 43.6173 | 11.74, 42.21, 13.42, 43.77 |
| `IT-57` | 11 | Marche | 12.1855, 42.6872, 13.9164, 43.9716 | 12.03, 42.53, 14.07, 44.13 |
| `IT-62` | 12 | Lazio | 11.4494, 40.7847, 14.0276, 42.8387 | 11.29, 40.63, 14.18, 42.99 |
| `IT-65` | 13 | Abruzzo | 13.0185, 41.6821, 14.7830, 42.8951 | 12.86, 41.53, 14.94, 43.05 |
| `IT-67` | 14 | Molise | 13.9410, 41.3640, 15.1616, 42.0703 | 13.79, 41.21, 15.32, 42.23 |
| `IT-72` | 15 | Campania | 13.7621, 39.9905, 15.8064, 41.5074 | 13.61, 39.84, 15.96, 41.66 |
| `IT-75` | 16 | Puglia (Apulia) | 14.9341, 39.7896, 18.5204, 42.2266 | 14.78, 39.63, 18.68, 42.38 |
| `IT-77` | 17 | Basilicata | 15.3350, 39.8948, 16.8672, 41.1399 | 15.18, 39.74, 17.02, 41.29 |
| `IT-78` | 18 | Calabria | 15.6298, 37.9158, 17.2065, 40.1439 | 15.47, 37.76, 17.36, 40.3 |
| `IT-82` | 19 | Sicilia (Sicily) | 11.9257, 35.4929, 15.6533, 38.8177 | 11.77, 35.34, 15.81, 38.97 |
| `IT-88` | 20 | Sardegna (Sardinia) | 8.1307, 38.8592, 9.8284, 41.3133 | 7.98, 38.7, 9.98, 41.47 |

Boxes overlap their neighbours, as US state boxes do. Several boxes include land outside Italy: San Marino lies inside
the boxes of Emilia-Romagna and Marche, Vatican City inside Lazio's, and Lombardy's holds Campione d'Italia, a Lombard
commune inside Switzerland, along with parts of Ticino. Sicily's box runs south to Lampedusa and so contains Malta (the
islands of Malta, Gozo and Comino). With the margin, Sardinia's box reaches the southern tip of Corsica and Liguria's
reaches Monaco. The ISTAT layers have 7,896 communes in 2026; the JSON gives the count per region.

## Sources, layer by layer

| Layer | US source today | Proposed for Italy | Licence | Mark |
|---|---|---|---|---|
| Streets, water, names, buildings | OSM (Geofabrik US extracts) | OSM, Geofabrik's five Italian extracts (`nord-ovest`, `nord-est`, `centro`, `sud`, `isole`) | ODbL 1.0 | opened |
| Terrain | USGS 3DEP | TINITALY/1.1, INGV, 10 m cell, whole country (released January 2023) | CC BY 4.0 | opened |
| Terrain, alternative | | Copernicus DEM GLO-30, as in the other proposals | Copernicus WorldDEM-30 | opened |
| Rivers and lakes | USGS NHD | OSM; no national river network was opened | ODbL 1.0 | opened (OSM) |
| Flood and landslide hazard | | ISPRA IdroGEO open data (national hazard mosaics) | CC BY 4.0 for some products, CC BY-SA 4.0 for others | opened |
| Dams | USACE NID | OSM `waterway=dam` (2,044 in Italy); the Ministry of Infrastructure's large dam register (DG Dighe) | ODbL 1.0; register: not checked | opened (OSM), page fetched, no licence found (register) |
| Crops | USDA CDL | CORINE Land Cover 2018, classes 221 vineyards, 222 fruit trees and berries, 223 olive groves | Copernicus data policy, full, open and free | opened |
| Places | USGS GNIS, Census | ISTAT communes and boundaries, plus OSM for *frazioni* and *località* | CC BY 4.0; ODbL 1.0 | opened |
| Addresses | Overture (US) | ANNCSU indirizzario, one CSV per region; or Overture, which carries ANNCSU | CC BY 4.0 (from Overture's attribution page, see below) | opened, file read |
| Pharmacies | OSM | Ministry of Health pharmacy list, with coordinates | IODL 2.0 | opened, file read |
| Hospitals | OSM | Ministry of Health list of hospital trusts and public research hospitals; OSM for the buildings | IODL 2.0 | opened (page), file not read |
| Fire stations, assembly areas | OSM | OSM only; no national open list was reached | ODbL 1.0 | not checked (official lists) |

Notes on the rows:

- **OSM.** Geofabrik's pages for Italy and for `nord-ovest` were opened (ODbL, "© OpenStreetMap contributors"). Lombardy,
  Piedmont, the Aosta Valley and Liguria are in `nord-ovest`. Counts for Italy from Geofabrik's taginfo (data until
  17 November 2026, 21:24 UTC): 16,891 `amenity=pharmacy`, 2,348 `amenity=hospital`, 2,181 `amenity=clinic`, 1,472
  `amenity=fire_station`, 7,135 `amenity=police`, 1,584 `emergency=assembly_point`, 8,180 `emergency=defibrillator`,
  69,898 `amenity=drinking_water`, 10,297 `man_made=water_tap`, 9,888 `natural=spring`, 3,986 `man_made=water_well`,
  12,304 `amenity=fountain`, 1,944 `tourism=alpine_hut`, 1,522 `tourism=wilderness_hut`.
- **TINITALY.** INGV's page says TINITALY/1.1 is under CC BY 4.0 "and can be used freely, even partly, but it must be
  cited as follows", with a fixed citation. It is finer than the 30 m data the app uses today and covers the whole
  country in one product. How it is downloaded (tiles, any registration) was not checked.
- **IdroGEO.** The page gives CC BY 4.0 for some products and CC BY-SA 4.0 for others; a share-alike product would have to
  be read product by product before use. This is hazard mapping, not a river network. ISPRA's national hydrographic
  network (SINAnet) was seen in search only.
- **Dams.** The DG Dighe register page was fetched, but no download and no licence text was found on it. A "grandi dighe
  italiane" dataset on `dati.mit.gov.it` was seen in search only.
- **Crops.** No national open parcel layer, like Spain's SIGPAC, was found. CORINE is coarse (25 ha minimum unit), and
  citrus and nuts fall inside class 222.

## Addresses in ANNCSU, measured

ANNCSU (Archivio Nazionale dei Numeri Civici delle Strade Urbane) is the national archive of streets and house numbers,
kept by the communes. Its open data pages (opened) offer one zipped CSV per region, served by the Agenzia delle Entrate.
The Lombardy file was downloaded on 18 November 2026: `indirizzarioLombardia20261102.zip`, 36,906,989 bytes, SHA-256
`3ae8004f52a1b467cb05c5b21428f523e0e0840dc470f9155e7787a9b08df189`, holding `INDIR_LOMB_20261102.csv`. Read in full:

- 3,136,806 rows (one per house number), on 142,847 streets in 1,501 communes (ISTAT counts 1,502 in Lombardy).
- 2,070,077 rows have coordinates; 2,069,101 of those fall inside the `IT-25` box with its margin.
- Columns: commune codes, street name (`ODONIMO`), `LOCALITA'`, a second-language name (`DIZIONE_LINGUA1`, empty in
  Lombardy), house number (`CIVICO`) and suffix (`ESPONENTE`, on 593,605 rows), coordinates, height and a method code.
  **There is no postcode column.**
- All street names are in capitals. The commonest first words are *VIA* (2,738,891), *VIALE* (87,961), *PIAZZA*
  (64,345), *STRADA* (53,916), *VICOLO* (52,194), *LOCALITA'* (35,038), *CORSO* (23,364), *FRAZIONE* (21,312) and
  *CASCINA* (19,523).

The ANNCSU pages opened do not name a licence. Overture's attribution page (opened) lists Italy as "Archivio Nazionale
dei Numeri Civici delle Strade Urbane (ANNCSU). Available under CC BY 4.0. Distributed by OpenAddresses". The national
catalogue `dati.gov.it`, where the licence would be stated, returned an error (502) when queried. So CC BY 4.0 is taken
from a second-hand source and should be confirmed with the publisher before a build. Whether Overture adds postcodes to
the Italian rows was not measured.

## Help points

- **Pharmacies.** The Ministry of Health publishes every pharmacy, open or closed, with coordinates (page opened, IODL
  2.0). The file `FRM_FARMA_5_20261118.csv` was read: 59,268 rows, of which 20,779 have no end date (open pharmacies),
  and 18,941 of those have coordinates. Per region, the JSON gives the open count (3,287 in Lombardy). The ministry's
  list has about 3,900 more pharmacies than OSM's 16,891.
- **Hospitals.** The ministry lists hospital trusts, university hospitals and public research hospitals (IRCCS) with
  address and province (page opened, IODL 2.0); no coordinates were mentioned, and the file was not read. A trust can run
  several sites, so this is not a list of buildings. OSM has 2,348 hospitals.
- **Fire stations.** The Vigili del Fuoco open data portal answered searches for "sedi" (stations) with no results, and
  further pages could not be read. OSM has 1,472.
- **Civil protection assembly areas** (*aree di attesa*, *aree di emergenza*) are planned by each commune and published,
  if at all, on regional or municipal portals. No national list was found. OSM has 1,584 `emergency=assembly_point`.
- **Emergency numbers.** 112 is the European number. The Department for European Affairs page (opened) said on European
  112 day 2026 that the NUE model, where one centre answers 112 and passes calls on, runs in 16 regions and 2 autonomous
  provinces through 23 answering centres. How 112 is answered elsewhere, and whether the older numbers (113 police, 115
  fire, 118 ambulance) still answer everywhere, was not checked on a publisher page.

## Licence notes and attribution

All proposed licences allow redistribution in a free offline library, including commercial reuse, except where noted.

- **CC BY 4.0, ISTAT.** The legal notice puts the site's content under "Licenza CC-by Creative Commons 4.0": credit ISTAT,
  link the licence, and say if the data was changed (boxes are a change).
- **CC BY 4.0, INGV (TINITALY).** Must be cited with the citation the page gives (dataset name, version, DOI and the
  Tarquini et al. papers).
- **CC BY 4.0, ANNCSU.** As above, read on Overture's page, not on the publisher's.
- **IODL 2.0, Ministry of Health.** Named on both dataset pages ("Italian Open Data Licence v2.0"). It asks for credit to
  the licensor. The licence text itself was not opened; IODL 2.0 is generally described as compatible with CC BY, which
  was not checked here.
- **CC BY-SA 4.0, some ISPRA products.** Share-alike, if used.
- **Copernicus** (CORINE, DEM). Free, full and open access under the Copernicus data policy, with source credit.
- **ODbL** (OSM). As for the US map.

These notices would belong wherever the map already credits its sources, and in `THIRD_PARTY_NOTICES.md` if that is
where the maintainers keep data licences.

## How addresses are written

- **Order.** Street type, street name, comma, house number, then postcode, town and province *sigla*: "Piazza della
  Scala, 2, 20121 Milano MI". The type comes first (*Via*, *Viale*, *Piazza*, *Corso*, *Vicolo*, *Strada*, *Largo*) and is
  often abbreviated (*V.*, *P.za*, *C.so*). The house number (*civico*) can carry a suffix: "10/A", "10 bis".
- **Postcode** (*CAP*). Five digits, the same shape as a US ZIP code. Leading zeros occur (Rome is `001xx`), so a CAP must
  stay text. 20,778 of the 20,779 open pharmacy rows carry a five-digit CAP. ANNCSU has none (see above), so an address
  index built from it would need postcodes from elsewhere.
- **Province.** The two-letter *sigla* after the town ("Milano MI", often "(MI)").
- **Frazione and località.** Hamlets of a commune; a rural address may name one instead of a street ("Località
  Cascina Nuova, 5") or between street and town. 65,047 Lombardy ANNCSU rows fill `LOCALITA'`.
- **Other languages.** In South Tyrol street and place names are official in Italian and German, and in some valleys in
  Ladin ("Bolzano/Bozen"). In the Aosta Valley they are Italian and French. In Slovene-speaking communes of the provinces
  of Trieste, Gorizia and Udine, Slovene names are protected. 124 of ISTAT's 7,896 communes carry a second official name.
- **What the current code does with that** (read in this repository on 18 November 2026):
  - `normalize()` in `engine/address_search.py` and `norm()` in `tools/build_addresses.py` keep only `a-z` and `0-9`,
    so accented names ("Località", "Città") lose letters, while ANNCSU writes them in capitals with an apostrophe
    ("LOCALITA'"). Accents need folding on both sides.
  - `is_address_query()` needs a number first, and Italian addresses never start with one.
  - `_parts()` takes a postcode only as the last word, while Italian addresses put the town and *sigla* after it.
  - `tools/build_addresses.py` keeps only `country = 'US'`.
  - The five-digit postcode rule itself fits Italy unchanged.

## Still undecided

Each of these needs the maintainers' decision before any code changes. The first two are shared with REGIONS.md and the
other proposals.

1. **Codes in setup.** Whether `IT-25` and the others are acceptable as a manifest `id`, in `map-set.json` and in
   `Lastbook-Map-<id>.zip`, and how setup groups 20 Italian regions. As REGIONS-ES.md notes, `carry_over()` in
   `engine/setup/install.py` keeps only address indexes named `[A-Z]{2}`, so `IT-25.sqlite` would be left behind on an
   upgrade (read in this repository on 18 November 2026).
2. **The box rule**, as in REGIONS.md, here from ISTAT's boundaries.
3. **Trentino-South Tyrol.** One map (`IT-32`) or two (`IT-BZ`, `IT-TN`), since the autonomous provinces run what regions
   run elsewhere and South Tyrol's names are bilingual.
4. **Address source.** ANNCSU directly, which needs the licence confirmed and has no postcodes, or Overture's copy of it.
5. **Postcodes.** No open postcode area layer was found; Poste Italiane assigns them.
6. **Terrain.** TINITALY at 10 m, one Italian source, or Copernicus DEM at 30 m, one source for all of Europe.
7. **Official help-point lists.** Whether to merge the Ministry of Health pharmacy list into OSM's, and how to credit it.
8. **Bilingual names**: whether the place finder and address search index both official forms.
9. **Relation to #84**: whether a region map and the `eu-it` country map can sit in one library, and which wins when both
   cover a street.

## What was checked, and what was not

- Opened on 18 November 2026: ISTAT's boundaries page and legal notice; the ISTAT 2026 boundary file (downloaded and
  read); Geofabrik's pages for Italy and `nord-ovest`, and its taginfo for Italy; INGV's TINITALY page; the Copernicus DEM
  registry page; the CORINE 2018 product page; ISPRA's IdroGEO open data page; ANNCSU's open data, bulk download, search
  and update status pages and its metadata file; the ANNCSU Lombardy file (downloaded and read); Overture's attribution
  page; the Ministry of Health pharmacy page and file (downloaded and read) and its hospital page; Regione Lombardia's
  hospital dataset record; the DG Dighe register page; the Interior Ministry's 112 page; the Department for European
  Affairs' 112 page; Wikipedia's ISO 3166-2:IT page.
- Computed on 18 November 2026: the 20 boxes and the commune and province counts, from ISTAT's 2026 layers; the pharmacy
  counts, from the ministry's file; the Lombardy address figures, from the ANNCSU file.
- Seen only in search results: ISPRA's national hydrographic network; the MIT large dam dataset; civil protection
  assembly areas on regional portals; Regione Lombardia's 5 m terrain model.
- Not checked: the ANNCSU licence on a publisher page (`dati.gov.it` returned 502); the IODL 2.0 licence text; the
  dam register's licence and format; the Vigili del Fuoco station list; TINITALY's download terms; how 112 is answered
  outside the NUE regions; and the ISO 3166-2:IT codes against the ISO site.
