# Multihead Weighers and Fillers (multihead, auger, piston/liquid, cup)

## What it does / working principle
Dosing equipment puts a target quantity of product into a pack.
- **Multihead (combination) weigher:** product is spread out by a top cone, then fed by radial feeders into pool hoppers and weigh hoppers. A computer picks the combination of hoppers whose total is closest to target, and discharges it down a chute. Booster hoppers add more possible combinations.
- **Auger filler:** a rotating screw delivers a volume per turn. It suits fine, non-free-flowing powders.
- **Volumetric cup filler:** fixed-volume cups are filled and dumped. It needs free-flowing product with a stable bulk density.
- **Piston filler:** a piston draws a set volume into a cylinder and pushes it out. It suits viscous liquids and pastes.
- **Other liquid fillers:** gravity or pressure overflow fillers (fill to a level), net-weight fillers (large containers), mass-flow fillers (Coriolis meter).

## Main types and when to choose each
| Product | Typical choice |
|---|---|
| Snacks, confectionery, frozen pieces, free-flowing pieces | Multihead weigher |
| Sticky fresh meat, cheese, salads | Multihead with belt or screw feeders |
| Flour, milk powder, spices, protein powder | Auger (servo) |
| Sugar, rice, salt, seeds | Cup filler (low cost) or multihead |
| Sauces, creams, purées | Piston or pump filler |
| Water-thin liquids filled to a visual level | Overflow filler |
| Drums, pails, totes | Net-weight filler |

## Key specifications to ask for
- Target weight range, accuracy (standard deviation) and speed *at your product*
- Number of heads and hopper volume (multihead). Number of fill lanes (liquid).
- Contact parts, IP rating and washdown rating, dust control
- Changeover time. Typical figures quoted in one trade comparison: auger tooling 30–90 min, cup size change 10–30 min.

## Sizing / selection notes
- One trade comparison quotes auger accuracy at about ±0.5–1% (servo) and cup accuracy at about ±1–3%, only for consistent-density products (typical).
- Cup fillers cannot correct for changes in bulk density. If density varies, pair the filler with a checkweigher feedback loop.
- A multihead must be specified for the product's flow behaviour (sticky, fragile, wet) and the speed of the bagger below it.

## Integration with the line
The doser and the packer exchange ready and dump signals. A timing hopper can shorten the drop into a VFFS. A checkweigher downstream gives feedback for automatic target correction.

## Hygiene and safety notes
Use smooth contact surfaces and quick-release hoppers. For powders, consider dust extraction and ATEX zoning. Guard hopper pinch points.

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| High give-away | Feed too heavy or light, too few heads in combination | Feeder amplitude, target settings, product flow |
| Weight drift | Load-cell zero drift, product sticking | Auto-zero, clean the hoppers, check calibration |
| Auger fill variation | Bridging, aeration, level in hopper varies | Agitator, hopper level control |
| Piston dripping | Worn seals, wrong nozzle cut-off | Seals, nozzle, suck-back setting |

## Sources
- https://en.wikipedia.org/wiki/Multihead_weigher
- https://img0.hospitalityhub.com.au/auger-filling-vs-volumetric-cup-filling-which-system-is-right-for-your-production-line/f/27569
- https://extension.okstate.edu/fact-sheets/filler-identification-and-selection-for-liquid-foods.html
