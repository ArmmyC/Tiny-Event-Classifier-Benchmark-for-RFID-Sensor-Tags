# Codex Prompt: Temporal-Hard SNN Optimization Gate

Implement:

```text
docs/specs/temporal-hard-snn-optimization-gate.md
```

Goal: improve `tiny_snn_v2` only at the software/search level for temporal-hard cases, and add a gate that decides whether future SNN RTL work is justified.

Required:

1. Add `configs/snn_search_temporal_hard_optimized.json`.
2. Add `make temporal-snn-optimize`.
3. Use existing `run_snn_search.py` flow.
4. Output to `results/temporal_snn_optimized/`.
5. Add at least two new fixed-weight SNN search variants for temporal-hard ambiguity.
6. At least one new variant must be ternary-only `-1, 0, +1`.
7. At least one new variant must use small signed integer weights limited to `[-2, 2]`.
8. Do not change `tiny_snn_v2` default behavior.
9. Add an optimization gate report:
   - `results/temporal_snn_optimized/optimization_gate.json`
   - `results/temporal_snn_optimized/optimization_gate.md`
10. Gate recommendation enum:
   - `continue_to_snn_rtl_candidate`
   - `continue_software_snn_search`
   - `prioritize_fsm_or_lut_baseline`
   - `insufficient_data`
11. Do not add this command to `make evidence` yet.
12. Update README and clean target.
13. Add tests for config, new variants, gate logic, Makefile integration, and proxy limitation text.

Constraints:

- Do not add RTL.
- Do not add training.
- Do not add heavy dependencies.
- Do not make hardware power claims.
- Do not commit generated outputs.
- Keep existing evidence and smoke flows working.

Run:

```bash
python -m pytest
make temporal-snn-optimize
```

Final response: summarize changed files, tests run, generated outputs, and the gate recommendation if available.
