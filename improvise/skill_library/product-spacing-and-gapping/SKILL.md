---
name: product-spacing-and-gapping
description: Separate touching products on conveyors (gapping, spacing, singulation) with a speed step-up, timing screw or metering belt; size both conveyors, sensors, drives and the control.
tools: product_spacing, conveyor_sizing, make_flowchart, plc_io_list, plc_generate_ladder, plc_simulate
---
## Principle
Products touching on the infeed (pitch = length L) need pitch L + gap on the outfeed. At the same rate
(products/min) the outfeed must run faster by the pitch ratio: v_out / v_in = (L + gap) / L.
Gap = L means the outfeed runs TWICE as fast as the infeed. Always calculate with product_spacing.

## Method
1. product_spacing -> both speeds and the ratio.
2. conveyor_sizing for EACH conveyor with its OWN speed: infeed pitch = L, outfeed pitch = L + gap.
3. Equipment: two conveyors with separate gear motors; VFD on the outfeed (often both) to set the ratio;
   photo-eye at the transfer (product present / jam) and one after it (gap check); start/stop and reset
   pushbuttons; stack light; MCB/MPCB per motor; 24 VDC supply; PLC; safety relay for E-stop
   (hardware safety circuit, not PLC logic).
4. Control logic: flowchart first (start, run, jam = transfer sensor blocked too long, gap fault = gap
   shorter than limit, stop, reset). Then a state-machine spec -> plc_generate_ladder -> plc_simulate with a
   product timeline. Never hand-write ladder.
5. Speeds via VFD references (analog or fieldbus); ratio as a parameter so it can be tuned on site.

## Checks
- Outfeed speed = ratio x infeed speed (not equal speeds).
- Product stability at the transfer (tall or light products may tip at high ratios).
- Gap check: gap_mm = sensor OFF time x outfeed speed.
