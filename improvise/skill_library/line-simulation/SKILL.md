---
name: line-simulation
description: Simulate a line with stops and buffers to check real output, using a small Python program.
tools: workspace_write, run_python, line_capacity
---
## When
Static capacity looks fine but machines stop often, or buffer sizes must be justified.
## Method
1. Inputs per machine: rate, MTBF and MTTR (or stop frequency and duration); buffer sizes.
2. Write a discrete-time simulation (1 s steps, standard library only) with workspace_write:
   each machine produces if not stopped, not starved (upstream buffer > 0) and not blocked (downstream buffer not full).
3. run_python for one or more shifts with fixed random seeds; report output/h, starving/blocking per machine.
4. Rerun with bigger buffers or faster machines to show the effect.
## Checks
Simulated output must not exceed the static bottleneck rate; explain any big difference.
