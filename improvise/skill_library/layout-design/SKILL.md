---
name: layout-design
description: Arrange machines into a line layout and check the room: flow, aisles, hygiene zones, maintenance access.
tools: layout_line, search_knowledge
---
## Rules
- One-directional flow; raw and finished product never cross; people/material flow from low to high care
  only through hygiene points.
- Aisles: 1.0-1.5 m operator/maintenance, 2.5-3.5 m forklift; keep 0.8-1 m behind machines for service.
- Straight line when the room is long; U-shape when start and end should be close or the room is short;
  serpentine (rows > 2) only for long lines in square rooms.
- Leave space for changeover parts trolleys, waste bins, utility drops, electrical panels (with door swing).
- Drawings: dimensions in metres, machine numbers matching the machine list, north/flow arrow.

## Method
1. Get machine footprints (L x W) in flow order and the room size.
2. layout_line with rows=1, then rows=2 if it does not fit; compare envelopes.
3. Check panels, aisles and doors; list what still needs to be verified on site (columns, drains, door heights).
4. Hand off the JSON for 3D.
