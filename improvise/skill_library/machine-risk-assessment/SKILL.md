---
name: machine-risk-assessment
description: Structure a machine safety risk assessment (ISO 12100 method) for a proposal or design review.
tools: search_knowledge
---
## Method (ISO 12100 steps)
1. Limits of the machine: use, space, time, people (operators, cleaners, maintenance).
2. Hazard identification per life phase: mechanical (crushing, shearing, entanglement), electrical,
   thermal, pneumatic stored energy, noise, ergonomics, cleaning chemicals.
3. Risk estimation: severity x probability of occurrence x frequency of exposure x possibility to avoid.
4. Risk reduction in order: inherently safe design -> guards and safety devices -> information for use.
5. Safety functions are specified with a required performance level (ISO 13849-1) and implemented in
   certified safety components - never in standard PLC logic.
## Output
Hazard table and the list of safety functions with required PL. Final sign-off by a competent person.
