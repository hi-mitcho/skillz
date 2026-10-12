"""Draw social-ready SVG charts (1080x1350, 4:5) from the lens_usage.py CSV.

Every shape sits in a named group (<g id="...">) so layers are easy to find in
Figma or Illustrator. Text stays live and editable (font: Inter). Bar lengths
come straight from the CSV, so restyle freely but don't stretch bars by hand.

Usage:
    python3 make_charts.py --csv ~/Desktop/lens_usage.csv --config config.json --out charts/
Optional config keys used here: "labels" (short display names), "zoom" (e.g. "5x").
"""
import argparse
import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

W, H, PAD = 1080, 1350, 80
FONT = "Inter, Helvetica, Arial, sans-serif"
SURFACE, INK, INK_2, INK_3, GRID, EMPTY = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"                   # all photos / favorites (CVD-validated pair)
AQUA, MAIN_GREY, VIOLET = "#1baf7a", "#d6d5d0", "#4a3aa7"  # ultra-wide / main / telephoto (validated)


# ---------------------------------------------------------------- primitives

def text(x, y, s, size, fill=INK, weight=400, anchor="start", id_=None):
    ident = f' id="{escape(id_)}"' if id_ else ""
    return (f'<text{ident} x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(s))}</text>')


def group(id_, parts):
    return f'<g id="{escape(id_)}">' + "".join(parts) + "</g>"


def bar(x, y, length, thick, fill, id_, round_left=False, round_right=True):
    """Horizontal bar; rounded only on the requested outer ends."""
    length = max(length, 0.5)
    rl = min(6, length / 2, thick / 2) if round_left else 0
    rr = min(6, length / 2, thick / 2) if round_right else 0
    d = (f"M{x + rl:.1f},{y} H{x + length - rr:.1f} "
         + (f"A{rr},{rr} 0 0 1 {x + length:.1f},{y + rr} " if rr else "")
         + f"V{y + thick - rr} "
         + (f"A{rr},{rr} 0 0 1 {x + length - rr:.1f},{y + thick} " if rr else "")
         + f"H{x + rl:.1f} "
         + (f"A{rl},{rl} 0 0 1 {x},{y + thick - rl} " if rl else "")
         + f"V{y + rl} " + (f"A{rl},{rl} 0 0 1 {x + rl:.1f},{y} " if rl else "") + "Z")
    return f'<path id="{escape(id_)}" d="{d}" fill="{fill}"/>'


def svg(parts):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect id="background" width="{W}" height="{H}" fill="{SURFACE}"/>' + "".join(parts) + "</svg>")


def header(title, subtitle):
    return group("header", [text(PAD, 150, title, 54, weight=700, id_="title"),
                            text(PAD, 205, subtitle, 28, INK_2, id_="subtitle")])


def legend(items, y=275):
    parts, x = [], PAD
    for name, color in items:
        parts += [f'<rect x="{x}" y="{y - 20}" width="24" height="24" rx="5" fill="{color}"/>',
                  text(x + 36, y, name, 26, INK_2)]
        x += 36 + len(name) * 14 + 40
    return group("legend", parts)


def footer(lines):
    return group("footnote", [text(PAD, H - 70 - 36 * (len(lines) - 1 - i), s, 22, INK_3)
                              for i, s in enumerate(lines)])


# ---------------------------------------------------------------- data helpers

class Data:
    def __init__(self, csv_path, config):
        with csv_path.open() as f:
            self.rows = list(csv.DictReader(f))
        self.config = config
        self.labels = config.get("labels", {})
        self.zoom = config.get("zoom", {})
        self.small = config.get("small_sample", 30)
        self.crop_note = bool(config.get("crop_note_cameras"))

    def get(self, photos, section, group):
        for r in self.rows:
            if (r["photos"], r["section"], r["group"]) == (photos, section, str(group)):
                return r
        return None

    def section(self, photos, section):
        return [r for r in self.rows if r["photos"] == photos and r["section"] == section]

    def cameras(self):
        """Cameras with enough rear photos to chart, in config order."""
        return [r for r in self.section("all", "camera")
                if r["telephoto_pct"] and int(r["rear_photos"]) >= self.small]

    def label(self, name):
        return self.labels.get(name, name)


def pct(r, key="telephoto_pct"):
    return float(r[key]) if r and r[key] not in ("", None) else None


def crop_line(d):
    return ["2x crop shots count as main lens, not telephoto."] if d.crop_note else []


# ---------------------------------------------------------------- charts

def chart_headline(d):
    all_r, fav_r = d.section("all", "overall")[0], d.section("favorites", "overall")
    fav_r = fav_r[0] if fav_r else None
    n_cams = len(d.cameras())
    parts = [header("Would I miss the zoom lens?", f"Telephoto share of my rear-camera photos, {n_cams} cameras")]
    stats = [(all_r, "of all my photos", BLUE, "all")]
    if fav_r and pct(fav_r) is not None:
        stats.append((fav_r, "of my favorites", ORANGE, "favorites"))
    for i, (r, label, color, key) in enumerate(stats):
        x = (PAD + 10, W / 2 + 30)[i]
        p = pct(r)
        dots = [f'<circle cx="{x + (k % 10) * 34 + 13}" cy="{520 + (k // 10) * 34 + 13}" r="13" '
                f'fill="{color if k < round(p) else EMPTY}"/>' for k in range(100)]
        parts.append(group(f"stat-{key}", [
            text(x, 420, f"{p:.0f}%", 140, weight=700, id_=f"hero-{key}"),
            text(x, 475, label, 30, INK_2, id_=f"hero-label-{key}"),
            group(f"dots-{key}", dots),
            text(x, 900, f"{int(r['telephoto_photos']):,} of {int(r['rear_photos']):,} photos", 24, INK_3,
                 id_=f"count-{key}"),
        ]))
    zooms = {}
    for r in d.cameras():
        if r["group"] in d.zoom:
            zooms.setdefault(d.zoom[r["group"]], []).append(d.label(r["group"]))
    if zooms:
        key_parts = [text(PAD + 10, 975, "ZOOM BY CAMERA", 20, INK_3, weight=600, id_="zoom-key-heading")]
        for i, z in enumerate(sorted(zooms, key=lambda z: float(z.rstrip("x")) if z.rstrip("x").replace(".", "").isdigit() else 0)):
            x, y = (PAD + 10, W / 2 + 30)[i % 2], 1020 + (i // 2) * 42
            key_parts.append(group(f"zoom-{z}", [text(x, y, z, 26, weight=700),
                                                 text(x + 60, y, ", ".join(zooms[z]), 22, INK_2)]))
        parts.append(group("zoom-key", key_parts))
    parts.append(footer(["Each dot = 1% of photos. Selfies left out."] + crop_line(d)))
    return svg(parts)


def chart_per_camera(d):
    cams = d.cameras()
    n = len(cams)
    top, bottom_limit = 330, 1130
    row_h = min(122, (bottom_limit - top) / max(n, 1))
    thick = min(32, (row_h - 20) / 2)
    max_p = max([pct(r) or 0 for r in cams] +
                [pct(d.get("favorites", "camera", r["group"])) or 0 for r in cams] + [10])
    scale_max = math.ceil(max_p / 10) * 10
    x0, x1 = 330, W - PAD - 70
    scale = (x1 - x0) / scale_max
    parts = [header("How often I zoom, by camera", "Share of rear-camera photos shot on the telephoto lens"),
             legend([("All photos", BLUE), ("Favorites", ORANGE)])]
    bottom = top + row_h * n - (row_h - 2 * thick - 4) + 10
    grid = []
    for p in range(0, scale_max + 1, 10):
        x = x0 + p * scale
        grid.append(f'<line x1="{x:.1f}" y1="{top - 20}" x2="{x:.1f}" y2="{bottom:.1f}" stroke="{GRID}" '
                    f'stroke-width="{2 if p == 0 else 1}"/>')
        grid.append(text(x, bottom + 38, f"{p}%", 22, INK_3, anchor="middle"))
    parts.append(group("grid", grid))
    any_small = False
    for i, r in enumerate(cams):
        name, label = r["group"], d.label(r["group"])
        y = top + i * row_h
        row = [text(PAD, y + 30, label[:20], 28 if n <= 9 else 24, weight=600, id_=f"label-{label}")]
        if name in d.zoom:
            row.append(text(PAD, y + 62, f"{d.zoom[name]} telephoto", 21, INK_2, id_=f"zoom-{label}"))
        for j, (subset, color) in enumerate((("all", BLUE), ("favorites", ORANGE))):
            rr = d.get(subset, "camera", name)
            p = pct(rr)
            if p is None:
                continue
            by = y + j * (thick + 4)
            mark = "*" if "small sample" in rr["notes"] else ""
            any_small |= bool(mark)
            row.append(bar(x0, by, max(p * scale, 2), thick, color, f"bar-{subset}-{label}"))
            row.append(text(x0 + p * scale + 12, by + thick - 8, f"{p:.0f}%{mark}", 22, INK, weight=600,
                            id_=f"value-{subset}-{label}"))
        parts.append(group(f"row-{label}", row))
    total = d.section("all", "overall")[0]
    notes = (["* Fewer than %d favorites, so treat as rough." % d.small] if any_small else []) + crop_line(d)
    notes.append(f"{int(total['rear_photos']):,} rear-camera photos.")
    parts.append(footer(notes))
    return svg(parts)


def chart_per_year(d):
    excluded = {str(y) for y in d.config.get("chart_exclude_years", [])}
    rows = [r for r in d.section("all", "year")
            if int(r["rear_photos"]) >= d.small and pct(r) is not None and r["group"] not in excluded]
    rows.sort(key=lambda r: int(r["group"]))
    if len(rows) < 2:
        return None
    years = [int(r["group"]) for r in rows]
    vals = [pct(r) for r in rows]
    scale_max = math.ceil((max(vals + [10]) + 5) / 10) * 10  # headroom so top labels clear the axis
    x0, x1, ytop, ybot = PAD + 70, W - PAD - 40, 400, 1080
    sx = (x1 - x0) / (len(years) - 1)
    sy = (ybot - ytop) / scale_max
    px = lambda i: x0 + i * sx
    py = lambda v: ybot - v * sy
    parts = [header("How often I zoom, year by year", "Share of rear-camera photos shot on the telephoto lens")]
    grid = []
    for p in range(0, scale_max + 1, 10):
        grid.append(f'<line x1="{x0}" y1="{py(p):.1f}" x2="{x1}" y2="{py(p):.1f}" stroke="{GRID}" '
                    f'stroke-width="{2 if p == 0 else 1}"/>')
        grid.append(text(x0 - 20, py(p) + 8, f"{p}%", 22, INK_3, anchor="end"))
    step = 1 if len(years) <= 12 else 2
    for i, y in enumerate(years):
        if i % step == 0 or i == len(years) - 1:
            grid.append(text(px(i), ybot + 44, f"'{str(y)[2:]}", 22, INK_3, anchor="middle"))
    parts.append(group("grid", grid))
    pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vals))
    parts.append(f'<polyline id="line-all" points="{pts}" fill="none" stroke="{BLUE}" stroke-width="5" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
    parts.append(group("dots", [f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="10" fill="{BLUE}" '
                                f'stroke="{SURFACE}" stroke-width="4"/>' for i, v in enumerate(vals)]))
    # Label first, peak and latest; put a label below its dot when the line arrives from above.
    labels = []
    middle = range(1, len(vals) - 1)
    peak_i = max(middle, key=lambda i: vals[i]) if len(vals) > 2 else 0
    for i, id_ in ((0, "label-first"), (peak_i, "label-peak"), (len(vals) - 1, "label-latest")):
        if any(l[0] == i for l in labels):
            continue
        below = 0 < i and vals[i - 1] > vals[i] and id_ != "label-peak"
        labels.append((i, text(px(i), py(vals[i]) + (52 if below else -30), f"{vals[i]:.0f}%",
                               30 if id_ == "label-peak" else 26, INK if id_ == "label-peak" else INK_2,
                               weight=700 if id_ == "label-peak" else 600, anchor="middle", id_=id_)))
    parts.append(group("labels", [l[1] for l in labels]))
    skipped = [r["group"] for r in d.section("all", "year") if int(r["rear_photos"]) < d.small]
    notes = []
    if skipped:
        notes.append(f"Left out (fewer than {d.small} photos): {', '.join(skipped)}.")
    if excluded:
        notes.append(f"Left out (partial year): {', '.join(sorted(excluded))}.")
    parts.append(footer(notes + crop_line(d) + ["The latest year may be year to date."]))
    return svg(parts)


def chart_lens_mix(d):
    cams = d.cameras()
    if not any(int(r["ultrawide_photos"]) for r in cams):
        return None  # no ultra-wide lenses configured - nothing to show beyond the per-camera chart
    three = [r for r in cams if int(r["ultrawide_photos"]) and int(r["telephoto_photos"])]
    rows = [(d.label(r["group"]), r["group"], [pct(r, k) for k in ("ultrawide_pct", "main_pct", "telephoto_pct")])
            for r in cams]
    if len(three) > 1:
        tot = {k: sum(int(r[k]) for r in three) for k in ("ultrawide_photos", "main_photos", "telephoto_photos", "rear_photos")}
        rows.append(("Combined", "all three lenses",
                     [100 * tot[k] / tot["rear_photos"] for k in ("ultrawide_photos", "main_photos", "telephoto_photos")]))
    n = len(rows)
    top, x0, x1, gap = 345, 330, W - PAD, 2
    row_h = min(100, (1110 - top) / n)
    thick = min(48, row_h - 40)
    items = [("0.5x ultra-wide", AQUA), ("1x main", MAIN_GREY), ("Telephoto", VIOLET)]
    parts = [header("Which lens did I actually use?", "Share of rear-camera photos by lens, per camera"), legend(items)]
    for i, (label, sub_key, pcts) in enumerate(rows):
        combined = sub_key == "all three lenses"
        y = top + i * row_h + (20 if combined else 0)
        if combined:
            sub = "all three lenses"
        else:
            z = d.zoom.get(sub_key)
            sub = (f"{z} tele" if z else "tele") + (" + ultra-wide" if pcts[0] else ", no ultra-wide")
        row = [text(PAD, y + 26, label[:20], 26, weight=700 if combined else 600, id_=f"label-{label}"),
               text(PAD, y + 56, sub, 20, INK_2, id_=f"sub-{label}")]
        if combined:
            row.insert(0, f'<line x1="{PAD}" y1="{y - 22}" x2="{x1}" y2="{y - 22}" stroke="{GRID}" stroke-width="2"/>')
        live = [(name, color, p) for (name, color), p in zip(items, pcts) if p]
        x, span = x0, (x1 - x0) - gap * (len(live) - 1)
        for j, (name, color, p) in enumerate(live):
            w = span * p / 100
            row.append(bar(x, y, w, thick, color, f"seg-{name.split()[-1]}-{label}", j == 0, j == len(live) - 1))
            if w >= len(f"{p:.0f}%") * 15 + 12:
                row.append(text(x + w / 2, y + thick / 2 + 9, f"{p:.0f}%", 24, "#ffffff" if color == VIOLET else INK,
                                weight=700, anchor="middle", id_=f"value-{name.split()[-1]}-{label}"))
            x += w + gap
        parts.append(group(f"row-{label}", row))
    last = rows[-1][2]
    notes = [f"A main + ultra-wide camera keeps the 0.5x and 1x shots: {100 - last[2]:.0f}% of "
             + ("these" if len(three) > 1 else "my") + " photos."]
    parts.append(footer(notes + (["1x includes 2x crop shots. Selfies left out."] if d.crop_note else ["Selfies left out."])))
    return svg(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=Path.home() / "Desktop" / "lens_usage.csv")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("charts"))
    args = ap.parse_args()
    d = Data(args.csv.expanduser(), json.loads(args.config.read_text()))
    args.out.mkdir(parents=True, exist_ok=True)
    for name, fn in (("1-headline", chart_headline), ("2-per-camera", chart_per_camera),
                     ("3-per-year", chart_per_year), ("4-lens-mix", chart_lens_mix)):
        result = fn(d)
        if result is None:
            print(f"skipped {name} (not enough data)")
            continue
        (args.out / f"{name}.svg").write_text(result)
        print(f"wrote {args.out / f'{name}.svg'}")


if __name__ == "__main__":
    main()
