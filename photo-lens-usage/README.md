# photo-lens-usage

A skill for answering "would I miss the zoom lens?" before buying a phone without one. It reads your Apple Photos library and works out what share of your photos used the telephoto, ultra-wide and main lens, per phone, per year, overall, and for favorites only.

**Status:** tested on one real library (about 30,000 photos, 9 iPhones from the 7 Plus to the 17 Pro Max). The maths has 13 unit tests. It hasn't been run on Android or standalone-camera libraries yet, so treat that path as untested.

## What you get

- Tables in the terminal: telephoto and ultra-wide share per camera, per year and overall, for all photos and for favorites.
- A CSV with every number.

The first run gave 24% telephoto across all photos and 30% for favorites. Telephoto was used about twice as often as ultra-wide.

## Requirements

- A Mac with your Photos library on it (iCloud-synced is fine).
- [osxphotos](https://github.com/RhetTbull/osxphotos), installed with pipx. The skill checks for both and asks before installing anything.
- Full Disk Access for the app that runs the commands. macOS protects the Photos library, so you have to grant this yourself in System Settings. The skill explains how and which app needs it.

## Install

Copy the `photo-lens-usage` folder into `~/.claude/skills/`. Then ask Claude something like "how often do I actually use my telephoto lens?" or "would I miss optical zoom on my next phone?"

## How it works

1. Checks the tools are installed, and asks before installing.
2. Checks it can read the library, and walks you through Full Disk Access if not.
3. Prints the camera fields for about 20 sample photos, so nothing is built on guessed field names.
4. Lists every camera and lens in your library with photo counts and year ranges.
5. Stops and asks you which cameras are yours and which lenses count as telephoto and ultra-wide. Lens names never say "telephoto"; lenses are told apart by focal length (for example, 15.66mm is the 5x on a 15 Pro Max). Your answers go in a `config.json`.
6. Runs the unit tests on fake data, then runs on your library with sanity checks (per-camera and per-year totals must add up to the overall total).
7. Reports the results, with caveats.

## Read-only

The skill only reads metadata. osxphotos works from a temporary copy of the Photos database, and the skill never runs osxphotos commands that export, import, edit or change albums.

## Things to know

- On the iPhone 14 Pro and later, 2x is a crop of the main sensor and is recorded as the main lens. Telephoto share therefore undercounts how often you zoomed.
- Photos from other people's phones end up in most libraries (AirDrop, shared albums, family libraries). The inventory shows year ranges so you can leave those out.
- Selfies are counted but left out of the percentages, since every phone has a front camera.
- Videos are excluded.
- In the Claude desktop app, commands run under an inner `claude.app` that needs its own Full Disk Access entry, and its path changes when Claude updates. If it worked last week and fails now, that's the likely reason.

## Files

- `SKILL.md`: the instructions Claude follows.
- `scripts/lens_usage.py`: inventory and report.
- `scripts/test_lens_usage.py`: unit tests (`python3 -m unittest test_lens_usage` from `scripts/`).
- `scripts/sample_fields.py`: prints raw camera fields for a sample of photos.
- `references/lens-hints.md`: observed iPhone lens strings and focal lengths.
- `assets/config.example.json`: config template.

Built on [osxphotos](https://github.com/RhetTbull/osxphotos) by Rhet Turnbull.
