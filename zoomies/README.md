# zoomies

A skill for answering "would I miss the zoom lens?" before buying a phone without one. It reads your Apple Photos library and works out what share of your photos used the telephoto, ultra-wide and main lens, per phone, per year, overall, and for favorites only.

**Status:** tested on one real library (about 30,000 photos, 9 iPhones from the 7 Plus to the 17 Pro Max). The maths has 15 unit tests. It hasn't been run on Android or standalone-camera libraries yet, so treat that path as untested.

## What you get

- Tables in the chat: telephoto and ultra-wide share per camera, per year and overall, for all photos and for favorites.
- A CSV with every number, saved to your Desktop as `lens_usage.csv` (see below).

The first run gave 24% telephoto across all photos and 30% for favorites. Telephoto was used about twice as often as ultra-wide.

## Requirements

- [Claude Code](https://claude.com/claude-code), either in the terminal or the Code tab of the Claude desktop app, running on the Mac that has your Photos library. It won't work in regular Claude chat, which can't reach files on your Mac.
- A Mac with your Photos library on it (iCloud-synced is fine).
- [osxphotos](https://github.com/RhetTbull/osxphotos), installed with pipx. The skill checks for both and asks before installing anything.
- Full Disk Access for the app that runs the commands. macOS protects the Photos library, so you have to grant this yourself in System Settings. The skill explains how and which app needs it.

## Install

The easiest way is to ask Claude Code to do it: "Install the zoomies skill from https://github.com/hi-mitcho/skillz into ~/.claude/skills".

Or in Terminal:

```bash
git clone https://github.com/hi-mitcho/skillz.git /tmp/skillz
mkdir -p ~/.claude/skills && cp -R /tmp/skillz/zoomies ~/.claude/skills/
```

Start a new Claude Code session, then ask something like "how often do I actually use my telephoto lens?" or "would I miss optical zoom on my next phone?"

## How it works

1. Checks the tools are installed, and asks before installing.
2. Checks it can read the library, and walks you through Full Disk Access if not.
3. Prints the camera fields for about 20 sample photos, so nothing is built on guessed field names.
4. Lists every camera and lens in your library with photo counts and year ranges.
5. Stops and asks you which cameras are yours and which lenses count as telephoto and ultra-wide. Lens names never say "telephoto"; lenses are told apart by focal length (for example, 15.66mm is the 5x on a 15 Pro Max). Your answers go in a `config.json`.
6. Runs the unit tests on fake data, then runs on your library with sanity checks (per-camera and per-year totals must add up to the overall total).
7. Reports the results, with caveats.

## The CSV

`~/Desktop/lens_usage.csv` opens in Numbers or Excel. Each row is one camera, one year, or the overall total, for either all photos (`photos` = `all`) or favorites only (`favorites`). The columns are:

- `section` and `group`: what the row covers, e.g. `camera` / `iPhone 15 Pro Max`, or `year` / `2024`.
- `total_photos`: every photo in that group, including selfies.
- `rear_photos`: photos from the back cameras. Percentages are out of this number.
- `telephoto_photos`, `telephoto_pct`, `ultrawide_photos`, `ultrawide_pct`, `main_photos`, `main_pct`: counts and shares per lens.
- `selfies_excluded`, `missing_lens_excluded`: counted, but left out of the percentages.
- `notes`: flags like "small sample" or "2x crops counted as main lens".

The inventory step also saves `inventory.csv` in the working folder: every camera and lens found in your library, with photo counts and the years it was used.

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
- `scripts/test_lens_usage.py`: unit tests.
- `scripts/sample_fields.py`: prints raw camera fields for a sample of photos.
- `references/lens-hints.md`: observed iPhone lens strings and focal lengths.
- `assets/config.example.json`: config template.

Built on [osxphotos](https://github.com/RhetTbull/osxphotos) by Rhet Turnbull.
