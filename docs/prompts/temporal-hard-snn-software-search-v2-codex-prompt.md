# Codex Prompt: Temporal-Hard SNN Software Search v2

Implement:

```text
docs/specs/temporal-hard-snn-software-search-v2.md
```

Goal: continue SNN work at the software-search level only by searching fixed-weight variants near `current_default` for temporal-hard cases.

Required:

1. Add `configs/snn_search_temporal_hard_v2.json`.
2. Add `make temporal-snn-v2-search`.
3. Use existing `run_snn_search.py` flow.
4. Output to `results/temporal_snn_v2_search/`.
5. Compare the v2 gate against `results/temporal_snn_optimized/search_results.json`.
6. Add several new current-default-derived fixed-weight variants, such as:
   - `current_default_gap_tuned`
   - `current_default_output_rebalanced`
   - `current_default_noise_inhibited`
   - `current_default_sparse_activity`
7. Do not change `tiny_snn_v2` default behavior.
8. Do not remove existing variants.
9. At least two new variants should preserve current_default hidden neuron count.
10. At least one new variant should have lower output-weight absolute sum than current_default.
11. Reuse `build_temporal_snn_optimization_gate.py` and write:
   - `results/temporal_snn_v2_search/optimization_gate.json`
   - `results/temporal_snn_v2_search/optimization_gate.md`
12. Do not add this command to `make evidence`.
13. Update README and clean target.
14. Add tests for config, variants, Makefile integration, cleanup, and gate behavior if changed.

Constraints:

- Do not add RTL.
- Do not add training.
- Do not add heavy dependencies.
- Do not make hardware power claims.
- Do not commit generated outputs.
- Keep existing evidence, smoke, optimized search, and writeup flows working.

Run:

```bash
python -m pytest
make temporal-snn-v2-search
```

Final response: summarize changed files, tests run, generated outputs, and the v2 gate recommendation if available.
