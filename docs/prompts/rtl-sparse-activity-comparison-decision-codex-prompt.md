# Codex Prompt: RTL Sparse-Activity Comparison Decision

Implement:

```text
docs/specs/rtl-sparse-activity-comparison-decision.md
```

Goal: make the top-level RTL comparison recommendation judge `tiny_snn_v2_sparse_activity` against FSM, while keeping default `tiny_snn_v2` only as context.

Required:

1. Update `python/tinysnnrfid/compare_rtl_designs.py`.
2. Add summary fields:
   - `candidate_design: tiny_snn_v2_sparse_activity`
   - `legacy_snn_design: tiny_snn_v2`
   - keep `reference_design: fsm`
3. Make top-level `recommendation` and `reason` use `tiny_snn_v2_sparse_activity` vs FSM.
4. Do not require default `tiny_snn_v2` simulation to pass before judging sparse activity.
5. If sparse activity simulation is missing/failing, return `insufficient_rtl_data`.
6. Keep both contexts:
   - `tiny_snn_v2_context`
   - `tiny_snn_v2_sparse_activity_context`
7. Update Markdown so it clearly says the primary candidate is `tiny_snn_v2_sparse_activity` and default `tiny_snn_v2` is legacy context.
8. Update `build_research_report.py` if needed so the RTL comparison section shows the sparse candidate as the candidate design.
9. Add tests for sparse-candidate decision semantics.

Constraints:

- Do not add new RTL.
- Do not change detector weights.
- Do not change vector export.
- Do not add training.
- Do not add heavy dependencies.
- Do not claim measured silicon power or silicon area.
- Do not commit generated outputs.

Run:

```bash
python -m pytest
make rtl-report
make rtl-compare
make research-report
```

Final response: summarize changed files, tests run, and whether the sparse-activity candidate now drives the RTL decision.
