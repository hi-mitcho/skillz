# Lens-string hints

Use these to *propose* telephoto / ultra-wide lists faster. Always confirm against the
user's own inventory: strings vary with iOS version, camera mode, and phone.

## How iPhone lens strings work

Format: `<model> <back|front> <descriptor> camera <focal>mm f/<aperture>`

- The descriptor ("dual", "triple", "dual wide", "iSight Duo", or nothing) reflects the
  **camera mode**, not the lens. Portrait mode, for example, can say "dual camera" on a
  triple-camera phone. **Identify the lens by its mm number**, and group every descriptor
  variant with the same mm value together.
- The word "telephoto" never appears. On a multi-lens phone, telephoto is the longest
  rear mm value (usually f/2.8), ultra-wide is the shortest, and main is in between.
- Firmware updates can change the mm text for the same lens (15 Pro Max main: `6.86mm`,
  later `6.765mm`; 17 Pro Max tele: `16.891mm` and occasionally `16.8906mm f/2.79883`).
- Older photos (roughly pre-2013) often have no lens string at all.
- Some photos report a generic model ("iPhone", "iPhone (New model)") or none; the
  lens string still names the real phone. `lens_usage.py` resolves these automatically.

## Observed iPhone values (real library, Oct 2026)

| Phone | Ultra-wide (0.5x) | Main (1x) | Telephoto |
|---|---|---|---|
| 7 Plus / 8 Plus | none | 3.99mm f/1.8 | 6.6mm f/2.8 (2x) |
| XS / XS Max | none | 4.25mm f/1.8 | 6mm f/2.4 (2x) |
| 11 Pro / Pro Max | 1.54mm f/2.4 | 4.25mm f/1.8 | 6mm f/2 (2x) |
| 13 Pro / Pro Max | 1.57mm f/1.8 | 5.7mm f/1.5 | 9mm f/2.8 (3x) |
| 14 Pro / Pro Max | 2.22mm f/2.2 | 6.86mm f/1.78 | 9mm f/2.8 (3x) |
| 15 Pro | 2.22mm f/2.2 | 6.86 / 6.765mm f/1.78 | 9mm f/2.8 (3x) |
| 15 Pro Max | 2.22mm f/2.2 | 6.86 / 6.765mm f/1.78 | 15.66mm f/2.8 (5x) |
| 17 Pro / Pro Max | 2.22mm f/2.2 | 6.765mm f/1.78 | 16.891mm f/2.8 (4x) |
| 11, 12, 13 (non-Pro) | ~1.54mm f/2.4 ("dual wide") | 4.2–5.1mm f/1.6–1.8 | none |

## Crop zoom (important caveat)

On 14 Pro and later Pro models, **2x is a crop of the 48MP main sensor**, and the 17 Pro's
**8x is a crop of the telephoto**. Crops are recorded as the lens they came from, so:
- 2x shots count as **main**, which means telephoto share **undercounts** how often the
  person zoomed. List these phones in `crop_note_cameras` so the results flag it.
- 8x shots already count as telephoto. Don't add crop modes as separate lenses.

## Non-Apple cameras

Lens strings from Android phones and standalone cameras are inconsistent: some record a
lens model, many record only a focal length. When `lens_model` is missing,
`lens_usage.py` uses the key `<model> @ <focal>mm`. Read the inventory, group focal
lengths per camera (shortest = ultra-wide, longest = telephoto, as a starting
proposal), and have the user confirm. Don't assume specific values for non-Apple
devices; check the inventory every time.

Cameras with a **zoom lens** (most compacts, and DSLRs with zoom lenses) record a different
focal length for almost every shot, e.g. `C3030Z @ 6.60mm`, `@ 8.50mm`, `@ 10.70mm`. That's
one lens across a range, not separate lenses, so this skill's telephoto / ultra-wide split
doesn't fit them well. Usually leave such cameras out of `my_cameras`; if the person wants
them in, agree on a focal-length cut-off and list the matching keys.
