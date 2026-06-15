# Research Notes

## Main research gap

RFID sensing papers often use AI or ML outside the tag, such as on the reader, gateway, phone, or server. Ultra-low-power SNN papers show event-driven operation can be efficient under sparse activity. The less-tested intersection is tiny SNN-style logic inside or near RFID sensor-tag control logic.

## Practical target ranking

1. Near-tag companion block: most realistic
2. Semi-passive or battery-assisted sensor tag: realistic enough for a feasibility study
3. Fully passive RFID tag IC: high risk and should not be claimed without strong numbers

## Strongest use cases

- wake-up decision
- noisy event filtering
- simple anomaly flag
- sparse multi-sensor temporal fusion

## Weak use cases

- simple threshold detection
- fixed protocol recognition where a small FSM is enough
- reader-side RF signature classification
- general AI or full neural acceleration inside passive RFID

## What would make the SNN interesting

The SNN becomes interesting only if it shows at least one of the following:

- fewer false positives than simple logic under noisy sparse events
- comparable accuracy with lower switching activity
- better temporal fusion than a compact FSM or LUT
- acceptable area overhead under synthesis

## What would kill the idea

The idea is probably not worth pursuing if:

- threshold logic solves the task with similar accuracy
- FSM area is much smaller and more predictable
- SNN weight and membrane storage dominate the area
- SNN only wins by using an unfairly weak baseline
- power claims are based only on vague neural-efficiency arguments
