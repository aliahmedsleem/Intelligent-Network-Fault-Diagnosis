# Explainable topology-aware fault localization

`POST /api/localization/analyze` accepts a validated network graph and at least two end-to-end probe comparisons. Each probe has source, destination, baseline loss, and observed loss. The engine computes the *baseline shortest-delay path* and marks probes as degraded when loss increases by the configured threshold (default: 5 percentage points).

Each candidate link receives the fraction of degraded paths traversing it, minus the fraction of nondegraded paths traversing it. Highest positive unique score is the suspected link. Equal best scores yield **ambiguous**, not a fabricated precise answer. No positive score yields **insufficient_evidence**.

This is an explainable heuristic, **not machine learning**, and the scores are **not probabilities**. The model does not use fault-injection ground truth as an input. It currently assumes stable routing, undirected links, a single dominant fault and valid probe data. For meaningful localization, collect multiple independent paths; a single end-to-end measurement generally cannot identify one link.

## Scientific validation
Construct labeled fault scenarios, keep injected link IDs in a separate evaluation dataset, measure Top-1 localization accuracy, ambiguity rate, no-fault false-positive rate, and runtime. Include diverse topologies and healthy-path controls. Do not report model accuracy before running these evaluations.
