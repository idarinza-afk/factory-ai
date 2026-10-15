---
name: steam-and-heating
description: Size heating for cookers, blanchers, retorts, CIP heaters: heat load, steam demand, heat-up vs holding.
tools: heat_load, pipe_size
---
## Method
1. Continuous duty: heat_load with product flow, cp and temperature rise; add losses (10-25 %).
2. Batch heat-up: energy = mass x cp x dT (product + vessel + water) divided by heat-up time - often the peak.
3. Steam: kg/h = kW x 3600 / latent heat at supply pressure; size the steam main with pipe_size at 20-30 m/s for steam (check with steam tables).
4. Boiler: sum of simultaneous peaks + 15-20 % margin; condensate return improves efficiency.
## Note
Thermal processes for food safety (e.g. sterilisation F0 values) must be validated by a recognised process authority - the tool only sizes the energy.
