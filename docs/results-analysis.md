# Results Analysis

## Current Milestone

The current sparse SNN RTL baseline is `tiny_snn_v2_sparse_activity`.

The latest complete evidence milestone reports:

- Simulation status: pass.
- Synthesis status: available.
- Cell-count proxy: 610 cells.
- Cell ratio vs FSM: 3.961x.
- Toggle-count proxy: 73189 toggles.
- Toggle ratio vs FSM: 1.117x.
- RTL comparison recommendation: `optimize_snn_rtl_before_more_features`.
- Research report recommendation: `continue_snn_optimization`.
- Evidence manifest: complete with 0 missing outputs.

This is a meaningful improvement over earlier dense SNN RTL exploration, but it is not yet a win over the strongest conventional RTL baselines.

## Why FSM And LUT Baselines Remain Strong

The target task is a small noisy temporal motif detector. That is exactly the kind of problem where compact conventional logic can do well.

The FSM baseline remains strong because it directly represents the sequence structure. A short motif can be encoded as a few states with predictable control behavior and little storage.

The LUT-like baseline remains strong because the decision boundary is small and discrete. For compact event vectors and fixed temporal conditions, table-like or decision-tree-like logic can often encode the useful behavior without membrane state, weight storage, or neuron update machinery.

These baselines are not straw targets. They are the practical designs an engineer would naturally try first for RFID-style sensor-tag control logic.

## Why Sparse SNN Is Still Worth Studying

The sparse SNN is still worth studying because the current milestone moved the RTL evidence into a more plausible regime:

- Simulation passes for the current sparse SNN candidate.
- Synthesis evidence is available.
- The cell-count proxy is 610 cells.
- The toggle-count proxy is only 1.117x the FSM toggle count under the current vectors.

The SNN still carries a much higher cell-count proxy than the FSM, but its activity proxy is close enough to keep the research question alive. The result suggests that sparse event-driven structure can reduce unnecessary switching compared with less disciplined SNN RTL, even if the present architecture is still too large.

This supports continued architecture-level study, not immediate feature expansion.

## Why The RTL Recommendation Remains Optimization First

The RTL comparison recommendation remains `optimize_snn_rtl_before_more_features` because the sparse SNN cell ratio is still 3.961x the FSM baseline. That is close to the configured optimization boundary and still materially larger than the conventional control logic.

Adding more RTL-facing features before addressing this cost would risk improving the wrong thing. The current evidence says the sparse SNN is interesting, but not yet compact enough to treat as a settled hardware direction.

The better next move is to preserve the current sparse baseline and investigate architecture-level simplifications that could reduce fixed overhead:

- smaller or shared membrane state
- simpler spike accumulation
- fewer always-active update paths
- more direct encoding of the temporal motif
- hybrid FSM-plus-sparse-scoring structures

## Interpreting The Proxy Metrics

The cell-count proxy is a local synthesis count. It helps compare relative RTL complexity between the threshold, FSM, LUT-like, and SNN implementations under the same tool flow.

The toggle-count proxy is a VCD activity count. It helps compare relative switching activity under the exported benchmark vectors.

These proxy metrics are useful because they are generated, repeatable, and tied to the same benchmark inputs. They are also limited. They do not include physical layout effects, real standard-cell power characterization, clock tree cost, memory macro behavior, voltage and process variation, or measured hardware energy.

## Research Interpretation

The current result is a research milestone rather than a final hardware conclusion.

The conventional baselines remain the best immediate implementation choices for a small fixed motif detector. The sparse SNN remains a plausible research candidate because it now has fresh simulation, synthesis, and activity evidence with a much more controlled RTL profile than the original dense SNN direction.

The research recommendation remains `continue_snn_optimization`: continue studying the SNN path, but require the next step to answer an architecture-level cost question rather than adding features on top of the current structure.
