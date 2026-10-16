---
name: conveyor-design
description: Size a product conveyor: speed, belt pull, wet/dry friction, starting torque, shaft load, gearmotor check, accumulation.
tools: conveyor_sizing, gearmotor_check, buffer_size
---
## Method
1. Rate (products/min) and pitch (product length + gap) -> speed. Typical packaging conveyors 10-60 m/min.
2. conveyor_sizing with the real belt_type (flat PU/PVC on slider bed, modular plastic, roller_bed) and condition
   (dry, wet = water/washdown/wet product, sticky = sauce, sugar, starch, fat). Ask which line it is if not said:
   the same conveyor that runs fine on a dry line can stall on a wet line.
3. Read ALL results, not only kW: starting_torque_Nm, required_gearbox_output_torque_Nm, drive_shaft_radial_load_N,
   slip_check. kW often stays small while torque and shaft load triple on a wet/sticky line.
4. Gearmotor: brands differ in gear ratio steps, rated output torque, output shaft diameter and permissible radial
   load. Pick a candidate from the brand's catalogue and run gearmotor_check with its datasheet values. Never assume
   datasheet values; if they are missing, list what to read from the datasheet.
5. Accumulation: buffer_size; accumulation needs low-friction belts/chains or zero-pressure rollers.

## Wet and sticky lines
- Wet flat belts suck onto a flat stainless slider bed: use perforated/grooved slider beds, UHMW strips or a roller
  bed, a belt with a structured underside and a lagged drive pulley; keep take-up tension so the pulley does not slip.
- Clean water lowers friction of modular plastic belts on UHMW (Rexnord: acetal 0.25 dry -> 0.21 water), but sauce,
  sugar or fat residue raises it.
- Wet/sticky friction values are allowances: measure motor current on site and save the result as a verified case.

## Shaft load
- If the pulley sits on the gearmotor shaft, the belt tensions T1 + T2 load that shaft: compare with the
  permissible radial load (position-corrected if the pulley is not at the shaft middle). If it is too high, use a
  hollow-shaft gearmotor on the pulley shaft (pulley shaft in its own bearings, torque arm) or a coupling.
- Chain/belt drive to the pulley: radial load on the gearmotor shaft = 2000 x T / d0 x fZ
  (fZ chain 1.25-1.4, V-belt 1.75, timing belt 2-2.5, flat belt 2.5).

## Checks
- Speed jump between conveyors <= 20 % or use a spacer/timing screw.
- Transfers: dead plates or side transfer for small products; check product stability.
