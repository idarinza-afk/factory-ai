---
name: boq-and-tender-documents
description: Prepare a bill of quantities / tender package structure without inventing prices.
tools: make_machine_list, make_part_list, workspace_write
---
## Structure
1. Machines and equipment (make_machine_list).
2. Installation: mechanical, piping, electrical, controls - each with quantities and units.
3. Utilities to point of connection; civil works (by customer unless agreed).
4. Engineering, documentation, FAT/SAT, training, spare parts, warranty.
5. Exclusions and assumptions.
## Rule
Quantities and units are filled; every price cell stays blank unless the engineer supplies it.
