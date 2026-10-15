---
name: pneumatics-sizing
description: Choose cylinder bores and estimate compressed-air consumption for a machine.
tools: pneumatic_cylinder, utilities_summary
---
## Method
1. Required force (N) incl. friction and acceleration; supply pressure (usually 6 bar, design at 5 bar for margin).
2. pneumatic_cylinder with required_force_N and load factor 0.5-0.7 (dynamic) -> standard bore.
3. Air: cycles per minute per cylinder -> NL/min; add blow-offs and vacuum generators separately.
4. Sum into utilities.
