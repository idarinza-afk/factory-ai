# Contributing to Improvise

There are two ways to help.

## A. Contribute code and knowledge (no project data needed)

Open a Pull Request against this repository with:
- New calculation tools (`improvise/calc/`) — unit tests required
- Knowledge base articles (`improvise/knowledge_base/*.md`) — written in your own words; do not copy copyrighted textbooks or standards
- Machine templates and document templates

## B. Help train the shared model (Community LoRA)

1. Use Improvise as usual, and `verify` only the cases that have been proven on site.
2. Build a contribution pack:
   ```
   improvise contribute --name "Display name" --secret "Customer name" --secret "Project name"
   ```
   - Emails, phone numbers, URLs, tax IDs, prices, company names and every term passed with `--secret` are removed automatically.
   - **You review and approve every record yourself.** Skip anything you are unsure about.
3. Submit the resulting `contribution.jsonl` as a Pull Request to the community dataset repository (opening in a later phase).
   Contributed data is licensed under CC-BY-4.0.
4. CI scans incoming packs for leaked personal data and duplicates, and maintainers review them before merging.
5. A new Community LoRA is trained every quarter and is **released only if it scores better than the previous version on the benchmark**.

### Do not submit
Confidential customer information, commercial prices, drawings covered by an NDA, personal data, or safety-related code.

### Next phase: federated learning
Each user trains locally and shares only the weight differences (LoRA deltas), so the data never leaves their machine.
