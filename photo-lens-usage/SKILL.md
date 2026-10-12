---
name: photo-lens-usage
description: Measure which camera lens someone actually uses (telephoto/zoom, ultra-wide, main) by reading their Apple Photos library on a Mac with osxphotos, strictly read-only. Reports telephoto and ultra-wide share per phone, per year, overall, and for favorites, with tested maths, sanity checks, a CSV, and optional editable SVG charts for social media. Use this whenever someone asks how often they use their zoom/telephoto/ultra-wide lens, whether they'd miss optical zoom, whether to buy a phone without a telephoto (or "Pro") camera, what focal lengths they shoot most, or wants lens or camera stats from their Photos library, even if they don't mention osxphotos.
---

# Photo lens usage

Answer "which lens do I actually use?" from a person's own Apple Photos library, so a
phone-buying decision rests on real data. Works for iPhones and any other camera whose
photos are in Photos.

## Ground rules (and why)

- **Strictly read-only.** This is someone's photo library, often irreplaceable. Read
  metadata only. Use the bundled scripts and `osxphotos query --count`; never run osxphotos
  commands that write, export, import, or change albums (`export`, `import`, `batch-edit`,
  `timewarp`, `push-exif`, `sync`, `query --add-to-album`, etc.).
- **Look before building.** Lens strings differ by phone, firmware and camera mode, so
  never guess field names or which lens is which. Sample, then run the inventory, then ask.
- **The person decides what counts.** Which cameras are theirs and which lens strings are
  telephoto or ultra-wide are their call. Propose, then pause for confirmation before any
  percentages are calculated.
- **Prove the maths before touching real data.** Run the bundled tests first.
- **Explain as you go.** Many people asking this aren't developers. Say what each step does
  in plain language, and when something errors, explain what it means before fixing it.
- **Installs and system settings need consent.** Ask before installing anything; never
  change privacy or security settings yourself; tell the person how.

Paths below: `SKILL_DIR` is this skill's folder. Write `config.json`, `inventory.csv` and
`charts/` to the working folder, and the results CSV to the Desktop unless asked otherwise.

## Step 1: Tools

Check: `which pipx osxphotos python3`. If missing, show the person the commands, explain
each in one line, and wait for an OK:

```bash
brew install pipx
pipx ensurepath
pipx install osxphotos
```

If `pipx install` fails with *"pipx needs uv>=…, but … uv reports …"*, an old `uv` installer
is on the PATH. Fix it without touching uv: `pipx install osxphotos --backend pip`.

The scripts need the Python that lives inside the osxphotos environment:

```bash
OSX_PY="$(pipx environment --value PIPX_LOCAL_VENVS)/osxphotos/bin/python"
```

## Step 2: Permission to read the library

Test with `osxphotos query --count`. Two errors both mean macOS privacy protection is
blocking access: **"Operation not permitted"** on `Photos.sqlite`, or **"Could not get path
to photo library database"** (osxphotos can't even read which library is the system one).
osxphotos may also write `osxphotos_crash.log` to the working folder; delete it after
reading. Confirm with `head -c 4 ~/Pictures/*.photoslibrary/database/Photos.sqlite`. The person must grant
**Full Disk Access** in System Settings → Privacy & Security → Full Disk Access, then
restart the app.

The catch: grant access to **the process that actually runs your commands**, which may not
be the app the person sees. Find it:

```bash
pid=$$; while [ "$pid" -gt 1 ]; do ps -o pid=,ppid=,comm= -p $pid; pid=$(ps -o ppid= -p $pid | tr -d ' '); done
```

In the Claude desktop app, commands run under an inner `claude.app` inside
`~/Library/Application Support/Claude/claude-code/<version>/…/claude.app`, launched through a
"disclaimer" helper, so it needs its **own** Full Disk Access entry (+ button, ⌘⇧G, paste the
path). The path contains a version number, so **after any Claude update the new inner app
needs adding again**. If it worked last week and fails now, check the version in the
process chain first. In
Terminal or iTerm, grant it to that terminal app. Mention that the person can switch it off
again afterwards.

Once it works, report total items and photos only (`--only-photos --count`).

## Step 3: Sample real fields

```bash
"$OSX_PY" "$SKILL_DIR/scripts/sample_fields.py" 20
```

Show the person the actual `camera_model`, `lens_model` and `focal_length` values, and
point out what you see: missing lens strings on old photos, generic model names, the mm
numbers that distinguish lenses.

## Step 4: Inventory, then pause for decisions

```bash
"$OSX_PY" "$SKILL_DIR/scripts/lens_usage.py" inventory --out inventory.csv
```

This lists every camera and lens key with photo counts and year ranges. Read
`references/lens-hints.md`, then present:

1. **Which cameras look like theirs.** Libraries contain photos from other people's phones
   (shared, AirDropped, family libraries). Use volume and year ranges to propose a list and
   flag doubtful ones (e.g. many photos from a phone overlapping their main phone's years).
2. **Proposed telephoto and ultra-wide lens keys** as a table per camera with counts. Group
   all descriptor variants of the same mm value. Explain that the word "telephoto" never
   appears and lenses are told apart by mm.
3. **Defaults to confirm:** selfies (front camera) are counted but left out of percentages,
   since every phone has a front camera; crop modes (2x on 14 Pro and later, 8x on 17 Pro)
   are not separate lenses.

Ask these together (a multiple-choice question tool helps), wait for answers, then write
`config.json` (template: `assets/config.example.json`). Keys must match the inventory
exactly. Put Pro phones with sensor-crop zoom in `crop_note_cameras`. Add short `labels`
and `zoom` (e.g. `"5x"`) if charts are likely, and `chart_exclude_years` for partial years
(e.g. the year a first telephoto phone arrived late), which otherwise look like spikes.

## Step 5: Tests, then the real run

```bash
cd "$SKILL_DIR/scripts" && python3 -m unittest test_lens_usage -v
```

All should pass; show the person. If one fails, stop and explain; don't run on real data.
Then:

```bash
"$OSX_PY" "$SKILL_DIR/scripts/lens_usage.py" report --config config.json --out ~/Desktop/lens_usage.csv
```

The script prints per-camera, per-year and overall tables for all photos and favorites,
runs sanity checks (per-camera and per-year totals equal the overall total; buckets add up;
overall equals a direct count), and saves the CSV. If any sanity check fails, stop and
investigate before reporting numbers.

## Step 6: Report

Lead with the answer in one sentence, e.g. *"About 1 in 4 of your rear-camera photos (24%)
used the telephoto lens; among favorites it's 30%."* Then:

- A per-camera table (telephoto %, plus ultra-wide % if configured, all vs favorites);
  mark small samples rather than hiding them.
- What it means for the decision: trends as zoom reach changed, whether favorites lean
  telephoto, and what share a phone without a telephoto (main + ultra-wide) would still
  cover (100% − telephoto %).
- **Caveats, always:** crop zoom counts as main, so telephoto **undercounts** zooming;
  scope is "photos taken on these cameras", not "photos taken during these years"; videos
  are excluded; how many photos lacked lens data.

## Step 7 (optional): Charts for social

Offer this once the numbers are done.

```bash
python3 "$SKILL_DIR/scripts/make_charts.py" --csv ~/Desktop/lens_usage.csv --config config.json --out charts
```

This writes up to four 1080×1350 (4:5) SVGs: a headline stat with dot grids, telephoto by
camera (all vs favorites), telephoto by year, and a lens mix (if ultra-wide is configured).
Every element is a named layer with live text (Inter), ready to restyle in Figma
(drag in) or Illustrator (File → Open).

- **Look at them before handing over.** SVGs can hide overlapping labels. If Chrome is
  installed, render previews:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --hide-scrollbars --window-size=1080,1350 --screenshot=out.png "file://$PWD/charts/1-headline.svg"`
  (Quick Look crops to a square, so don't trust it for layout.) Fix collisions in the
  script, not by hand.
- Tell the person: restyle freely, but don't stretch bars by hand (that changes the numbers);
  rerunning the script overwrites `charts/`, so duplicate files before styling.
- If they need different content, edit `make_charts.py` rather than drawing bars manually.
