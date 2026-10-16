# Changelog

## v0.15 — 2026-10-16
### Added
- Snack knowledge: line overview, extruded corn, khao taen (baked), baked crisps + pork sheet, seasoning and packing.
- Skill snack-line-design; tool snack_packing_capacity; snack terms in the multilingual glossary.
- Challenge level 9 (snack packing capacity, khao taen flow in Thai).
- Datasheet questions require gearmotor_check.

## v0.14 — 2026-10-16
### Added
- conveyor_sizing: belt_type, condition (dry/wet/sticky), starting torque, belt tensions, drive shaft radial load,
  pulley slip check, transmission radial load (2000 x M / d0 x fZ).
- gearmotor_check: datasheet-based check of torque, starting torque, speed, radial load, shaft stress.
- Knowledge: conveyor drives on wet and dry lines (Rexnord friction tables, ISO 5048, SEW overhung load).
- Layout pass line per machine from the model library, mismatch warnings.
- Probe item: wet PU conveyor + gearmotor check (Thai).
### Fixed
- OEE: impossible performance is reported as an error; break warning only when planned time is the stated shift.

## v0.13 — 2026-10-16
### Added
- Model library: `improvise library learn|list|show`, tools find_machine_model and machine_model_details, one
  knowledge article per machine design; layout_line takes footprints, heights and clearances from `model_id`.
- Probe benchmark (benchmarks/probe.jsonl), level-8 challenge items, `forbid_tools` checks.
- pneumatic_cylinder `other_air_NL_min` -> machine_total_air_NL_min.
### Changed
- Agent sends back answers that skip a tool the question needs, or that promise work and stop.
- line_balance accepts after/depends_on/requires and comma-separated predecessors.

## v0.12 — 2026-10-16
### Added
- `improvise ui`: local web screen (standard library only). Chat with live tool steps, previews of produced files
  (SVG/HTML/3D viewer/CSV/Markdown/PLC code), approve/deny prompts for actions that change something, engineer rules,
  save answer as a case. Listens on 127.0.0.1 only; API calls need the per-session token; Host header checked.
### Fixed
- SQLite connections (experience memory, knowledge index) can be used from worker threads.

## v0.11 — 2026-10-16
### Added
- Challenge levels 6-7; benchmark checks with fixed values and alternative correct answers.
- Tool next-step hints (product_spacing, pneumatic_cylinder); pneumatic_cylinder quantity.
### Changed
- Empty replies from thinking models are retried once with thinking on; empty-reply retry in the agent.
- Tool reports (generated code, simulation verdicts, produced files) are appended to answers verbatim.
- Number audit asks for a clean rewritten answer.

## v0.10 — 2026-10-16
### Added
- LLM providers: OpenAI-compatible APIs and the Anthropic Messages API (`IMPROVISE_PROVIDER`, `IMPROVISE_API_BASE`,
  `IMPROVISE_API_KEY`); tool calls carry ids across providers.
- `ask_expert`: optional second brain (`IMPROVISE_EXPERT_*`), anonymised questions.
- Number audit of answers (`IMPROVISE_NUMBER_AUDIT=0` to disable).
- `batch_heat_up`; `machines_required` accepts per-shift/per-day targets.
### Changed
- Benchmark grader accepts x1000 unit scaling (NL/min vs m3/min); ROI skill uses staffing for labour savings.

## v0.9 — 2026-10-16
### Added
- layout_dxf (A3 DXF), layout_3d (OBJ + HTML viewer), electrical_schematic (power + control SVG/HTML, component CSV).
- 16 researched machine articles (knowledge_base/machine_*.md, sources listed in each).
- product_spacing, convert_units; skills electrical-design, product-spacing-and-gapping.
- Challenge benchmark (benchmarks/challenge.jsonl); answer guards provided by plugins.
- `cad` extra (ezdxf).

## v0.8 — 2026-10-16
### Added
- Flowchart first: `make_flowchart` (Mermaid + HTML preview, structure check) and the rule that new processes,
  sequences and control logic start with a flowchart the user approves.
- Machine manuals: `improvise ingest <pdf|folder>`, alarm-code index and `lookup_alarm_code`; skill read-machine-manual.
- Multilingual requests: engineering glossary (Thai, Chinese, Japanese, Vietnamese, Indonesian/Malay, Korean, German,
  Spanish) for tool routing, skills and knowledge search; multilingual benchmark questions.
- Pro: ladder logic generation (`plc_generate_ladder`, step-bit pattern, double-coil check) and skills
  ladder-logic, machine-troubleshooting, plc-io-signal-diagnosis.
### Changed
- Machine lists: model, supplier and price columns are always left for the engineer; a "Data status" column marks
  AI-filled rows "to confirm with supplier".

## v0.7 — 2026-10-16
### Added
- 20 more engineering skills (38 total) and calculators: drive_torque, shaft_diameter, pipe_size, air_receiver,
  cooling_load, process_capability, staffing, takt_from_rate.
- `improvise memory rules` / `memory delrule <id>`.
- Pro: 5 Pro skills (PLC program structure, I/O list & panel, IoT architecture, OEE dashboards, commissioning)
  and Pro connectors (Siemens TIA Portal, CODESYS).
### Changed
- The AI never fills prices in machine lists; team members' results include a tool record; stricter
  consultant review; relevant-skill hints per request instead of the full catalogue; 8k context by default.
### Benchmark
- Added per-hour takt and "typical prices" trap questions.

## v0.6 — 2026-10-16
### Added
- Skills framework (SKILL.md, loaded on demand with `use_skill`) and 18 built-in engineering skills; `improvise skills`.
- Coding workspace: `workspace_write/read/list`, `run_python` (confirmation required), version history and restore.
- Software Engineer team role (can run on its own model via `IMPROVISE_CODE_MODEL`).
- Calculators: conveyor sizing, pneumatic cylinder, heat load / steam, pump power, utilities summary.
- Connector catalogue `improvise connect` (14 checked MCP servers) and docs/CONNECTORS.md.
- Self-protection: `improvise backup` (+ automatic daily), `improvise selftest`, `improvise update` with rollback.
- Knowledge: industrial connectivity.
- README: measured capability and hardware guide.
### Changed
- Agent: tool routing for small models, automatic reference knowledge, duplicate-call guard,
  parameter validation, forced final answer; thinking off by default (`IMPROVISE_THINK=1` to enable).
### Fixed
- Windows: workspace paths, benchmark temp files, restore with an open database.

## v0.5 — 2026-10-16
### Changed
- Renamed factory-ai to **Improvise** (package `improvise`, command `improvise`, repo `idarinza-afk/improvise`).
  `factory-ai` command kept as an alias; `~/.factory-ai` is moved to `~/.improvise`; `FACTORY_AI_*`
  environment variables still work. Pro is now Improvise Pro (`improvise-pro`).

## v0.4 — 2026-10-16
### Changed
- Project team mode is now led by the Project Manager: the owner talks only to the PM, the PM proposes a
  team, and the owner defines every position (title, responsibility, tools), adds or removes positions
  and chooses the reviewer. Teams, board and PM conversation are saved per project
  (`~/.improvise/teams/`). Commands inside the chat: /team, /role, /add, /remove, /reviewer, /board, /report.
- `improvise team "brief"` still runs a one-shot job with the PM's proposed team.

## v0.3 — 2026-10-16
### Added
- Project team mode (`improvise team`): Project Manager plans, discipline specialists work with
  their own tool sets on a shared project board, Senior Consultant reviews, PM summarises.
  Roles in `team_roles.json`, user roles in `~/.improvise/team_roles.json`; PLC and IT/IoT roles with Pro.
- Agent can run with a role prompt and a restricted tool set.
### Fixed
- Benchmark temporary memory is closed before cleanup (Windows).

## v0.2 — 2026-10-16
### Added
- MCP server (`improvise mcp serve`): all tools plus teaching tools (`add_rule`, `verify_case`,
  `add_verified_case`, `memory_stats`) for AI assistants such as Claude Desktop.
- MCP client: use external MCP servers listed in `~/.improvise/mcp.json`; actions need confirmation.
- Benchmark suite and `improvise bench` with `--compare` to gate model releases.
- README demo GIF and layout image.
### Changed
- Layout: return rows of U / serpentine lines are right-aligned; flow lines drawn in the SVG.

## v0.1 — 2026-10-15
- First public preview: local agent on Ollama, experience memory, knowledge search, line
  calculations, OEE, ROI, machine / part lists, manuals, 2D layout + JSON for 3D, community
  contribution packs, plugin loading for the Pro edition.
