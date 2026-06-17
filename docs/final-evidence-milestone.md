# Final Evidence Milestone

## Fresh evidence status

The latest full evidence run completed from a clean generated-output state. The test suite passed with 188 tests, `make clean` ran through the Python cleaner, `rtl-doctor` found `iverilog`, `vvp`, and `yosys`, and `make evidence` completed successfully.

The generated evidence manifest is complete with 0 missing outputs. RTL simulation, synthesis, activity, comparison, research report, artifact card, and research writeup artifacts were regenerated in the same run.

## Sparse SNN result

The current sparse RTL candidate is `tiny_snn_v2_sparse_activity`.

Generated RTL evidence reports:

- Simulation status: pass.
- Synthesis status: available.
- Cell-count proxy: 610 cells.
- Cell ratio vs FSM: 3.961x.
- Toggle-count proxy: 73189 toggles.
- Toggle ratio vs FSM: 1.117x.

These are local-tool proxy results from open-source RTL simulation, synthesis, and VCD activity analysis. They are not silicon area, measured power, measured energy, or signoff results.

## Recommendation interpretation

The RTL comparison recommendation remains `optimize_snn_rtl_before_more_features` because the sparse SNN is still materially larger than the FSM reference on the cell-count proxy. Its 3.961x cell ratio is close to the configured 4.0x optimization boundary, while its toggle proxy is only 1.117x vs FSM.

This means the sparse RTL is no longer in the same regime as the original dense `tiny_snn_v2` RTL, but it is also not yet small enough to justify adding new RTL-facing features ahead of consolidation.

## Why this is a meaningful milestone

This is a useful research milestone because the evidence is fresh, complete, and guarded against stale artifacts. The sparse SNN now has passing simulation, available synthesis, and current activity evidence from a clean run.

The sparse implementation reduced the SNN RTL cost proxy enough to become a plausible candidate for continued study, while preserving a clear comparison against FSM, threshold, LUT-like, and legacy SNN baselines.

The broader research report still recommends `continue_snn_optimization`, supported by software-side SNN search evidence. The RTL comparison narrows the immediate hardware direction: preserve this sparse RTL result as the current baseline before doing more feature work.

## Next steps

- Pause RTL micro-optimization for now.
- Preserve `tiny_snn_v2_sparse_activity` at 610 cells and 1.117x toggle ratio vs FSM as the current sparse SNN RTL baseline.
- Use this result in the research writeup as the first complete fresh RTL evidence milestone for the sparse SNN path.
- Continue RTL optimization only if there is a clear architecture-level simplification, not merely another small local rewrite.
- Keep reporting cell counts and toggles as local-tool proxies, not silicon area or measured power.
