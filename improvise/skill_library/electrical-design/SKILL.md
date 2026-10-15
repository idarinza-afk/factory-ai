---
name: electrical-design
description: Concept electrical design for a machine or line - motor list, starters (DOL/VFD), protection, control voltage, safety circuit, PLC I/O wiring and the electrical diagrams.
tools: electrical_schematic, drive_torque, utilities_summary, plc_io_list
---
## Method
1. Motor list with kW from the mechanical calculations; starter per motor: DOL for fixed speed, VFD for speed
   control or soft start (VFD with STO for the safety circuit).
2. Protection: motor protection breaker (DOL) or MCB per VFD manual; main isolator; control supply MCB.
3. Control voltage 24 VDC; size the PSU for PLC + I/O + sensors + 30 %.
4. Safety: E-stop and guards through a safety relay / safety PLC to the required performance level
   (from the risk assessment). Safety is hardware, never standard PLC logic.
5. PLC I/O: plc_io_list (Pro) or a list of inputs/outputs; 20 % spare.
6. electrical_schematic -> power and control sheets (SVG/HTML) and a component list (CSV, no prices).
7. Utilities: connected load into utilities_summary for the transformer size.
## Note
Concept level for proposals. Cable sizing, breaking capacity, selectivity and code compliance are done and
signed by a qualified electrical engineer.
