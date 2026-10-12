"""Print every camera/EXIF field for ~20 photos spread across the library's history.

READ-ONLY: osxphotos reads a temporary copy of the Photos database. Nothing is
exported, edited, or written. Use this to see real field names and values before
building anything.

Usage:  python sample_fields.py [N] [--library PATH]      (N defaults to 20)
"""
import argparse
import dataclasses

import osxphotos

ap = argparse.ArgumentParser()
ap.add_argument("n", nargs="?", type=int, default=20)
ap.add_argument("--library", help="path to a .photoslibrary (default: system library)")
args = ap.parse_args()
n = args.n
db = osxphotos.PhotosDB(dbfile=args.library) if args.library else osxphotos.PhotosDB()
photos = [p for p in db.photos(movies=False) if p.exif_info and p.exif_info.camera_model]
photos.sort(key=lambda p: p.date)
print(f"Photos with camera info: {len(photos)}\n")
step = max(1, len(photos) // n)
for p in photos[::step][:n]:
    print(f"date={p.date:%Y-%m-%d}  favorite={p.favorite}  ismovie={p.ismovie}")
    for name, value in dataclasses.asdict(p.exif_info).items():
        if name not in ("latitude", "longitude"):  # location isn't needed; keep it off screen
            print(f"    exif_info.{name} = {value!r}")
    print()
