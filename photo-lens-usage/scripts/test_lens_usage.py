"""Tests for lens_usage.py using made-up photo records with hand-worked answers.

Run from this folder:  python3 -m unittest test_lens_usage -v
These never touch a real Photos library.
"""
import unittest

from lens_usage import (
    FRONT, MAIN, MISSING, NO_LENS, TELEPHOTO, ULTRA_WIDE,
    build_report, classify, inventory, lens_key, resolve_model, sanity_failures, share,
)

P15_TELE = "iPhone 15 Pro Max back triple camera 15.66mm f/2.8"
P15_MAIN = "iPhone 15 Pro Max back triple camera 6.765mm f/1.78"  # 2x crops also land here
P15_ULTRA = "iPhone 15 Pro Max back triple camera 2.22mm f/2.2"
P15_FRONT = "iPhone 15 Pro Max front TrueDepth camera 2.69mm f/1.9"
P7_TELE = "iPhone 7 Plus back dual camera 6.6mm f/2.8"
P7_MAIN = "iPhone 7 Plus back dual camera 3.99mm f/1.8"

CONFIG = {
    "my_cameras": ["iPhone 7 Plus", "iPhone 15 Pro Max", "iPhone 16 Pro Max", "Galaxy S24 Ultra"],
    "telephoto": [P7_TELE, P15_TELE, "iPhone 15 Pro Max back camera 15.66mm f/2.8", "Galaxy S24 Ultra @ 6.30mm"],
    "ultrawide": [P15_ULTRA, "Galaxy S24 Ultra @ 2.20mm"],
    "front": ["Galaxy S24 Ultra @ 3.10mm"],
    "crop_note_cameras": ["iPhone 15 Pro Max", "iPhone 16 Pro Max"],
    "overall_label": "All my cameras",
}


def rec(model, lens, year, favorite=False, focal=None, make="Apple"):
    return {"camera_make": make, "camera_model": model, "lens_model": lens,
            "focal_length": focal, "year": year, "favorite": favorite}


def galaxy(focal, year=2025, favorite=False):
    """Android-style record: no lens string, only a focal length."""
    return rec("Galaxy S24 Ultra", MISSING, year, favorite, focal, make="samsung")


# Hand-worked expectations:
#   15 Pro Max: 4 tele, 2 ultra-wide, 4 main, 2 selfies, 1 missing -> 13 total, 10 rear
#               tele 40.0%, ultra-wide 20.0%, main 40.0%
#   7 Plus:     2 tele (one labelled just "iPhone"), 3 main -> 5 total, tele 40.0%
#   16 Pro Max: 1 selfie only -> no rear photos -> no percentage
#   Galaxy:     1 tele, 1 ultra-wide, 2 main, 1 selfie (via config) -> 5 total, 4 rear, tele 25.0%
#   iPhone 12, iPhone 17 Pro: not my cameras -> ignored
#   Overall:    7 tele / 19 rear = 36.8%; ultra-wide 3/19 = 15.8%; 24 photos total
FAKE = [
    rec("iPhone 15 Pro Max", P15_TELE, 2024, favorite=True),
    rec("iPhone 15 Pro Max", P15_TELE, 2024),
    rec("iPhone 15 Pro Max", P15_TELE, 2024),
    rec("iPhone 15 Pro Max", "iPhone 15 Pro Max back camera 15.66mm f/2.8", 2025, favorite=True),
    rec("iPhone 15 Pro Max", P15_MAIN, 2024, favorite=True),
    rec("iPhone 15 Pro Max", P15_MAIN, 2024, favorite=True),
    rec("iPhone 15 Pro Max", P15_MAIN, 2024),
    rec("iPhone 15 Pro Max", P15_MAIN, 2024),
    rec("iPhone 15 Pro Max", P15_ULTRA, 2024, favorite=True),
    rec("iPhone 15 Pro Max", P15_ULTRA, 2024),
    rec("iPhone 15 Pro Max", P15_FRONT, 2024, favorite=True),
    rec("iPhone 15 Pro Max", P15_FRONT, 2024),
    rec("iPhone 15 Pro Max", MISSING, 2024),
    rec("iPhone 7 Plus", P7_TELE, 2017),
    rec("iPhone", P7_TELE, 2017, favorite=True),  # generic model name
    rec("iPhone 7 Plus", P7_MAIN, 2017),
    rec("iPhone 7 Plus", P7_MAIN, 2017),
    rec("iPhone 7 Plus", P7_MAIN, 2017),
    rec("iPhone 16 Pro Max", "iPhone 16 Pro Max front TrueDepth camera 2.69mm f/1.9", 2024),
    galaxy(6.3, favorite=True),
    galaxy(2.2),
    galaxy(6.4),
    galaxy(6.4),
    galaxy(3.1),
    rec("iPhone 12", "iPhone 12 back dual wide camera 4.2mm f/1.6", 2024, favorite=True),
    rec("iPhone 17 Pro", "iPhone 17 Pro back triple camera 16.891mm f/2.8", 2026, favorite=True),
]


def find(rows, photos, section, group):
    matches = [r for r in rows if (r["photos"], r["section"], r["group"]) == (photos, section, group)]
    assert len(matches) == 1, f"expected one row for {photos}/{section}/{group}, got {len(matches)}"
    return matches[0]


class TestPieces(unittest.TestCase):
    def test_resolve_model(self):
        self.assertEqual(resolve_model(rec("iPhone", P7_TELE, 2017)), "iPhone 7 Plus")
        self.assertEqual(resolve_model(rec("iPhone (New model)", P15_MAIN, 2024)), "iPhone 15 Pro Max")
        self.assertEqual(resolve_model(rec(MISSING, P7_MAIN, 2016)), "iPhone 7 Plus")
        self.assertEqual(resolve_model(rec("iPhone XS Max", P7_MAIN, 2016)), "iPhone XS Max")
        self.assertEqual(resolve_model(rec("iPhone", MISSING, 2008)), "iPhone")

    def test_lens_key_falls_back_to_focal_length(self):
        self.assertEqual(lens_key(rec("x", P15_TELE, 2024)), P15_TELE)
        self.assertEqual(lens_key(galaxy(6.3)), "Galaxy S24 Ultra @ 6.30mm")
        self.assertEqual(lens_key(rec("x", MISSING, 2008)), MISSING)

    def test_classify(self):
        self.assertEqual(classify(rec("x", P15_TELE, 2024), CONFIG), TELEPHOTO)
        self.assertEqual(classify(rec("x", P15_ULTRA, 2024), CONFIG), ULTRA_WIDE)
        self.assertEqual(classify(rec("x", P15_MAIN, 2024), CONFIG), MAIN)
        self.assertEqual(classify(rec("x", P15_FRONT, 2024), CONFIG), FRONT)
        self.assertEqual(classify(rec("x", "iPhone 17 Pro front FaceTime camera", 2026), CONFIG), FRONT)
        self.assertEqual(classify(galaxy(3.1), CONFIG), FRONT)  # front via config list
        self.assertEqual(classify(galaxy(6.4), CONFIG), MAIN)
        self.assertEqual(classify(rec("x", MISSING, 2024), CONFIG), NO_LENS)

    def test_share(self):
        self.assertEqual(share({TELEPHOTO: 1, MAIN: 3, FRONT: 50, NO_LENS: 9}), 25.0)
        counts = {TELEPHOTO: 1, ULTRA_WIDE: 1, MAIN: 2}
        self.assertEqual((share(counts, ULTRA_WIDE), share(counts, MAIN)), (25.0, 50.0))
        self.assertIsNone(share({FRONT: 2}))

    def test_inventory_counts_every_photo_once(self):
        rows = inventory(FAKE)
        self.assertEqual(sum(r["photos"] for r in rows), len(FAKE))
        seven = [r for r in rows if r["camera"] == "iPhone 7 Plus" and r["lens_key"] == P7_TELE]
        self.assertEqual(seven[0]["photos"], 2)  # generic "iPhone" merged in


class TestReport(unittest.TestCase):
    def setUp(self):
        self.rows = build_report(FAKE, CONFIG)

    def test_per_camera(self):
        r = find(self.rows, "all", "camera", "iPhone 15 Pro Max")
        self.assertEqual((r["total_photos"], r["rear_photos"], r["telephoto_photos"]), (13, 10, 4))
        self.assertEqual((r["telephoto_pct"], r["ultrawide_pct"], r["main_pct"]), (40.0, 20.0, 40.0))
        self.assertEqual((r["selfies_excluded"], r["missing_lens_excluded"]), (2, 1))
        self.assertIn("2x crops counted as main lens", r["notes"])

        r = find(self.rows, "all", "camera", "iPhone 7 Plus")
        self.assertEqual((r["total_photos"], r["telephoto_photos"], r["telephoto_pct"], r["ultrawide_pct"]),
                         (5, 2, 40.0, 0.0))
        self.assertNotIn("2x", r["notes"])

        r = find(self.rows, "all", "camera", "Galaxy S24 Ultra")
        self.assertEqual((r["total_photos"], r["rear_photos"], r["selfies_excluded"]), (5, 4, 1))
        self.assertEqual((r["telephoto_pct"], r["ultrawide_pct"], r["main_pct"]), (25.0, 25.0, 50.0))

    def test_camera_with_only_selfies_has_no_percentage(self):
        r = find(self.rows, "all", "camera", "iPhone 16 Pro Max")
        self.assertEqual((r["total_photos"], r["rear_photos"]), (1, 0))
        self.assertIsNone(r["telephoto_pct"])
        self.assertIn("small sample", r["notes"])

    def test_other_cameras_ignored(self):
        groups = {r["group"] for r in self.rows}
        self.assertNotIn("iPhone 12", groups)
        self.assertNotIn("iPhone 17 Pro", groups)

    def test_per_year(self):
        self.assertEqual(find(self.rows, "all", "year", 2017)["telephoto_pct"], 40.0)
        r = find(self.rows, "all", "year", 2024)
        self.assertEqual((r["telephoto_photos"], r["rear_photos"], r["telephoto_pct"]), (3, 9, 33.3))
        r = find(self.rows, "all", "year", 2025)  # 1 iPhone tele + Galaxy (1 tele, 1 UW, 2 main)
        self.assertEqual((r["telephoto_photos"], r["rear_photos"], r["telephoto_pct"]), (2, 5, 40.0))
        self.assertNotIn(2026, {r["group"] for r in self.rows if r["section"] == "year"})

    def test_overall(self):
        r = find(self.rows, "all", "overall", "All my cameras")
        self.assertEqual((r["total_photos"], r["rear_photos"], r["telephoto_photos"]), (24, 19, 7))
        self.assertEqual((r["telephoto_pct"], r["ultrawide_pct"]), (36.8, 15.8))

    def test_favorites(self):
        self.assertEqual(find(self.rows, "favorites", "camera", "iPhone 15 Pro Max")["telephoto_pct"], 40.0)
        self.assertEqual(find(self.rows, "favorites", "camera", "iPhone 7 Plus")["telephoto_pct"], 100.0)
        r = find(self.rows, "favorites", "overall", "All my cameras")
        self.assertEqual((r["rear_photos"], r["telephoto_photos"], r["telephoto_pct"]), (7, 4, 57.1))

    def test_sanity_checks_pass_on_good_data(self):
        self.assertEqual(sanity_failures(FAKE, self.rows, CONFIG), [])

    def test_sanity_checks_catch_a_broken_total(self):
        broken = [dict(r) for r in self.rows]
        find(broken, "all", "camera", "iPhone 7 Plus")["total_photos"] += 1
        self.assertTrue(sanity_failures(FAKE, broken, CONFIG))


if __name__ == "__main__":
    unittest.main()
