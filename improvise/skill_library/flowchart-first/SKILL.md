---
name: flowchart-first
description: Draw the process / machine sequence / workflow as a flowchart and get the user's approval before building anything. Use for any new logic or process.
tools: make_flowchart
---
## When
The user asks for a new process, machine sequence, control logic (PLC), workflow or procedure and has
not supplied a flowchart.

## Method
1. List the steps in order; mark decisions (sensor yes/no, OK/NOK, timeout) with both exits labelled.
2. Include start, normal cycle, stop, fault/alarm path and reset - for machines also manual/auto mode.
3. make_flowchart; fix every item in "problems" (unreachable steps, decisions with one exit).
4. Show the numbered text version and the file paths; ask: "Is this flow correct? What should change?"
5. Stop and wait. Build code or documents only after the user approves.

## Checks
- Every wait has a timeout leading to an alarm.
- The fault path ends in a safe state; safety functions are noted as hardware, not logic.
