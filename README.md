# factory-ai

**A local AI assistant for production engineering.**
Design production lines · calculate capacity, line balance, OEE and ROI · lay out lines in 2D and hand off to 3D
· produce machine lists, part lists, manuals and related documents —
and it **keeps getting better from your own verified experience**, without your data ever leaving your machine.

Free to use. PLC control logic, IoT and dashboards are coming in **factory-ai Pro** (see below).

> Status: v0.1 (preview) — see [docs/ROADMAP.md](docs/ROADMAP.md)

---

## What it does (free edition)

| Module | Capabilities | Code |
|---|---|---|
| Line calculations | takt time, machine count (OEE-adjusted), bottleneck, line balancing (RPW), buffer sizing | `factory_ai/calc/line.py` |
| OEE / ROI | OEE split into A × P × Q with the main loss; payback, NPV, IRR | `calc/oee.py`, `calc/roi.py` |
| Documents | machine list, part list (Excel), O&M manual (Markdown/Word) — unknown prices are left blank | `documents.py` |
| Layout | place machines in flow order (straight, U or serpentine), check room fit, export SVG + JSON for 3D | `layout.py` |
| Knowledge | searchable engineering knowledge base, plus your own notes in `~/.factory-ai/knowledge` | `knowledge.py` |
| Learning | experience memory, engineer-confirmed rules, dataset export for fine-tuning | `memory.py` |
| Community | anonymised contribution packs to help train the shared model | `contribute.py` |

Core principle: **the AI never guesses numbers.** Every figure comes from a tested calculation function;
the language model's job is to understand the request, pick the right tools and explain the result.

## Installation (Windows / macOS / Linux)

1. Install Python 3.10+ and [Ollama](https://ollama.com).
2. Pull a model that supports tool calling, sized to your GPU — roughly 7–8B for 6–8 GB of VRAM,
   14B or larger for 12 GB and up. For example:
   ```bash
   ollama pull qwen2.5:14b
   ```
   Set the model name with the `FACTORY_AI_MODEL` environment variable.
3. Install factory-ai:
   ```bash
   git clone https://github.com/idarinza-afk/factory-ai
   cd factory-ai
   pip install -e ".[docs]"
   factory-ai doctor
   ```

## Usage

```bash
factory-ai chat                      # interactive assistant (type /save to store an answer as a case)
factory-ai ask "Bottling line, 20,000 bottles/day on 2 shifts: how many 3,000 bph fillers do I need?"
factory-ai tools                     # list all tools
factory-ai run takt_time '{"demand_units":20000,"shifts":2,"hours_per_shift":8,"break_min_per_shift":60}'
factory-ai run layout_line examples/bottling_line.json
factory-ai pro                       # see what the Pro edition adds
```

The calculation tools work without a language model — `factory-ai run` calls them directly.

### Making it smarter

```bash
factory-ai memory add --kind line_design --title "Egg packing line" --problem "..." --solution "..."
factory-ai memory verify 1 "On site the sealer was the bottleneck; needed 10% more speed"
factory-ai memory rule "egg line" "Always add a 10% buffer before the sealer"
factory-ai memory export dataset.jsonl     # for periodic LoRA fine-tuning
```

Details: [docs/LEARNING.md](docs/LEARNING.md) · Help train the shared model: [CONTRIBUTING.md](CONTRIBUTING.md)

## factory-ai Pro (coming soon)

Takes the line you designed in the free edition into control and automation.

| Capability | Details |
|---|---|
| **PLC control logic** | I/O list generated from the machine list, sequences converted to IEC 61131-3 Structured Text, standard function blocks (motor, valve, conveyor, alarm), automatic code checking, simulator testing, export to Siemens TIA / Mitsubishi GX Works / Omron Sysmac |
| **IoT** | MQTT / OPC UA tag maps from the I/O list, read-only edge collector code, gateway configuration |
| **Dashboards** | OEE and production dashboards built from your lines' data, downtime and reject analysis, shift reports and real-time dashboards |

**Pricing** (prices to be announced)

| Plan | Billing | For |
|---|---|---|
| Pro | monthly, per user | engineers, freelancers, small system integrators |
| Team | monthly, per seat + shared experience memory | system integrators, machine builders |
| Enterprise | annual + on-prem install, fine-tuning on company data, support | factories and large organisations |

Interested in trying Pro? Open a GitHub issue with the label `pro-interest`.

## Safety (read before use)

- Results are decision-support tools; the responsible engineer must check them before real-world use.
- Prices that are not supplied are always left blank — the AI never guesses prices.

See [docs/SAFETY.md](docs/SAFETY.md).

## Your data

Everything that belongs to you (experience memory, notes, output files) lives in `~/.factory-ai`
(change it with `FACTORY_AI_HOME`), outside the repository, and is never pushed to GitHub.

## License

See [LICENSE](LICENSE).
