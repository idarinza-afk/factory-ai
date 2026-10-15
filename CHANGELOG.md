# Changelog

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
