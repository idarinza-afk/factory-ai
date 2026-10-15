# Changelog

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
