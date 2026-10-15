---
name: maintenance-plan
description: Create a preventive maintenance plan and spare-parts list for machines.
tools: make_part_list, make_manual
---
## Method
1. Per machine: components that wear (belts, bearings, seals, knives, suction cups, sensors).
2. Interval by hours/cycles from supplier data; otherwise mark "to confirm".
3. Tasks: inspect / clean / lubricate / replace, with duration and skill level.
4. Spare parts classes: critical (stops the line, long lead time - keep in stock), wear (consumed regularly),
   standard (buy when needed). make_part_list with spare_class.
