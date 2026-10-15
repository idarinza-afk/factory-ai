# X-ray Inspection

## What it does / working principle
An X-ray tube sends a beam through the product onto a line-scan detector. The detector is usually a scintillator with a row of photodiodes. The detector builds an image strip by strip as the belt moves. Denser or higher-atomic-number materials absorb more X-rays and show up darker. Software compares each image with learned acceptance criteria and triggers a reject.

X-ray also performs quality checks: missing or broken items, fill level, mass estimation, and product trapped in the seal.

## Main types and when to choose each
- **Single-energy, top-down beam:** general packaged food. Good for metals (including stainless), glass, calcified bone, mineral stone and dense plastics or rubber.
- **Dual-energy:** compares two energy bands to tell materials apart by composition. It helps with low-contrast items such as flat glass, stone in nuts, and some bone or filled plastics. One source stresses it is not automatically more sensitive.
- **Side-view or multi-beam:** tall containers such as jars, cans and bottles, including glass in glass.
- **Bulk / pipeline X-ray:** unpacked product streams or pumped products.

## Key specifications to ask for
- Detectable sizes per contaminant type *in your product and pack*, demonstrated on samples
- Tube power (kV, W), detector pixel pitch, belt speed and width
- Inspection functions (contaminants, mass, fill, seal)
- Reject system and fail-safe features (as for metal detectors)
- Radiation leakage compliance, shielding curtains, and local licensing or registration requirements

## Sizing / selection notes
- Finer pixel pitch resolves smaller objects but can limit belt speed, because exposure time per line gets shorter.
- Thick, uneven or overlapping product reduces contrast. Single layers and consistent presentation improve detection.
- Low-density materials (most plastics, wood, paper, insects) may be hard or impossible to detect. Do not rely on X-ray alone for them.
- Required detection levels come from the HACCP study and customer codes, not from this note.

## Integration with the line
X-ray usually sits after final sealing, often combined with a checkweigher. It needs the same reject confirmation, bin-full and lockable-bin logic as metal detectors. Images and data can be logged for traceability.

## Hygiene and safety notes
The machine emits ionising radiation. Keep the shielding curtains intact and interlocks working. Follow national radiation regulations, and survey leakage after maintenance. Washdown versions exist for raw meat and poultry.

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| False rejects | Product variation (thickness, overlap), wrong learn | Re-learn, check product presentation and spacing |
| Missed test pieces | Sensitivity settings, worn tube output, detector calibration | Run the test card, check tube hours and calibration |
| Image streaks | Dirty belt or detector window, detector element fault | Clean, run flat-field calibration |
| Curtain damage | Tall or misaligned packs | Guides, curtain condition, leakage survey |

## Sources
- https://www.mt.com/us/en/home/library/know-how/product-inspection/PI-Guides/xray-inspection-guide.html
- https://www.packagingdigest.com/packaging-technologies/how-to-choose-between-single-or-dual-energy-x-ray-systems
- https://www.vareximaging.com/blogs/how-do-x-ray-detectors-work-in-food-inspection-systems/
