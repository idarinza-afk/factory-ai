# Changelog

## v0.3 — 2026-10-16
### Added
- Project team mode (`factory-ai team`): Project Manager plans, discipline specialists work with
  their own tool sets on a shared project board, Senior Consultant reviews, PM summarises.
  Roles in `team_roles.json`, user roles in `~/.factory-ai/team_roles.json`; PLC and IT/IoT roles with Pro.
- Agent can run with a role prompt and a restricted tool set.
### Fixed
- Benchmark temporary memory is closed before cleanup (Windows).

## v0.2 — 2026-10-16
### Added
- MCP server (`factory-ai mcp serve`): all tools plus teaching tools (`add_rule`, `verify_case`,
  `add_verified_case`, `memory_stats`) for AI assistants such as Claude Desktop.
- MCP client: use external MCP servers listed in `~/.factory-ai/mcp.json`; actions need confirmation.
- Benchmark suite and `factory-ai bench` with `--compare` to gate model releases.
- README demo GIF and layout image.
### Changed
- Layout: return rows of U / serpentine lines are right-aligned; flow lines drawn in the SVG.

## v0.1 — 2026-10-15
- First public preview: local agent on Ollama, experience memory, knowledge search, line
  calculations, OEE, ROI, machine / part lists, manuals, 2D layout + JSON for 3D, community
  contribution packs, plugin loading for the Pro edition.
