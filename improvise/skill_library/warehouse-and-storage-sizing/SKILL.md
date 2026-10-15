---
name: warehouse-and-storage-sizing
description: Size raw material and finished goods storage: pallet positions, area, racking.
tools: takt_from_rate, workspace_write
---
## Method
1. Daily flow in pallets = units per day / units per pallet (takt_from_rate gives units/day from a rate).
2. Days of stock per item (raw, packaging, finished) from the user -> pallet positions = flow x days x peak factor.
3. Racking choice: floor stacking, selective racking, drive-in, mobile; area per position incl. aisles.
4. Temperature zones (ambient, chilled, frozen) separately; dock doors from trucks per day.
