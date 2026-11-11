# Fault-management lifecycle (safe planning stage)

`POST /api/lifecycle/plan` accepts a measured multi-probe batch, infers candidate links, and creates an allowlisted lab-only remediation plan. The API **does not execute** the plan or run privileged commands.

States:
- `blocked`: no unique link; action withheld.
- `awaiting_approval`: unique candidate but operator approval required.
- `plan_ready`: approval requirement disabled in the request, but still **no action is executed**.
- Verification is `not_run` until a separate real Mininet remediation experiment is imported.

The only accepted action is `remove_injected_loss`. This is a conservative initial workflow, not a general self-healing network. Never interpret `plan_ready` as successful remediation.

## Evaluation roadmap
Repeat Mininet experiments across randomized fault positions and loss levels, save probe batches and remediation reports, separate fault ground truth from inference, compute Top-1 accuracy, ambiguity, false positives, remediation verification pass rate, and 95% uncertainty intervals. Avoid claims of validated accuracy until those runs complete.
