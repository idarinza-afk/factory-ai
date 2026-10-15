---
name: compressed-air-system
description: Size the compressed-air system: consumption, compressor, receiver, dryer, distribution.
tools: pneumatic_cylinder, utilities_summary, air_receiver, pipe_size
---
## Method
1. Consumption per machine (pneumatic_cylinder for cylinders; blow-offs and vacuum generators from datasheets).
2. Total with utilities_summary (margin 25-30 % for leaks and growth).
3. Compressor: total NL/min at the required pressure + 0.5-1 bar for losses; consider 2 units for redundancy.
4. Receiver for peaks: air_receiver with the peak deficit and duration.
5. Air quality: food contact air needs oil-free compressor or proper filtration and dryer (ISO 8573-1 classes per customer requirement).
6. Ring main sized for low pressure drop (< 0.1 bar).
