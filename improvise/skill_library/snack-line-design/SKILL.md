---
name: snack-line-design
description: Design a snack production line (extruded corn, khao taen, baked crisps, pork sheet) with seasoning, VFFS packing and inspection.
tools: snack_packing_capacity, takt_from_rate, machines_required, conveyor_sizing, batch_heat_up, make_flowchart, layout_line, layout_dxf, layout_3d, make_machine_list, utilities_summary, find_machine_model
---
## Method (baseline - adjust to the customer's site)
1. Ask for the data first if missing: kg/h per product, shifts, bag weight and size, film (metallized or clear),
   shelf life / nitrogen, standards (HACCP, halal, export), building and energy.
2. Process flow per product from the snack_* knowledge articles; draw it with make_flowchart for approval.
3. Packing: snack_packing_capacity (bags/min, weigher and VFFS count, bag volume from bulk density).
4. Order: elevator -> distribution -> multihead weigher -> VFFS + N2 -> coder -> checkweigher -> X-ray -> case
   packer -> case checkweigher -> palletizer, unless the customer's standard says otherwise.
5. Machines: look them up in the model library first (find_machine_model), then layout_line, layout_dxf, layout_3d.
6. Utilities (oven/dryer heat, air, N2, dust collection, humidity control) and the machine list (prices blank).
## Checks
- Khao taen: puffed by baking unless the customer asks for frying.
- Metallized film -> X-ray, not a metal detector on the closed bag.
- Sugar-coated products -> packing-room humidity control and barrier film.
- Allergens (sesame, wheat, soy, milk) -> cleaning plan and labels. Meat snacks -> cooking CCP, raw/cooked separation.
- Starch/sugar/seasoning dust -> dust collection and explosion risk assessment.
