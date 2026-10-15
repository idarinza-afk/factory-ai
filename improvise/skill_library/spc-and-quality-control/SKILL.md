---
name: spc-and-quality-control
description: Statistical process control: capability, control limits, sampling for weights and dimensions.
tools: process_capability, workspace_write, run_python
---
## Method
1. Collect at least 20-25 subgroups of the characteristic (e.g. fill weight).
2. process_capability for Cp/Cpk against specs; target Cpk >= 1.33.
3. Control chart (X-bar/R or individuals): write a small script to compute limits and plot when needed.
4. React rules: points outside limits, runs, trends -> stop and investigate.
5. Document sampling plan and reaction plan.
