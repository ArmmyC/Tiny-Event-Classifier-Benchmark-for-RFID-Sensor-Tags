# Feature Spec: Research Writeup Generator

## Goal

Add a generated paper-style Markdown writeup that turns the evidence pipeline outputs into a concise research report.

The repo now has benchmark results, RTL comparison results, a research decision report, an evidence manifest, and an artifact card. The next step is to make those results easier to present as a research artifact.

This task should not add new classifiers or RTL. It only summarizes existing outputs.

## Command

Add:

```text
python/tinysnnrfid/build_research_writeup.py
python/build_research_writeup.py
make research-writeup
```

Default command:

```bash
python python/build_research_writeup.py --input-root results --output-dir results
```

Support smoke mode:

```bash
python python/build_research_writeup.py --input-root results/smoke --output-dir results/smoke
```

## Inputs

Read these files when present:

```text
artifact_card.json
research_decision_summary.json
research_decision_report.md
rtl/rtl_comparison_summary.json
rtl/rtl_comparison_report.md
evidence_manifest.json
```

Missing inputs should be allowed. The writeup should clearly mark missing evidence.

## Outputs

Write:

```text
research_writeup.md
research_writeup_summary.json
```

under the selected output directory.

Generated outputs must not be committed.

## Markdown sections

The writeup should include:

```text
# Tiny SNN RFID Research Writeup
## Abstract
## Research Question
## Methodology
## Dataset and Scenario Suites
## Classifiers Compared
## Software Evidence Summary
## RTL Evidence Summary
## Decision Summary
## Limitations
## Reproducibility
## Next Steps
```

## Required content

The writeup should explain:

- the project compares tiny SNN logic against threshold, FSM, and LUT-like baselines,
- the benchmark includes legacy and temporal-hard scenarios,
- `tiny_snn_v2` is fixed-weight and not trained,
- software activity is only a software operation proxy,
- RTL cell counts and VCD toggles are local-tool proxies,
- no silicon power, silicon area, or signoff claim is made,
- the final recommendation is taken from the generated evidence when available.

Use stable language for the main recommendation:

```text
continue_snn_optimization
add_harder_temporal_scenarios
prioritize_fsm_or_lut_rtl_baseline
insufficient_data
```

Also include RTL recommendation when available:

```text
continue_snn_rtl_optimization
optimize_snn_rtl_before_more_features
prioritize_fsm_or_lut_rtl_baseline
insufficient_rtl_data
```

## Summary JSON

Suggested fields:

```json
{
  "generated_at": "...",
  "input_root": "results",
  "research_recommendation": "...",
  "rtl_recommendation": "...",
  "missing_inputs": [],
  "key_limitations": [],
  "next_steps": []
}
```

## Makefile

Add `research-writeup` to `.PHONY`.

Update `evidence` so it runs:

```text
research-writeup
```

after `artifact-card`.

Update `clean` to remove:

```text
results/research_writeup.md
results/research_writeup_summary.json
```

`results/smoke/` is already cleaned as a directory.

## README

Document:

```text
make research-writeup
```

Explain that the writeup is a generated paper-style summary and should be regenerated after `make evidence`.

## Tests

Add tests that do not run the full evidence pipeline:

1. Missing inputs still generate writeup outputs.
2. Synthetic artifact card and research summary are loaded correctly.
3. Synthetic RTL comparison summary is included correctly.
4. Markdown contains all required sections.
5. Markdown contains proxy-metric limitation text.
6. Summary JSON includes recommendations and missing inputs.
7. Makefile contains `research-writeup` and `evidence` runs it after `artifact-card`.
8. Clean target removes writeup outputs.

## Constraints

- Do not add new classifiers.
- Do not add new RTL.
- Do not add heavy dependencies.
- Do not run the full evidence pipeline inside tests.
- Do not commit generated outputs.

## Definition of done

- `make research-writeup` works.
- Markdown and JSON writeup outputs are generated.
- Full and smoke input roots are supported.
- README and tests are updated.
- Existing workflows keep working.
