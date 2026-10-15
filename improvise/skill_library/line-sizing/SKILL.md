---
name: line-sizing
description: From demand to machine count: takt time, OEE-adjusted machines, V-curve speeds, bottleneck and buffers.
tools: takt_time, machines_required, line_capacity, buffer_size, recall_experience
---
## Method
1. Demand basis: units/day at PEAK season, shifts, hours, planned stops (breaks, CIP, changeovers).
2. takt_time -> required good output per hour.
3. Choose the critical machine (usually filler/forming/most expensive). Size it with machines_required
   using planning OEE: 0.85 simple proven machines, 0.65-0.75 complex packaging, lower for new technology.
4. V-curve: rate the machines upstream and downstream 10-30 % faster per step away from the critical one.
5. line_capacity on the full list: confirm the bottleneck IS the critical machine.
6. Buffers before and after the critical machine: buffer_size with the typical short stop to ride through.

## Checks
- Installed capacity / required >= 1.1 at the critical machine.
- No machine slower than the critical one after OEE.
- State the assumptions (OEE, shift pattern, stops) next to the result.
