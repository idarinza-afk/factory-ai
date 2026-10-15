# Roadmap

## Free edition

### v0.1 (done)
- Agent loop with Ollama tool calling, experience memory, knowledge search
- Line calcs (takt, machines, bottleneck, RPW line balance, buffer), OEE, ROI
- Machine list / part list (Excel), O&M manual (Markdown/Word)
- 2D layout (SVG) + CAD-neutral JSON for 3D
- Anonymised community contribution packs

### v0.2 (done)
- MCP server and client (safe-by-default confirmations)
- Benchmark suite + `factory-ai bench`
- U-shaped layout flow

### v0.3 (done)
- Project team mode (PM, consultant, discipline specialists)

### v0.4 (done)
- PM-led team: owner talks only to the PM and defines every position; teams saved per project

### v0.5
- Desktop/web UI (chat + forms + file previews)
- Quotation / proposal package: 2D drawing, 3D views, machine spec, machine list in one bundle
- Utility calculator (power, compressed air, water, steam)
- A3 layout drawing with title block, DXF export; 3D placement script for Blender/FreeCAD

### v0.6
- Embedding-based search, PDF/datasheet ingestion with OCR
- Fine-tune pipeline script (LoRA -> GGUF -> Ollama)

### v0.7+
- Community dataset repo + CI leak scanner, quarterly Community LoRA
- Federated LoRA training

## Pro edition (commercial)
- PLC control logic: I/O list, sequence -> Structured Text, FB library, checker, simulator loop,
  vendor exporters (Siemens TIA, Mitsubishi GX Works, Omron Sysmac, PLCopen XML)
- IoT: MQTT / OPC UA tag maps, read-only edge collectors, gateway configuration
- Dashboards: OEE / production dashboards, downtime and reject analysis, live dashboards
- Team mode (shared memory), on-prem server
