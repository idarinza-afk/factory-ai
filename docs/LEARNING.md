# How Improvise gets better

Improvise **stores what it learns, but only on your machine**, and it does not change its own
"brain" (model weights) automatically every time you use it. Learning from answers nobody has
checked would make it accumulate mistakes.

## Layer 1 — Experience memory (better immediately)
Every finished job (line design, machine list, ROI...) is stored as a *case* in SQLite
(`~/.improvise/experience.db`). Before every answer the agent retrieves similar cases into its
context; **verified** cases (proven on site) are ranked first.

```
improvise memory add ...        # add a case (or type /save during chat)
improvise memory verify <id> "site result / lesson learned"
```

## Layer 2 — Engineer-confirmed rules (better where it matters)
Your corrections are stored as *rules* and take precedence over general knowledge.

```
improvise memory rule "egg line" "Always add a 10% buffer before the sealer"
```

## Layer 3 — Periodic fine-tuning (permanently better, inside the model)
Export verified cases and rules as chat-format JSONL, train a LoRA with standard tools
(e.g. Unsloth, Axolotl, LLaMA-Factory), convert to GGUF and create a new Ollama model.

```
improvise memory export dataset.jsonl
# train LoRA -> merge -> GGUF -> ollama create improvise-personal -f Modelfile
# set IMPROVISE_MODEL=improvise-personal
```

Recommended every 3 months, or once you have ~200 new verified cases. Test against the
benchmark questions before switching to the new model.

## Layered models

```
Personal layer   (experience memory + personal LoRA)        <- tuned to the way you work
Community LoRA   (trained together by the community, versioned) <- see CONTRIBUTING.md
Base model       (open-weight model)
```
