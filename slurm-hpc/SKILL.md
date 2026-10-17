---
name: slurm-hpc-operator
description: Inspects and operates Slurm-managed HPC clusters safely and portably. Use when the task involves discovering partitions, accounts, QoS, hardware, GRES, memory or time limits, validating or submitting jobs, monitoring queue state, diagnosing pending jobs, reading accounting data, or canceling jobs without assuming site-specific defaults.
metadata:
  author: TianyuDu
  domain: hpc
  compatibility: Requires Slurm CLI tools in PATH. Accounting and policy visibility may vary by site.
---

# Slurm HPC operator

Treat every cluster as site-specific until verified. Never invent partition names, account names, QoS names, GPU types, memory defaults, submission caps, or time limits.

## Additional resources

- Use `references/command-map.md` for quick command selection.
- Use `references/pending-reasons.md` when a job is pending and the reason needs interpretation.
- Read `references/site-customization.md` when working on this user's cluster or adapting `/public/home/s20253051191/03_scripts`; it distinguishes script patterns from current controller facts.
- Use `templates/cpu-job.sbatch`, `templates/gpu-job.sbatch`, and `templates/array-job.sbatch` as starting points after discovery.

## Core rules

1. Prefer read-only discovery before any submit, cancel, or update action.
2. Discover site policy with Slurm commands instead of assuming it from generic documentation.
3. Report unknown, unavailable, or permission-restricted data explicitly.
4. Avoid admin-mutating commands such as `scontrol update` or `sacctmgr add/modify/delete` unless the user explicitly asks and clearly has admin authority.
5. Use the right execution primitive:
   - `sbatch` submits a batch script.
   - `salloc` obtains an interactive allocation.
   - `srun` launches tasks, including job steps inside an allocation.
6. Prefer `--test-only` when the user wants validation rather than immediate execution.
7. For finished jobs, prefer `sacct`. For running jobs, prefer `squeue`, `scontrol show job`, and `sstat`.
8. Before requesting GPUs or other GRES, discover what the cluster actually advertises.
9. If local man pages or on-cluster behavior differ from public docs, trust the cluster you are on.
10. Prefer explicit resource requests over silent defaults when portability matters.
11. Follow project HPC policy: computation and executable tests belong in Slurm; inspection, editing, downloads, archive handling, and environment management may run on the login node. Background processes and terminal sessions do not provide a compute allocation.
12. Show the exact complete command immediately before a submit, cancel, or other job-affecting action. Never execute unresolved template placeholders.

## Resource and execution selection

Before the first computation or a substantially different computational stage, inspect:

```bash
sinfo -h -O Partition,Available,StateLong,CPUs,Memory,Gres,Time
```

Reuse recent discovery for the same stage. For truncated names or GRES, use `sinfo -h -o '%P|%a|%l|%c|%m|%G'` and targeted partition/node queries.

- Default to CPU; request GPUs only for software that benefits from them.
- Use `srun` for short tests, validation, and debugging; use `sbatch` for production analyses, multistep workflows, memory-intensive work, or expected runtimes above 15 minutes.
- For one threaded program, normally request one node, one task, and `--cpus-per-task` matching its threads. Derive application threads from `SLURM_CPUS_PER_TASK`; control numerical-library threads and nested workers to avoid oversubscription.
- Use arrays for independent samples with a verified manifest, matching index range, and concurrency cap when needed. Concurrent elements multiply per-task CPU and memory requests.
- Estimate memory and runtime from input size, software behavior, and prior usage. Old scripts' allocations are examples, not requirements. Check node capacity and partition/association limits.
- Compare reasonable allocations with `--test-only` when queue delay matters. Favor reliability and time-to-result without reserving resources the application cannot use.

## First-contact workflow on a new cluster

Run these before proposing site-specific `sbatch`, `salloc`, or `srun` commands unless the user already provided verified local details.

### 1) Inspect version and high-level config

```bash
scontrol version
scontrol show config
```

Use this to identify the installed Slurm version and inspect high-level site configuration.

### 2) Discover partitions, default partition, node inventory, and time limits

```bash
sinfo --summarize
sinfo --Node --long
sinfo -o "%#P %.5a %.10l %.10L %.6D %G"
scontrol show partition
```

Look for:

- default partition marker (`*`)
- partition availability and state
- max time
- default time
- node counts
- advertised GRES and GPUs
- partition fields such as `DefaultTime`, `MaxTime`, `DefMemPerNode`, `MaxMemPerNode`, `OverSubscribe`, and `TRES`

If the first view looks incomplete, also try:

```bash
sinfo --all
```

### 3) Inspect node-level hardware when requests depend on CPUs, memory, features, or GPUs

```bash
scontrol show node <node_name>
```

Use this before choosing constraints, features, specific GPU types, or node-local assumptions.

### 4) Discover accounts, QoS, association limits, fairshare context, and TRES

Start with:

```bash
sacctmgr show tres
sacctmgr show assoc where user=$USER format=cluster,account,user,partition,defaultqos,qos,maxjobs,maxsubmitjobs,maxtresperjob,maxtrespernode,maxwall
sacctmgr show qos format=name,grpjobs,grpsubmitjobs,grptres,grpwall,flags
sshare -l
```

Use these to learn:

- valid accounts and partitions attached to the user association
- default QoS and allowed QoS values
- per-user or per-association `MaxJobs` and `MaxSubmitJobs`
- per-job or per-node TRES limits such as CPU, memory, nodes, and `gres/gpu`
- aggregate QoS limits such as `GrpJobs`, `GrpSubmitJobs`, `GrpTRES`, and `GrpWall`
- fairshare and usage context

If these commands fail, state that accounting visibility is restricted or unavailable. Then fall back to `sinfo`, `scontrol`, local site docs, and previously working job scripts.

### 5) Discover array limits only when arrays matter

Inspect `MaxArraySize` in:

```bash
scontrol show config
```

Do not assume job arrays are large enough for the requested fan-out.

### 6) Check queue pressure before submitting

```bash
squeue -u $USER
squeue --start -u $USER
```

Use `--start` only as an estimate. It depends on site scheduling configuration.

## Command map by question

- What partitions exist and which one is default?
  - `sinfo --summarize`
  - `scontrol show partition`
- What hardware exists?
  - `sinfo --Node --long`
  - `scontrol show node <node_name>`
- What GPUs or GRES exist?
  - `sinfo -o "%#P %.6D %G"`
  - `scontrol show node <node_name>`
  - `sacctmgr show tres`
- What time limit can this job use?
  - `scontrol show partition`
  - `sacctmgr show assoc where user=$USER ...`
  - `sacctmgr show qos ...`
- How many jobs can the user submit or run?
  - `sacctmgr show assoc where user=$USER format=cluster,account,user,partition,maxjobs,maxsubmitjobs`
  - `sacctmgr show qos format=name,grpjobs,grpsubmitjobs,flags`
  - `squeue -u $USER`
- Why is a job pending?
  - `squeue -l -j <jobid>`
  - `scontrol show job <jobid>`
- What is a running job using right now?
  - `sstat -j <jobid>`
- What happened after a job finished?
  - `sacct -j <jobid>`

## Submission workflow

### Batch jobs

Use `sbatch` for noninteractive work.

1. Confirm the executable or script, working directory, account, QoS, partition, time limit, nodes, tasks, `cpus-per-task`, memory policy, GRES, and output paths.
2. Validate the request against discovered limits.
3. Prefer explicit requests over silent defaults when portability matters.
4. Dry-run first when appropriate:

```bash
sbatch --test-only job.sh
```

5. Submit only after validation:

```bash
sbatch job.sh
```

### Interactive jobs

Use `salloc` to obtain an allocation and then `srun` inside it, or use `srun` directly when that matches the workflow.

```bash
salloc -p <partition> -A <account> -t <time> ...
srun <program> [args]
```

or

```bash
srun --test-only -p <partition> -A <account> -t <time> ...
srun -p <partition> -A <account> -t <time> ...
```

### Inside batch scripts

Use `srun` for the launched application unless the local site has a documented alternative pattern.

Inspect the complete body before adapting an existing script: a wrapper may generate and immediately submit multiple jobs. Check paths, environment setup, manifest indexing, application threads/memory, failure propagation, and heredoc expansion. Create log directories before submission. Resolve directive values when writing scripts or pass them as submission arguments; Slurm directives are parsed before shell execution.

Keep raw inputs unchanged, preserve important existing results, and record software, parameters, and allocations. Replace template account, partition, executable, and input placeholders; omit optional account/QoS directives when a verified default is appropriate.

## Monitoring and diagnosis

Start with:

```bash
squeue -j <jobid>
squeue -l -j <jobid>
scontrol show job <jobid>
```

For pending jobs:

- read the reported reason
- match it to partitions, QoS, associations, dependencies, or missing resources
- do not guess whether the blocker is partition, QoS, or association without verifying those layers

For running jobs:

```bash
sstat -j <jobid>
```

Use this only for running jobs and expect metric availability to vary by site configuration.

For completed jobs:

```bash
sacct -j <jobid>
```

Use this to inspect elapsed time, state, exit code, node list, requested versus allocated resources, and any recorded blocking reasons.

Capture the submitted job ID and monitor through completion. A useful accounting query is:

```bash
sacct -j <jobid> --format=JobID,JobName,State,Elapsed,ExitCode,AllocCPUS,MaxRSS
```

Inspect job steps, stdout/stderr, and expected outputs. Report success only after acceptable exit codes and non-empty, plausible outputs are verified. If accounting is unavailable, state the limitation and use remaining controller state, logs, and artifacts; disappearing from `squeue` alone does not prove success.

Diagnose failures before resubmission: distinguish OOM, timeout, application/environment errors, and infrastructure failure. Adjust only the relevant resources or code; use a small `srun` reproduction when helpful.

## Cancellation and cleanup

Use:

```bash
scancel <jobid>
```

Cancel only when the user explicitly asks or when cleanup is clearly required by the workflow.

## How to reason about limits

Do not assume there is one global limit knob. Check multiple layers.

Inspect:

1. partition data from `scontrol show partition`
2. QoS data from `sacctmgr show qos`
3. user and account associations from `sacctmgr show assoc where user=$USER`
4. pending reason codes from `squeue` or `scontrol show job`
5. fairshare from `sshare -l`

When a request is blocked, explain which layer appears responsible and which command established that conclusion.

## Permissions and missing data

If a command is restricted or unavailable:

- say which command failed
- say what category of certainty was lost
- fall back to other visible Slurm state
- do not invent missing limits

Examples:

- "I can see partitions and node states, but I cannot see accounting or QoS associations for this user."
- "I can see GPU GRES on nodes, but I cannot confirm which QoS or account limits apply to GPU jobs."
- "I cannot confirm submission caps from controller state alone; I need `sacctmgr` output or local site docs."

## Response checklist

When helping interactively:

1. summarize verified cluster facts first
2. list the exact commands used to verify them
3. propose the smallest valid `sbatch`, `salloc`, or `srun` command or script
4. separate verified facts from assumptions
5. prefer "unknown" over a guess
