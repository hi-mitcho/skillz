"""Which lens did I use? Lens-usage analysis of an Apple Photos library.

READ-ONLY: osxphotos reads a temporary copy of the Photos database. This script
only reads metadata. It never exports, edits, or deletes photos.

Usage (run with the Python inside the osxphotos pipx environment):
    python lens_usage.py inventory [--out inventory.csv]
    python lens_usage.py report --config config.json [--out ~/Desktop/lens_usage.csv]

A "lens key" identifies a lens: the EXIF lens string when the camera records one,
otherwise "<camera model> @ <focal length>mm". config.json lists which lens keys
count as telephoto / ultra-wide / front, and which cameras belong to the owner.
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

MISSING = "(missing)"
GENERIC_MODELS = {MISSING, "iPhone", "iPhone (New model)", "iPad"}

TELEPHOTO, ULTRA_WIDE, MAIN, FRONT, NO_LENS = "telephoto", "ultra_wide", "main", "front", "missing_lens"
REAR = (TELEPHOTO, ULTRA_WIDE, MAIN)


# ---------------------------------------------------------------- reading

def load_records():
    """Read photos (no videos) from the Photos library into plain dicts."""
    import osxphotos  # imported here so tests run without a Photos library

    records = []
    for p in osxphotos.PhotosDB().photos(movies=False):
        exif = p.exif_info
        records.append({
            "camera_make": (exif.camera_make if exif else None) or MISSING,
            "camera_model": (exif.camera_model if exif else None) or MISSING,
            "lens_model": (exif.lens_model if exif else None) or MISSING,
            "focal_length": exif.focal_length if exif else None,
            "year": p.date.year,
            "favorite": bool(p.favorite),
        })
    return records


# ---------------------------------------------------------------- pure logic (tested)

def resolve_model(record):
    """Camera name for a photo. When the model field is missing or generic
    ("iPhone"), use the camera named at the start of the lens string."""
    model, lens = record["camera_model"], record["lens_model"]
    if model in GENERIC_MODELS and lens != MISSING:
        for side in (" back ", " front "):
            if side in lens:
                return lens.split(side)[0]
    return model


def lens_key(record):
    """The lens string, or '<model> @ <focal>mm' when no lens string is recorded."""
    if record["lens_model"] != MISSING:
        return record["lens_model"]
    if record.get("focal_length"):
        return f"{resolve_model(record)} @ {record['focal_length']:.2f}mm"
    return MISSING


def classify(record, config):
    key = lens_key(record)
    if key == MISSING:
        return NO_LENS
    if key in config.get("telephoto", ()):
        return TELEPHOTO
    if key in config.get("ultrawide", ()):
        return ULTRA_WIDE
    if key in config.get("front", ()) or " front " in f"{key} ":
        return FRONT
    return MAIN


def share(counts, bucket=TELEPHOTO):
    """% of rear-camera photos in `bucket`, or None when there are no rear photos."""
    rear = sum(counts.get(b, 0) for b in REAR)
    return None if rear == 0 else 100 * counts.get(bucket, 0) / rear


def tally(records, group_fn, config):
    groups = defaultdict(Counter)
    for r in records:
        groups[group_fn(r)][classify(r, config)] += 1
    return groups


def inventory(records):
    """One row per (camera, lens key) with photo count and first/last year."""
    counts, years = Counter(), defaultdict(list)
    for r in records:
        key = (resolve_model(r), lens_key(r))
        counts[key] += 1
        years[key].append(r["year"])
    rows = [{"camera": cam, "lens_key": lens, "photos": n,
             "first_year": min(years[(cam, lens)]), "last_year": max(years[(cam, lens)])}
            for (cam, lens), n in counts.items()]
    return sorted(rows, key=lambda r: (r["camera"], -r["photos"]))


def build_report(records, config):
    """Rows for per-camera, per-year and overall sections, for all photos and favorites."""
    cameras = config["my_cameras"]
    overall_label = config.get("overall_label", "All my cameras")
    small = config.get("small_sample", 30)
    crop_cams = set(config.get("crop_note_cameras", ()))
    mine = [dict(r, camera=resolve_model(r)) for r in records]
    mine = [r for r in mine if r["camera"] in cameras]
    rows = []
    for subset, recs in (("all", mine), ("favorites", [r for r in mine if r["favorite"]])):
        sections = (("camera", tally(recs, lambda r: r["camera"], config), cameras),
                    ("year", tally(recs, lambda r: r["year"], config), None),
                    ("overall", tally(recs, lambda r: overall_label, config), None))
        for section, groups, order in sections:
            for group in order or sorted(groups):
                c = groups.get(group, Counter())
                if sum(c.values()) == 0:
                    continue
                rear = sum(c[b] for b in REAR)
                pct = lambda b: None if rear == 0 else round(share(c, b), 1)
                notes = []
                if rear < small:
                    notes.append("small sample")
                if section == "camera" and group in crop_cams:
                    notes.append("2x crops counted as main lens")
                rows.append({
                    "photos": subset, "section": section, "group": group,
                    "total_photos": sum(c.values()), "rear_photos": rear,
                    "telephoto_photos": c[TELEPHOTO], "telephoto_pct": pct(TELEPHOTO),
                    "ultrawide_photos": c[ULTRA_WIDE], "ultrawide_pct": pct(ULTRA_WIDE),
                    "main_photos": c[MAIN], "main_pct": pct(MAIN),
                    "selfies_excluded": c[FRONT], "missing_lens_excluded": c[NO_LENS],
                    "notes": "; ".join(notes),
                })
    return rows


def sanity_failures(records, rows, config):
    """List of human-readable failures; empty means every check passed."""
    expected = sum(1 for r in records if resolve_model(r) in config["my_cameras"])
    failures = []
    for subset in ("all", "favorites"):
        overall = [r for r in rows if r["photos"] == subset and r["section"] == "overall"]
        if not overall:
            continue
        o = overall[0]
        for section in ("camera", "year"):
            for field in ("total_photos", "rear_photos", "telephoto_photos", "ultrawide_photos"):
                parts = sum(r[field] for r in rows if r["photos"] == subset and r["section"] == section)
                if parts != o[field]:
                    failures.append(f"{subset}: per-{section} {field} {parts} != overall {o[field]}")
        for r in (r for r in rows if r["photos"] == subset):
            if r["rear_photos"] + r["selfies_excluded"] + r["missing_lens_excluded"] != r["total_photos"]:
                failures.append(f"{subset}/{r['section']}/{r['group']}: buckets don't add up to total")
            if r["telephoto_photos"] + r["ultrawide_photos"] + r["main_photos"] != r["rear_photos"]:
                failures.append(f"{subset}/{r['section']}/{r['group']}: lenses don't add up to rear total")
    all_overall = [r for r in rows if r["photos"] == "all" and r["section"] == "overall"]
    got = all_overall[0]["total_photos"] if all_overall else 0
    if got != expected:
        failures.append(f"overall {got} != photos from my cameras counted directly {expected}")
    return failures


# ---------------------------------------------------------------- output

def print_inventory(records, rows):
    print(f"\nAll photos (videos excluded): {len(records)}")
    print(f"\n{'Camera':<28} {'Years':<10} {'Photos':>7}  Lens key")
    print("-" * 110)
    current = None
    for r in rows:
        if r["camera"] != current and current is not None:
            print()
        current = r["camera"]
        span = str(r["first_year"]) if r["first_year"] == r["last_year"] else f"{r['first_year']}-{r['last_year']}"
        print(f"{r['camera'][:28]:<28} {span:<10} {r['photos']:>7}  {r['lens_key']}")


def print_table(rows, photos, section, title):
    picked = [r for r in rows if r["photos"] == photos and r["section"] == section]
    print(f"\n{title}")
    print(f"  {'':<26} {'Tele %':>7} {'UW %':>6} {'Tele':>6} {'Rear':>6} {'Selfies':>8} {'No lens':>8}  Notes")
    print("  " + "-" * 100)
    for r in picked:
        fmt = lambda v: "n/a" if v is None else f"{v:.1f}%"
        print(f"  {str(r['group'])[:26]:<26} {fmt(r['telephoto_pct']):>7} {fmt(r['ultrawide_pct']):>6} "
              f"{r['telephoto_photos']:>6} {r['rear_photos']:>6} {r['selfies_excluded']:>8} "
              f"{r['missing_lens_excluded']:>8}  {r['notes']}")


def write_csv(rows, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--out", type=Path, default=Path("inventory.csv"))
    rep = sub.add_parser("report")
    rep.add_argument("--config", type=Path, required=True)
    rep.add_argument("--out", type=Path, default=Path.home() / "Desktop" / "lens_usage.csv")
    args = ap.parse_args(argv)

    records = load_records()
    if args.command == "inventory":
        rows = inventory(records)
        print_inventory(records, rows)
        write_csv(rows, args.out)
        print(f"\nSaved {len(rows)} rows to {args.out}")
        return 0

    config = json.loads(args.config.read_text())
    rows = build_report(records, config)
    if not rows:
        print("No photos matched my_cameras in the config. Check the names against the inventory.")
        return 1
    for subset, label in (("all", "ALL PHOTOS"), ("favorites", "FAVORITES ONLY")):
        print_table(rows, subset, "camera", f"{label}: per camera")
        print_table(rows, subset, "year", f"{label}: per year")
        print_table(rows, subset, "overall", f"{label}: overall")
    print("\nPercentages are of rear-camera photos. Selfies and photos without lens data are counted")
    print("but left out of the percentages.")
    failures = sanity_failures(records, rows, config)
    print("\nSanity checks: " + ("all passed" if not failures else "FAILED"))
    for f in failures:
        print(f"  FAIL {f}")
    mine = sum(1 for r in records if resolve_model(r) in config["my_cameras"])
    print(f"  library photos {len(records)} = my cameras {mine} + everything else {len(records) - mine}")
    write_csv(rows, args.out.expanduser())
    print(f"\nSaved {len(rows)} rows to {args.out.expanduser()}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
