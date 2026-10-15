---
name: read-machine-manual
description: Use machine manuals - find specifications, alarm/error codes, troubleshooting steps, maintenance intervals, wiring and settings. Use whenever a question is about a specific machine.
tools: lookup_alarm_code, search_knowledge
---
## Before
Manuals must be ingested once: `improvise ingest <manual.pdf>` (scanned manuals need OCR first).

## Method
1. Alarm or error code given -> lookup_alarm_code(code, machine) first; then search_knowledge for the
   troubleshooting section around that page.
2. Specification, setting or procedure -> search_knowledge with the machine name + key words
   (e.g. "TS-200 sealing temperature", "lubrication interval").
3. Quote the manual name and page for every fact; if the manual does not say it, say so - never fill
   gaps from general knowledge without marking them as general.
4. For procedures that involve opening guards or working on energised parts, remind the user of
   lock-out/tag-out and the manual's safety section.

## Output
Short answer, then: source (manual, page), steps from the manual, and what to check next.
