# Metal Detector

## What it does / working principle
Most food metal detectors use a balanced three-coil head. A transmitter coil sits between two receiver coils. When a conductive or magnetic particle passes through, it disturbs the balance and the electronics flag it. Wet, salty or warm products are themselves conductive and create a "product effect" signal. Modern units use multi-frequency or product-signal suppression to separate this from real metal.

## Main types and when to choose each
- **Conveyor aperture detector:** packed or unpacked product on a belt.
- **Gravity / throat detector:** free-falling product, for example above a VFFS.
- **Pipeline detector:** pumped liquids, pastes and slurries.
- **Ferrous-in-foil detector:** foil or metallised packs, where a standard balanced coil cannot work. It is sensitive to ferrous metal only.

## Key specifications to ask for
- Aperture size, and the detectable test-sphere sizes for ferrous, non-ferrous and stainless steel with *your* product at the aperture centre
- Operating frequency or multi-frequency capability
- Reject device and fail-safe package
- Conveyor speed, belt type and data logging

## Sizing / selection notes
- Sensitivity is stated as the diameter of the smallest test sphere reliably detected at the aperture centre, which is the least sensitive point. Ferrous is generally the easiest to detect and stainless steel the hardest.
- Use the smallest practical aperture.
- Dry products usually suit higher frequencies, while wet products need product-effect compensation.
- Wire-shaped contaminants are detected differently depending on their orientation.
- The required sensitivity and test frequency come from your HACCP study, customer or retailer codes of practice, and certification schemes. Use those documents for actual pass/fail sizes; this note does not set them.

## Integration with the line
Typical fail-safe features required by retailer codes include:
- belt stop if a reject is not confirmed
- bin-full sensor
- low-air-pressure switch
- enclosed path to a lockable reject bin
- faults that survive a power cycle and need an authorised reset

Test packs are run with the metal at the leading edge, centre and trailing edge.

## Hygiene and safety notes
Keep metal structures away from the metal-free zone around the head. Avoid loose metal guards that vibrate. Secure test pieces under control so they never end up in product.

## Common problems and first checks
| Symptom | Likely causes | First checks |
|---|---|---|
| False rejects | Product effect changed (temperature, salt), vibration, electrical noise, metal in the metal-free zone | Re-learn the product, check earthing and loose fixings, check VFD cable routing |
| Test piece not detected | Sensitivity set too low, wrong product learned, aperture too large | Product setting, run test at centre, review aperture |
| Reject failing | Timing, air pressure | Reject delay, encoder or speed, air switch |
| Drifting sensitivity | Head temperature, build-up | Auto-tracking settings, cleaning, service check |

## Sources
- https://www.mt.com/us/en/home/library/know-how/product-inspection/metal-detector-sensitivity.html
- https://documents.thermofisher.com/TFS-Assets/CAD/Application-Notes/retailer-compliance-backgrounder.pdf
