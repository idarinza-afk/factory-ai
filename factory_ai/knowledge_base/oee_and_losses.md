# OEE and the six big losses

OEE = Availability x Performance x Quality.

- Availability = run time / planned production time. Losses: breakdowns,
  setups and changeovers (if not planned).
- Performance = (ideal cycle time x total count) / run time. Losses: minor stops
  and idling, reduced speed.
- Quality = good count / total count. Losses: startup rejects, production rejects.

Practical notes:
- Agree the ideal cycle time from the machine's design speed, not from the best
  day observed; a performance above 100% means the ideal cycle time is wrong.
- Define planned stops (breaks, planned cleaning, no-order time) before measuring,
  otherwise OEE numbers from different plants cannot be compared.
- Signals needed for automatic OEE: machine running, machine faulted (with fault
  code), product count (good) and reject count. Collect them from the PLC rather
  than manual sheets.
- Improve the biggest factor first. For packaging lines, minor stops (jams,
  sensor misreads) are usually the largest hidden loss.
