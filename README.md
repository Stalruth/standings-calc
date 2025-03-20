# standings-calc

Converts input table data from `rk9-standings-scraper` to Homemade Standings

## Usage:

- `--url`: String; the ID of the tournament with the provider, e.g. `VC02mEl6ma902dsptucd` or `BOG25-VG-MA`
- `--id`: String; the ID of the tournament for our records, e.g. `regional-vancouver` or `special-bogotá`
- `--in`: String; path to the input directory. The tournament data should be in `{in}/{id}`!
- `--out`: String; path to the output directory. The data will be saved to `{out}/{id}`.
- `--season`: Integer; The VGC season the tournament was played in.
- `--structure`: The tournament structure, with two options:
  - `2024`: The tournament structure used for all major tournaments from the 2023 Oceania International Championships till the 2024 North America International Championships.
  - `2025`: The tournament structure used for all major tournaments since and including the 2024 Pokémon World Championships.
  - `2023`: [TODO] Add the tournament structure used for the 2023 San Diego, Liverpool and Orlando Regionals.

## Dependencies:

Python 3.x, no external dependencies.

