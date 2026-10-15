---
name: proposal-package
description: Prepare a complete machine/line quotation package. Use whenever the user asks for a proposal, quotation or offer.
tools: recall_experience, takt_time, machines_required, layout_line, make_machine_list, utilities_summary, roi, make_manual
---
## Goal
A proposal the customer can approve: every deliverable present, every number traceable, no invented prices.

## Deliverables (always all of them)
1. Scope & basis of design - product, formats, capacity, shifts, utilities available, standards.
2. Process flow - ordered list of steps/machines.
3. Capacity calculation - takt, machine count with OEE, bottleneck (use the line tools).
4. 2D layout with dimensions in metres, and 3D views (hand off layout JSON to the 3D tool).
5. Machine specifications - one spec sheet per machine (skill: machine-spec-sheet).
6. Machine list - qty, capacity, power, dimensions, supplier; unknown prices left BLANK.
7. Utilities summary - power, air, water, steam (skill: utilities-calculation).
8. ROI evaluation when the customer is investing (skill: roi-evaluation).
9. Project schedule and exclusions / customer scope.

## Method
1. recall_experience for similar past projects and confirmed rules first.
2. Fill gaps by asking: product, formats, rate, shifts, room size, utilities, hygiene level.
3. Run the calculations, then layout, then lists. Keep one set of numbers across all documents.
4. Finish with an "Open points" list for the customer.

## Checks
- Same capacity and machine count in calculation, layout, list and ROI.
- Every price either supplied by the user or blank.
- Customer-scope items (civil, utilities to point of connection, permits) stated.
