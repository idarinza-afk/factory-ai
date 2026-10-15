# Conveyors (belt, modular, roller, accumulation)

## What it does / working principle
Conveyors move product or packs between process steps at a controlled speed and spacing. A drive (gearmotor, often on a VFD) pulls a belt, chain or rollers over a supporting bed. Besides moving product, conveyors also space it (pitch), orient it, merge or divide lanes, and buffer it between machines.

## Main types and when to choose each
| Type | Choose when |
|---|---|
| Flat fabric/PU belt | Unpackaged food, small or soft items, smooth surface needed, inclines with a cleated belt |
| Modular plastic belt (acetal, PP, PE) | Washdown areas, curves, turning or side transfers, wet product; you can replace single modules |
| Wire mesh / flush grid | Product must drain, or air must pass through it (cooling, freezing, frying) |
| Powered roller (MDR, belt- or chain-driven) | Cases, totes, zoned accumulation in end-of-line areas |
| Gravity roller | Manual or low-rate handling of cases |
| Accumulation (zero or low back pressure) | You need a buffer between machines that stop at different times |

## Key specifications to ask for
- Belt type, material and food-contact compliance, open area %
- Width, length, height and its adjustment range, incline angle
- Speed range and drive (VFD control is typical)
- Load per metre, and product dimensions and stability
- Transfer type: dead plate, nose-bar, roller, side transfer
- Frame design (open frame, tool-free belt release), IP rating of drives

## Sizing / selection notes
- Pitch = product length + gap. Belt speed = rate × pitch (for example, products/min × mm gives mm/min).
- One worked source notes that forgetting the gap is a common mistake and leaves the line roughly 5–15% short of rate.
- Avoid running motors far below base speed (below about 10% of it). Choose the gear ratio so the VFD runs in a sensible band.
- V-curve rule of thumb: run the critical (bottleneck) machine steady. Set the machines around it with about 10% more recovery speed at each step away from it, and place accumulation between them.

## Integration with the line
Photo-eyes at machine infeeds and outfeeds signal low level, high level and full, which drive start, stop and speed changes. Size the buffers from the downtime events of the critical machine and the time to repair them. Transfers between belts of different heights or pitches are common points for jams and tipping.

## Hygiene and safety notes
EHEDG Doc. 43 covers hygienic belt conveyor design: open frames, minimal horizontal ledges, cleanable belt types and quick belt-tension release for wet cleaning. Guard nip points, drive ends and transfers. Fit e-stops along long runs.

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| Belt mistracking | Misaligned pulleys, uneven tension, build-up on rollers | Square the pulleys, clean the rollers, check the take-up |
| Products tipping at transfer | Height or speed mismatch, gap at the dead plate | Level the transfer, match speeds, shorten the gap |
| Jams at merge | Insufficient overspeed downstream | Check the VFD set-points and sensor positions |
| Modular belt sprocket skipping | Wear, thermal expansion, wrong catenary sag | Check the sprockets and the return-side sag |

## Sources
- https://en.wikipedia.org/wiki/Conveyor_system
- https://www.iki.com/products/case-and-tote/modular-plastic-belt-conveyors
- https://www.ehedg.org/fileadmin/user_upload/2016_10_Conveying_Clean_-_EHEDG_Conveyor_Guideline_Offers_Hygienic_Best_Practices.pdf
- https://industrialmonitordirect.com/blogs/knowledgebase/conveyor-belt-speed-calculation-for-boxpackage-handling-lines
- https://lineview.com/en/is-the-v-curve-theory-the-best-option-for-setting-accumulation-line-speed
- https://www.intralox.com/media/news/accumulation-maximizing-line-efficiency-and-production-volume
