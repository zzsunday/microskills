# Command map

Use this file when the task is clear but the fastest matching Slurm command is not.

## Cluster discovery

| Question | Primary commands | Notes |
| --- | --- | --- |
| Which Slurm version is installed? | `scontrol version` | Prefer cluster output over public documentation. |
| What global controller config is visible? | `scontrol show config` | Check scheduling, accounting, and array-related settings here. |
| What partitions exist? | `sinfo --summarize` | Fast top-level view. |
| Which partition is default? | `sinfo --summarize`, `scontrol show partition` | Look for the `*` marker and partition defaults. |
| What nodes are available? | `sinfo --Node --long` | Good for a cluster-wide hardware overview. |
| What node-specific details matter? | `scontrol show node <node_name>` | Use before requesting features, constraints, or a GPU type. |
| What GRES are advertised? | `sinfo -o "%#P %.6D %G"`, `scontrol show node <node_name>` | GRES names are site-configured. |

## Policy and limit discovery

| Question | Primary commands | Notes |
| --- | --- | --- |
| What accounts can this user use? | `sacctmgr show assoc where user=$USER ...` | Visibility may be restricted. |
| What QoS values are allowed? | `sacctmgr show assoc where user=$USER ...`, `sacctmgr show qos ...` | Check both association and QoS layers. |
| What time limit applies? | `scontrol show partition`, `sacctmgr show assoc ...`, `sacctmgr show qos ...` | Limits can come from multiple layers. |
| What TRES exist? | `sacctmgr show tres` | Useful before reasoning about `gres/gpu` requests. |
| What fairshare context exists? | `sshare -l` | Helpful when `Priority` or share-based delays matter. |
| Can this user submit arrays of this size? | `scontrol show config` | Inspect `MaxArraySize`; do not assume. |

## Submission and validation

| Question | Primary commands | Notes |
| --- | --- | --- |
| Validate a batch script without submitting | `sbatch --test-only job.sh` | Use before a real submission when possible. |
| Submit a batch script | `sbatch job.sh` | Use only after discovery and validation. |
| Request an interactive allocation | `salloc ...` | Pair with `srun` inside the allocation. |
| Launch directly with Slurm | `srun ...` | `srun --test-only` is useful when supported. |
| Inspect current queue pressure | `squeue -u $USER`, `squeue --start -u $USER` | `--start` is an estimate, not a guarantee. |

## Monitoring and diagnosis

| Question | Primary commands | Notes |
| --- | --- | --- |
| Where is the job in the queue? | `squeue -j <jobid>` | Start here. |
| Why is the job pending? | `squeue -l -j <jobid>`, `scontrol show job <jobid>` | Match the reason to policy or resource state before concluding. |
| What is the running job doing now? | `sstat -j <jobid>` | Metric availability varies by site. |
| What happened after completion? | `sacct -j <jobid>` | Best source for finished jobs. |
| Should the job be canceled? | `scancel <jobid>` | Only after explicit user intent or required cleanup. |

## Practical command order

For a new cluster or unknown environment, prefer this order:

1. `scontrol version`
2. `scontrol show config`
3. `sinfo --summarize`
4. `sinfo --Node --long`
5. `scontrol show partition`
6. `sacctmgr show tres`
7. `sacctmgr show assoc where user=$USER ...`
8. `sacctmgr show qos ...`
9. `sshare -l`
10. `squeue -u $USER`

If accounting commands fail, say so clearly and continue with whatever read-only controller and partition data is still visible.
