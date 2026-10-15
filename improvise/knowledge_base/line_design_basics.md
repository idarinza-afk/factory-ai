# Production line design - working method

## 1. Start from demand, not from machines
Collect: product range and pack formats, daily/annual volume, peak season factor,
shifts and hours, planned stops (breaks, cleaning, changeover). Compute takt time
= available time / demand. Every machine must run faster than takt after losses.

## 2. Size each machine with expected OEE
Rated speed is a nameplate number. Effective rate = rated speed x expected OEE.
Typical planning OEE: 0.85 for simple, proven machines; 0.65-0.75 for complex
packaging machines (fillers, cartoners, case packers); lower for new technology.
Number of machines = target rate / effective rate, rounded up.

## 3. V-curve speed profile for packaging lines
The critical machine (usually the filler or the most expensive one) is the pace
setter. Machines upstream and downstream are rated faster, typically +10% to +30%
per step away from it, so short stops elsewhere do not starve or block it.

## 4. Buffers
Place accumulation between machines with frequent short stops. Buffer size =
downstream consumption rate x the upstream stop to ride through x safety factor.
Buffers before the critical machine protect it from starving; after it, from blocking.

## 5. Line balancing (manual or semi-automatic lines)
List tasks with times and precedence. Use takt as cycle time. Theoretical minimum
stations = total work content / cycle time. Line efficiency = work content /
(stations x cycle time); aim above 85%. Tasks longer than takt must be split or
parallelised.

## 6. Layout
Keep the material flow one-directional, avoid crossings of raw and finished
product (especially in food plants), keep 1.0-1.5 m operator and maintenance
aisles, allow space for changeover parts, utilities drops and forklift paths.
Straight lines are simplest; U-shape shortens operator walking and keeps start
and end near each other.

## 7. Deliverables checklist for a line proposal
Process flow diagram, 2D layout with dimensions, 3D views, machine list with
capacity and power, utility consumption (power, air, water, steam), machine
specifications, I/O and control philosophy, ROI evaluation, project timeline.
