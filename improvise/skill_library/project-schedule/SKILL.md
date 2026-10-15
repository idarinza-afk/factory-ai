---
name: project-schedule
description: Plan a machine/line project schedule (phases, durations, milestones) as a table or CSV for Excel.
tools: workspace_write
---
## Typical phases
Kick-off & URS -> design & approval -> procurement / manufacturing (machine lead times!) -> FAT ->
shipping -> installation -> commissioning & SAT -> training -> handover & warranty.
## Method
1. Ask contract date and required start-of-production date.
2. Use the user's supplier lead times; mark assumed ones.
3. Write the plan as CSV (task, start, end, duration, owner, depends on) with workspace_write so it opens in Excel.
4. Show the critical path and the milestones tied to payments.
