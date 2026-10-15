---
name: conveyor-design
description: Size a product conveyor: speed from rate and pitch, belt pull, motor power, accumulation.
tools: conveyor_sizing, buffer_size
---
## Method
1. Rate (products/min) and pitch (product length + gap) -> speed. Typical packaging conveyors 10-60 m/min.
2. conveyor_sizing with friction 0.3 (slider bed) or 0.05 (roller bed); add incline if any.
3. Accumulation: buffer_size; accumulation needs low-friction belts/chains or zero-pressure rollers.
4. Select belt type: modular plastic (food, wash-down), PU flat belt (light, hygienic), chain (heavy, hot).

## Checks
- Speed jump between conveyors <= 20 % or use a spacer/timing screw.
- Transfers: dead plates or side transfer for small products; check product stability.
