# Case Packer

## What it does / working principle
A case packer groups primary or secondary packs into a set pattern and puts them into a shipping case. It may also erect the case beforehand and seal it afterwards (tape or hot-melt). Packing methods include pushing packs in from the side, dropping or placing them from above, or folding a flat blank around the group (wrap-around).

## Main types and when to choose each
| Type | Choose when |
|---|---|
| Top-load / pick-and-place (often robotic) | Mixed formats, fragile items, frequent changeovers |
| Drop packer | Rigid, stable products (bottles, cans), simple and fast |
| Side-load | Cartons and stable packs pushed horizontally into an open case |
| Wrap-around | High volume, long runs, rigid uniform products; blanks cost less than pre-formed cases |
| Tray / shelf-ready packer | Retail-ready display trays, often with hoods |

One trade comparison gives roughly 10–30 cases/min for top/side-load (intermittent) and 20–60+ cases/min for wrap-around (typical). Wrap-around changeovers are longer, and the blanks must be cut to tighter tolerances.

## Key specifications to ask for
- Case or blank sizes, patterns, pack count and orientation per case
- Rate (cases/min and packs/min), changeover time, number of formats
- Case erector and sealer type, glue or tape, case magazine autonomy
- Gripper or end-of-arm tool design per format (robotic)
- Board specs, and the maximum case weight the machine handles

## Sizing / selection notes
- Packs/min ÷ packs per case = cases/min. Add margin so the packer can catch up after upstream stops (see the V-curve note in the conveyors article).
- Robotic packers trade some top speed for flexibility. For a robot, check the cycle time per pick and the number of packs picked per cycle.
- The type of packaging material used (RSC case versus wrap-around blank) affects running cost as much as the machine price does.

## Integration with the line
Upstream: accumulation and lane dividers or collators feed the pattern. Downstream: case coder or labeller, case checkweigher, palletiser. Signals: infeed full or empty, case magazine low, glue fault, and "missing pack" reject.

## Hygiene and safety notes
Secondary packaging area. Guard the robot cells and pushers with interlocked fencing or light curtains. Glue units have hot surfaces.

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| Packs falling over at collation | Lane pressure, speed mismatch | Accumulation pressure, guides, speeds |
| Case not squared / open flaps | Board quality, glue or tape faults | Compression section, glue nozzles, board storage |
| Robot mispicks | Product position variance, vacuum cups | Cup condition, vacuum level, vision or sensor teach |
| Jams at case erector | Blank warp, magazine feed | Board humidity, magazine settings |

## Sources
- https://img0.hospitalityhub.com.au/case-packer-vs-wrap-around-case-packer-which-packing-method-suits-your-line/f/27653
- https://lineview.com/en/is-the-v-curve-theory-the-best-option-for-setting-accumulation-line-speed
