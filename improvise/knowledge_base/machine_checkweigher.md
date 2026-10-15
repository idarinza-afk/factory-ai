# Checkweigher

## What it does / working principle
A checkweigher weighs every pack in motion and rejects packs that fall outside set limits. It has three sections:
- **Infeed belt:** sets the speed and the gap between packs.
- **Weigh belt:** sits on a load cell, either strain-gauge or electromagnetic force restoration.
- **Outfeed with a reject device.**

A photo-eye triggers the weighing. The controller samples the signal while the pack is fully on the weigh belt and averages it. It then classifies the pack (for example, under reject, under OK, accept, over OK, over reject) and fires the rejecter after a timed delay.

## Main types and when to choose each
- **Standard in-line belt checkweigher:** most packaged foods.
- **Combination unit:** checkweigher plus metal detector or X-ray on one frame. Saves floor space and uses one reject system.
- **Heavy-duty / case checkweigher:** end of line, for missing-item checks on cases.
- **Reject types:** air blast (light packs), pusher, diverter arm, drop flap or drop belt (fragile), retracting belt. Choose by pack weight, stability and rate.

## Key specifications to ask for
- Weight range, accuracy (stated as a standard deviation at your speed and pack), and division size
- Rate in packs/min. One manufacturer groups machines into about 50–250, 250–500 and 500–700+ ppm classes (typical).
- Pack length range and weigh-belt length, and conveyor speed
- Reject type, a lockable reject bin, reject confirmation
- Data output and feedback to the filler, statistics, and the approval status for legal metrology

## Sizing / selection notes
- Only one pack may be on the weigh belt at a time, and the gap must also leave time for auto-zero. Speed up the infeed if needed.
- Accuracy gets worse with higher speed, vibration, air drafts and unstable packs. Mount the machine on a firm floor and keep it away from fans.
- Legal metrology: whether you work to a minimum-weight system or an average-quantity system (for example the EU "e" system, or NIST Handbook 133 in the US), and which tolerances apply, comes from local legal metrology rules. Set limits with your QA team and the local authority; do not guess them.

## Integration with the line
The checkweigher sits after the filler or wrapper and before case packing. Its feedback signal to the filler cuts give-away. Provide "consecutive rejects" alarms that stop the upstream line.

## Hygiene and safety notes
Use washdown construction where needed, open belts that remove without tools, and guarded rejecters (pushers are pinch hazards).

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| Unstable or noisy weights | Vibration, airflow, dirty or worn belts | Floor mounting, draughts, belt condition, re-zero |
| Good packs rejected | Reject timing wrong, packs too close | Reject delay, infeed gap, photo-eye position |
| Rejects missed | Air pressure low, rejecter jammed | Air supply, reject confirmation sensor |
| Drift over the shift | Temperature change, product build-up | Auto-zero interval, cleaning, calibration check |

## Sources
- https://en.wikipedia.org/wiki/Check_weigher
- https://documents.thermofisher.com/TFS-Assets/CAD/Handbooks/checkweighing-checkweighers-ebook.pdf
- https://www.thermofisher.cn/blog/food/what-is-a-checkweigher-and-why-use-one-heres-a-free-guide-for-food-processors
