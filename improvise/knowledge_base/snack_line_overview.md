# Snack production lines - design workflow (baseline, adjust to each customer site)

## 0. Data to get first
Product list and kg/h per product, shifts, bag weight and bag size, pieces per bag, film (metallized or clear),
shelf life (nitrogen flush or not), standards (GMP/HACCP, halal, export market), building size and available
energy (gas, steam, electricity). Ask for these before sizing anything.

## 1. Process line per product (see the snack_* articles)
- Extruded corn snack (hot / cooking extruder)
- Khao taen (glutinous rice cracker), baked to puff, sugar syrup drizzle and sesame
- Baked crispy snacks / crackers (sheeted dough, rotary cutter, tunnel oven)
- Pork sheet (moo pan / หมูแผ่น): minced pork sheets dried and roasted crisp
- Seasoning / coating shared by all lines

## 2. Packing and inspection (typical order)
Incline or bucket elevator -> product distribution -> multihead weigher (low drop heights, products are fragile)
-> VFFS pillow bag with nitrogen flush -> date coder -> checkweigher -> X-ray -> case packer -> case checkweigher
-> palletizer. (Some plants put the X-ray before the checkweigher; follow the customer's standard.)
Metallized film blocks metal detectors: inspect the closed bag with X-ray, or put a metal detector on the loose
product before the weigher.

## 3. Support systems
Heat source for ovens/dryers, compressed air, nitrogen generator, dust collection for seasoning, flour and sugar
(dust explosion risk - assess), humidity control in the packing room (sugar-coated products absorb moisture),
QC lab (moisture, aw, oil, seal strength, residual O2), HACCP critical control points (cooking/baking temperature,
foreign-body inspection), allergen plan (sesame, wheat, soy, milk...).

## 4. Deliverables
Process flowchart, 2D layout, 3D, machine list (prices blank), machine specs, utilities, ROI.

Tool: snack_packing_capacity converts kg/h and bag weight into bags/min, weigher and VFFS count and bag volume.
