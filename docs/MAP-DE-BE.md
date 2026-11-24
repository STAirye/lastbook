# Berlin (DE-BE): a working offline map

Streets, named places, help points and street addresses for Berlin, built from redistributable sources by one command
and kept in its own folder; its places are searchable offline, and its addresses form an index ready for a German
address search. It follows the plan in [REGIONS-DE.md](REGIONS-DE.md) and the file formats in [MAPS.md](MAPS.md). The
region keeps its full ID, `DE-BE`: a bare `DE` means Delaware.

This is the data half: a builder, a testable map set and German query fixtures. It runs `tools/build_map.py` unchanged
and changes nothing in `engine/`, `server.py`, `web/`, `app/` (apart from its own test and fixture), `packaging/` or the
setup flow. Searching the address index the German way, the hand-pump layer and the map builder's region options are
the runtime half, offered in #79 and coordinated with the other regions in #31 and #25.

## Build it

```sh
python3 tools/build_region_de_be.py fetch    # downloads the sources, about 270 MB, into derived/regions/DE-BE/source/
python3 tools/build_region_de_be.py build    # builds beside the last build, replaces data/ once it passes check (about a minute)
python3 tools/build_region_de_be.py check    # validates it; exits non-zero on any failure
python3 tools/build_region_de_be.py demo     # adds an empty library beside it for trying the map alone
python3 server.py --data derived/regions/DE-BE/demo --no-index
```

Python 3.9 or newer and its standard library; no GDAL, no other packages. `fetch` is the only step that uses the
network. Everything is written under `derived/regions/DE-BE/`, so no existing map set changes. `data/build.json`
records every source (URL, dated file name, data date, licence, size, SHA-256) and every other output (size, SHA-256).

`build` writes into `data.new/` and runs `check` on it; only if every check passes does it take the place of `data/`.
A rebuild that fails, or fails its checks, leaves the previous `data/` and its `build.json` as they were (a failed build
stays in `data.new/` to look at, and the next build clears it).

## Sources

| What | Source | Licence | Attribution |
|---|---|---|---|
| Streets, water, land use, buildings, named places and points | OpenStreetMap via Geofabrik, `berlin-YYMMDD-free.gpkg.zip` (the dated name is recorded) | ODbL 1.0 | © OpenStreetMap contributors (already on the map) |
| Street addresses (house number, suffix, postcode, locality) | Geoportal Berlin WFS `adressen_rbs` | Datenlizenz Deutschland Zero 2.0 | none required |
| Hospitals | Geoportal Berlin WFS `krankenhaeuser` (plan hospitals and other hospitals) | dl-de/zero-2.0 | none required |
| Pharmacies | Geoportal Berlin WFS `apotheken` | dl-de/zero-2.0 | none required |
| Fire stations | Geoportal Berlin WFS `feuerwehr` | dl-de/zero-2.0 | none required (one catalogue entry says dl-de/by-2.0; the service says Zero) |
| Police stations | Geoportal Berlin WFS `polizei` | dl-de/zero-2.0 | none required |
| Districts (Bezirke) and localities (Ortsteile) | Geoportal Berlin WFS `alkis_bezirke`, `alkis_ortsteile` | dl-de/zero-2.0 | none required |

Postcode areas are placed at the middle of their own addresses rather than taken from the postcode polygons, which are
CC BY 3.0 DE; that keeps the map to ODbL plus sources without an attribution duty.

For the four official kinds, the Geoportal records replace OpenStreetMap's points, so each facility has one pin from
the public register. Everything else, including street hand pumps, comes from OpenStreetMap.

## What the build holds

Built on 23 November 2026 from the sources fetched on 17 November 2026: OpenStreetMap data of 16 November 2026
(`berlin-261116-free.gpkg.zip`) and the Geoportal services as served that morning. On 17 November a full `fetch`,
`build`, `check` took under two minutes. Row for row, every table holds what the builder in #79 writes from the same
sources with `tools/build_map.py`'s region options, apart from the build times and one fix: the place finder's 952 named
hospitals, pharmacies, fire stations and police stations now carry their source, Geoportal Berlin, where #79 labels
them OpenStreetMap.

| File | Size | SHA-256 (this build) | Holds |
|---|---|---|---|
| `derived/geo/national.sqlite` | 188.1 MB | `c2b77fa2…9d34e` | 467,739 road features plus water, land, rail, buildings and places; 21,000-odd help and supply points |
| `derived/geo/map.sqlite` | 32 KB | `5d421123…650dd` | empty, as in a US state map; carries the map's source and date |
| `derived/geo/places.sqlite` | 3.3 MB | `4b59f374…f30d9` | 12 districts, 97 localities, 193 postcode areas, 11,321 streets, 13,488 named points, 196 named places |
| `derived/geo/addresses/DE-BE.sqlite` | 51.6 MB | `d06f25d7…5a4b2` | 404,303 addresses; a sidecar, as the US address indexes are |
| `map-set.json` | 191 B | | name `DE-BE` and the sizes of the map files |

Help points: 111 hospitals, 702 pharmacies, 102 fire stations and 37 police stations from the Geoportal (replacing
59, 685, 103 and 68 OpenStreetMap points), and 2,080 street hand pumps from OpenStreetMap.

Full checksums are in `data/build.json`. They identify one build: the map and address files record their build time, so two
builds of the same sources differ in those bytes, not in content.

## Checks

`check` verifies, and fails on any miss:

- every output file has the size and SHA-256 recorded at build time; `map-set.json` is named `DE-BE` and its sizes match;
- every SQLite file passes `PRAGMA integrity_check`;
- streets are present, and each help kind has a plausible count (hospitals, pharmacies, fire stations, police, pumps);
- every help point and address lies inside Berlin's box from `regions-de-proposed.json`, and every address has a
  five-digit postcode;
- the address index says `region = DE-BE` and `norm = de-1` in its `meta`, its row count matches, and every stored
  street key is `normalize_de(street)`;
- three public buildings are in the index exactly once with their postcode and locality (Unter den Linden 77, Platz der
  Republik 1, Straße des 17. Juni 135);
- the place finder has a locality, a district, a postcode area and a street, and labels every official help point
  with its source, Geoportal Berlin.

`check` reads the files with SQL only and imports nothing from the app, so it says nothing about how the app searches
them. `app/tests/test_build_region_de_be.py` runs offline: the `de-1` spellings, the stored house-number form, the
fixtures' consistency, that each pump lands exactly where `tools/build_map.py` puts a point, that each place names the
source it came from, and that a rebuild which fails, or fails its checks, leaves the previous output in place.

## Try it

With the demo server running, the map opens over the US; go to Berlin with
`http://127.0.0.1:8890/#/map?lat=52.5163&lon=13.39&z=15&layers=hospital,pharmacy,fire,police`.

On current `main`, with only this map set installed:

| Search | Result |
|---|---|
| `Kreuzberg`, `10117`, `Oranienstraße`, `Alexanderplatz` | the locality, the postcode area, the street |
| `Unter den Linden 77` | the street, not the house: `main` does not read the German order yet |
| `Unter den Linden 77, 10117 Berlin`, `10117 Berlin` | nothing |
| `77 Unter den Linden`, `1 Platz der Republik`, `25 Oranienstr` | the house, in US form (`Berlin, DE-BE, 10117`) |
| `25 Oranienstraße`, `12 Müllerstraße` | nothing |
| `Route 66` | `Straße 66` in Karow, a real numbered Berlin street |

The number-first rows show that `main`'s US address search reads every index in `derived/geo/addresses/`, this one
too: it finds a house when the words, folded the US way, happen to equal the stored `de-1` key. #79 gives each index
only its own rule, so that every US answer stays the same with Berlin installed; the expectations for German queries
are in `app/tests/fixtures/de_be_queries.json`.

`/api/map/near?lat=52.5163&lon=13.3777&cls=hospital,pharmacy,fire_station,police` lists the nearest help around the
Brandenburg Gate. The 2,080 pumps are in `national.sqlite` as `water_well`, but `main` has no layer or name for that
class, so the map neither draws nor lists them until the layer in #79 lands.

## What the runtime half needs

Offered in #79, to be aligned in #31 and #25:

- **Address-index IDs.** `engine/setup/manifest.py` and the upgrade carry-over in `engine/setup/install.py` accept only
  two-letter IDs, so Setup does not install `DE-BE.sqlite` yet; it opens with `--data`.
- **German address search** for indexes whose `meta` says `norm = de-1`, with each index searched only by its own rule.
- **A `water_well` class and layer** ("Hand pumps & water wells (untested water)").
- **`tools/build_map.py` options** for another region's source, date, box and extra point classes. This builder does
  without them: it replaces the three metadata rows afterwards and adds the pumps from the same extract.

## Limits

- **The app's words are still American.** The map page says it shows what was mapped by 25 Oct 2026 (a fixed line in
  `web/map.js`; this map's date is in its `meta`), the search box asks for a ZIP, a button says "Whole United States",
  and the map opens over the US. The source list in `map_info` names US datasets. These belong to the shared region
  work, not to one region's builder.
- **Not in this map:** terrain, the water and dam layers, crops and the resource atlas (US datasets); Berlin's
  disaster-relief points (Katastrophenschutz-Leuchttürme), which are published only as a map and a PDF without a licence.
- **Pumps are not checked.** OpenStreetMap does not say whether a pump works, and the water is untested.
- **The iPad app** marks place results as on the map only inside Southern California or in a pack (`onMap` in
  `server.py`); the web app does not use that flag.

### German addresses

- Eleven houses in Schmöckwitz and Rahnsdorf officially carry a Brandenburg postcode (155xx); they are kept as recorded.
- The source has no postal place names beyond Berlin, so each row holds `city = Berlin` and its locality in `district`;
  a German result reads `10117 Berlin-Mitte` (postcode, city, locality).
- With the search in #79, a query may be written `Straße 12`, `Straße 12a` or `12 a`, with `Str.`/`Strasse`/`Straße`,
  umlauts typed or spelled out (`Muellerstrasse`), an optional postcode and an optional `Berlin` or locality, and with
  numbers inside street names. Not covered there: the number first, ranges (`12-14`), a street name split in two
  (`Oranien Str. 25`) and building parts beyond one letter.
