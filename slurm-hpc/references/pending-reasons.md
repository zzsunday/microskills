# Pending reasons

Use this file after reading `squeue -l -j <jobid>` or `scontrol show job <jobid>`.

Reason strings vary by Slurm version and site policy. Treat the items below as common patterns, not guaranteed explanations. Always tie the conclusion back to the command output you actually saw.

## Safe interpretation workflow

1. Record the exact reason string from `squeue` or `scontrol show job`.
2. Check whether the blocker looks like resources, partition policy, QoS, association limits, dependency state, or invalid job input.
3. Verify that hypothesis with the matching discovery command.
4. Report verified blockers separately from unresolved uncertainty.

## Common patterns

| Reason pattern | Usually means | Verify with |
| --- | --- | --- |
| `Priority` | Other jobs currently outrank this job. | `sshare -l`, `squeue --start -j <jobid>` |
| `Resources` | Eligible job is waiting for enough free resources. | `sinfo --summarize`, `sinfo --Node --long`, `squeue --start -j <jobid>` |
| `ReqNodeNotAvail` | Requested node, feature, or reservation target is unavailable. | `scontrol show job <jobid>`, `scontrol show node <node_name>`, `sinfo --Node --long` |
| `PartitionTimeLimit` | Requested wall time exceeds the partition limit. | `scontrol show partition` |
| `QOSMaxWallDurationPerJobLimit` | Requested wall time exceeds a QoS limit. | `sacctmgr show qos ...` |
| `AssocMaxSubmitJobLimit` | User or account hit an association submission cap. | `sacctmgr show assoc where user=$USER ...`, `squeue -u $USER` |
| `AssocMaxJobsLimit` | User or account hit a running job cap. | `sacctmgr show assoc where user=$USER ...`, `squeue -u $USER` |
| `QOSGrpSubmitJobsLimit` | A QoS submission limit is saturated. | `sacctmgr show qos ...`, `squeue -u $USER` |
| `QOSGrpJobsLimit` | A QoS running-job limit is saturated. | `sacctmgr show qos ...`, `squeue -u $USER` |
| `QOSGrpTRES` or `QOSMaxTRESPerJob` | Requested CPUs, memory, nodes, or GPUs exceed QoS limits. | `sacctmgr show qos ...`, `sacctmgr show tres`, `scontrol show partition` |
| `Dependency` | Upstream dependency has not completed successfully yet. | `scontrol show job <jobid>` |
| `InvalidAccount` | The selected account is not valid for this job. | `sacctmgr show assoc where user=$USER ...`, local site docs |
| `InvalidQOS` | The selected QoS is not permitted. | `sacctmgr show assoc where user=$USER ...`, `sacctmgr show qos ...` |
| `BeginTime` | The job is not eligible until a later time. | `scontrol show job <jobid>` |
| `JobHeldUser` or `JobHeldAdmin` | The job is held. | `scontrol show job <jobid>` |

## Response pattern

When explaining a pending job, prefer language like:

- Verified: "The job is pending with reason `PartitionTimeLimit`, and `scontrol show partition` shows the selected partition has a shorter `MaxTime` than the job requested."
- Verified: "The job is pending with reason `AssocMaxSubmitJobLimit`, and the association output shows a submit cap that appears saturated by the current queue."
- Unknown: "The job is pending for `Priority`, but I cannot confirm fairshare or QoS weighting because accounting visibility is restricted on this cluster."

Do not collapse `Priority`, `Resources`, QoS caps, and association caps into one generic explanation.
