---
name: utilities-calculation
description: Total line utilities: power and transformer, compressed air, water, steam, heat loads and pumps.
tools: utilities_summary, heat_load, pump_power, pneumatic_cylinder
---
## Method
1. Collect per machine: kW, air NL/min, water L/h, steam kg/h (from spec sheets; ask when missing).
2. Missing air: estimate from cylinders with pneumatic_cylinder; missing steam: heat_load; pumps: pump_power.
3. utilities_summary with diversity 0.7-0.85 (state it).
4. Present connected vs demand load, transformer kVA, compressor size (+30 % margin), water m3/h, steam kg/h.

## Checks
- Units: kW vs kVA, NL/min (free air) vs L/min at pressure.
- Peak events (CIP, start-up heating) can exceed the running average - list them separately.
