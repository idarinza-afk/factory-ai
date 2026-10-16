# Conveyor drives on wet and dry lines: friction, starting torque and shaft load

A conveyor that runs normally on a dry line can stall on a wet line. The motor power (kW) barely changes, but the
belt pull, the breakaway (starting) torque and the load on the drive shaft rise sharply. Size the drive on torque
and shaft load, not on kW alone.

## Friction belt -> bed (running)
- Flat PU/PVC belt on a steel slider bed, dry: about 0.3-0.4 (ISO 5048 value for belt on steel; designers often use
  0.5 for motor sizing and maximum belt tension).
- Flat belt on a flat stainless slider bed, wet: the belt sucks onto the bed (water film) and drag rises a lot;
  sauce, sugar, starch or fat make it sticky. Improvise uses allowances of 0.5 (wet) and 0.6 (sticky) - confirm by
  measuring the motor current on site.
- Modular plastic / table-top chain on UHMWPE wear strips (Rexnord TableTop/MatTop manual): acetal 0.25 dry,
  0.21 with water, 0.15 soap and water; polypropylene 0.30 dry, 0.25 water. Clean water lowers friction here;
  product residue raises it.
- Roller bed: about 0.05.
- After a standstill the static (breakaway) friction is higher than the running friction, more so when wet
  or sticky: check the starting torque, not only the running torque.

## Drive pulley slip (flat belts)
Belt on the drive drum transmits at most T1/T2 = e^(mu x wrap angle). A wet bare steel pulley has a low mu, so it
slips: use a lagged pulley and enough take-up (slack-side) tension.

## Shaft load
- Belt tensions T1 + T2 act on the drive pulley shaft. If the pulley sits on the gearmotor output shaft, this is
  the radial (overhung) load on the gear unit.
- For a chain or belt drive between gearmotor and pulley: F_R = 2000 x M / d0 x fZ (M in Nm, d0 pitch diameter in
  mm). fZ: gears 1.15, sprockets 1.25 (<20 teeth) to 1.40 (<13 teeth), narrow V-belt 1.75, toothed belt 2.0-2.5,
  flat belt 2.5 (SEW-EURODRIVE).
- Compare with the permissible radial load of that exact gear unit from its datasheet (corrected for the load
  position on the shaft). Brands differ in output shaft diameter and radial load rating; exceeding it bends or
  breaks the output shaft and destroys bearings.
- Remedies: hollow-shaft gearmotor on the pulley shaft (pulley shaft in its own bearings, torque arm), flexible
  coupling, bigger gear unit; on wet lines first lower the bed friction (perforated/grooved slider bed, UHMW strips,
  roller bed, belt with a structured underside).

Tools: conveyor_sizing (belt_type, condition, drive_pulley_mm, transmission) then gearmotor_check (datasheet values).

Sources:
- Rexnord TableTop and MatTop Chain Engineering Manual, friction tables Fw/Fm:
  https://documents.mrosupply.com/product_documents/61/614-106-1/8rx2004EM-en(TT).pdf
- Belt on steel friction, ISO 5048 discussion: https://www.bulk-online.com/en/node/59273
- SEW-EURODRIVE, Determining the overhung load: https://download.sew-eurodrive.com/download/html/31967477/en-EN/48651451915.html
- Field experience (Improvise users): a conveyor that ran on a dry line stalled on a wet line because belt drag rose.
