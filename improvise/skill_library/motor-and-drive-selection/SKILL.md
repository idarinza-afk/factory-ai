---
name: motor-and-drive-selection
description: Select motors and drives: power, speed, gear ratio, VFD vs direct-on-line, efficiency class, IP rating.
tools: drive_torque, conveyor_sizing, gearmotor_check, pump_power, shaft_diameter
---
## Method
1. Load power from the right calculator (conveyor_sizing, pump_power, or force x speed).
2. Speed: required output rpm; gear ratio and torque with drive_torque (service factor 1.25-2.0 by duty: smooth, shocks, starts/hour).
3. Starting: DOL for small fixed-speed loads; VFD when speed must change, soft start is needed, or for energy saving on fans/pumps.
4. Motor: next IEC size, efficiency class IE3 or better, IP55 standard, IP66/69K stainless or wash-down motors in wet food zones.
5. Check: starting torque of the load (full conveyors, mixers, wet/sticky belts), duty cycle, ambient temperature, altitude.
6. Gearmotor from a real catalogue: gearmotor_check with the datasheet's rated output torque, output rpm, output shaft
   diameter, permissible radial load and fB. Brands differ - a 0.37 kW of one brand can have a smaller shaft and a
   lower radial load rating than another. Overhung load beyond the rating bends or breaks the output shaft.
## Output
Motor list: kW, rpm, ratio, torque, starter type, IP - suppliers and prices blank.
