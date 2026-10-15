# Connectors

Improvise talks to other software through the Model Context Protocol (MCP).
`improvise connect add <name>` writes the entry to your local `~/.improvise/mcp.json`;
`improvise mcp tools` shows what is connected. Any connected tool that is not declared
read-only asks for your confirmation every time it runs.

All servers below are existing open-source projects (checked October 2026). They are
maintained by their own authors — read their README before connecting them to real equipment.

| Name | Category | Project | Licence | Notes |
|---|---|---|---|---|
| `freecad` | CAD / 3D | [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) | MIT | Needs its FreeCAD add-on |
| `blender` | CAD / 3D | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) | MIT | Package name `mcp-for-blender`; needs its Blender add-on |
| `build123d` | CAD / 3D | [build123d-mcp](https://pypi.org/project/build123d-mcp/) | Apache-2.0 | Parametric CAD |
| `excel` | Office / data | [haris-musa/excel-mcp-server](https://github.com/haris-musa/excel-mcp-server) | MIT | Works on .xlsx without Excel; limited to one folder |
| `files` | Office / data | [modelcontextprotocol/servers – filesystem](https://github.com/modelcontextprotocol/servers) | MIT | Limited to the folders you give |
| `git` | Office / data | [modelcontextprotocol/servers – git](https://github.com/modelcontextprotocol/servers) | MIT | |
| `fetch` | Office / data | [modelcontextprotocol/servers – fetch](https://github.com/modelcontextprotocol/servers) | MIT | Read-only |
| `sqlite` | Office / data | [servers-archived – sqlite](https://github.com/modelcontextprotocol/servers-archived) | MIT | Archived reference server |
| `postgres` | Office / data | [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp) | MIT | Added in restricted (read-only) mode |
| `influxdb3` | Plant data | [influxdata/influxdb3_mcp_server](https://github.com/influxdata/influxdb3_mcp_server) | MIT / Apache-2.0 | Machine time-series |
| `grafana` | Plant data | [grafana/mcp-grafana](https://github.com/grafana/mcp-grafana) | Apache-2.0 | |
| `nodered` | Plant data | [gmag11/NodeRed-MCP](https://github.com/gmag11/NodeRed-MCP) | Apache-2.0 | Author advises against production instances |
| `opcua` | Industrial | [kukapay/opcua-mcp](https://github.com/kukapay/opcua-mcp) | MIT | Run from a clone: `--param clone=<path>` |
| `twincat` | Industrial | [malcolm-mill/beckhoff_mcp](https://github.com/malcolm-mill/beckhoff_mcp) | MIT | Read-only ADS access |

Also available but not in the one-command catalogue yet:
- MQTT and Modbus servers by ezhuk (MIT) run over HTTP rather than stdio.
- Siemens TIA Portal via [vscode-tiaportal-mcp](https://github.com/heilingbrunner/vscode-tiaportal-mcp) (MIT, Windows, TIA V20 Openness).
- CODESYS via [codesys-mcp-toolkit](https://github.com/johannesPettersson80/codesys-mcp-toolkit) (MIT).
- KiCad via [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) (MIT).

Any other MCP server can be added by hand to `~/.improvise/mcp.json`:

```json
{ "servers": { "my-server": { "command": "python", "args": ["-m", "my_server"], "read_only": false } } }
```

Python libraries used or recommended for future built-in connectors: SimPy (MIT, line
simulation), pymodbus (BSD-3), asyncua (LGPL-3.0), python-snap7 (MIT), pycomm3 (MIT),
pyads (MIT), ezdxf (MIT, DXF drawings), paho-mqtt (EPL-2.0 / BSD-3).
