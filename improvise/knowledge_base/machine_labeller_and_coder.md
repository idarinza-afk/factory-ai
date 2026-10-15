# Labellers and Coders

## What it does / working principle
**Labellers** apply printed labels to packs.
- **Pressure-sensitive (self-adhesive):** labels on a liner web are peeled at a dispensing edge and wiped or rolled onto the product. This is the most common type.
- **Wet glue (cut-and-stack or roll-fed):** used for high-volume bottles.
- **Shrink sleeve:** a film tube is placed over the container and shrunk in a tunnel. Gives full-body decoration on shaped containers.
- **Print-and-apply:** prints variable data on the label and then applies it, typically for cases and pallets.

**Coders** print variable data such as date, lot code, barcode and 2D codes.
- **CIJ (continuous inkjet):** a jet of solvent ink droplets is charged and deflected onto the surface. Works on most materials and curved surfaces at high speed, and can print from a distance. The solvent must be topped up and the ink system needs maintenance.
- **TIJ (thermal inkjet):** cartridge-based, high resolution (typically 300 dpi or more). Works best on porous or semi-porous surfaces. Low maintenance, because the print head is in the cartridge.
- **TTO (thermal transfer overprint):** a heated print head melts ink from a ribbon onto flexible film. Used on wrappers, VFFS and thermoformers. Works in intermittent and continuous modes.
- **Laser (CO2 or fibre):** marks by ablating or changing the colour of the surface. No ink. Permanent marks. Higher capital cost. Needs fume extraction and laser guarding.
- **Large-character inkjet:** used for coding cases.

## Main types and when to choose each
- Flexible film on a packer → TTO.
- Cartons, porous board → TIJ.
- Cans, bottles, curved or wet surfaces, very high speed → CIJ or laser.
- No consumables wanted and suitable substrate → laser (test marks on samples first).

## Key specifications to ask for
- Line speed and print area, number of lines, resolution, and barcode grade needed
- Substrate samples for trials, the ink or ribbon type, consumables cost per print
- Label size, web width and roll diameter, accuracy of placement (labellers)
- Communication protocol for job selection from the line controller or MES, and code verification (vision)

## Sizing / selection notes
Consumable cost often outweighs machine price over its life. Ask for the cost per 1,000 codes. Speed limits depend on the length of the message and on resolution.

## Integration with the line
Job and data download from the line controller avoids typing errors. Vision verification with automatic rejection, or a "no code, no run" stop, protects against wrong dates and allergen mislabelling.

## Hygiene and safety notes
Watch for ink solvent vapours (CIJ) and laser radiation and fumes. Handle and store solvents and waste correctly.

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| Faint or missing code | Ribbon or ink low, print head dirty, wrong pressure | Consumables, head cleaning, head pressure |
| Smudged CIJ code | Wrong ink for substrate, condensation | Ink type, product surface dry |
| Label wrinkles / flags | Dispensing angle, speed mismatch, curved surface | Synchronise web and line speed, wipe brushes |
| Wrong data printed | Manual job entry | Use automated job download and verification |

## Sources
- https://www.packworld.com/coding-printing-labeling/article/13364035/comparing-coding-technologies
- https://www.packworld.com/machinery/coding-printing-labeling/article/13359844/comparing-inkjet-technologies-continuous-vs-thermal
- https://en.wikipedia.org/wiki/Continuous_inkjet
- https://en.wikipedia.org/wiki/Thermal_transfer_printing
- https://keyence.com/products/marker/inkjet-printers/resources/inkjet-printer-resources/factors-to-consider-when-choosing-between-industrial-continuous-inkjet-printing-vs-laser-coding.jsp
- https://www.bwpackaging.com/blog/automatic-bottle-labeling-machines
