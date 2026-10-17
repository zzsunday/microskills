# Local cluster conventions and script evidence

Use these notes on the cluster used by `/public/home/s20253051191`. Recheck live state before choosing resources. Script contents show historical intent, not proof of successful execution or current policy. On another cluster, discover its conventions independently.

## Evidence reviewed

Inspected on 2026-10-17 under `/public/home/s20253051191/03_scripts`:

| Source | Useful pattern | Checks before reuse |
| --- | --- | --- |
| `spades_para.sh` | One task, 16 CPUs, sample array, partition candidates `Fnode1,Fnode2,Cnode`; SPAdes memory below allocation | Match threads to allocation; size memory for actual data; check every candidate node class |
| `bakta_para.sh` | One task, eight CPUs, one-based array, manifest supplied as first argument | Quote manifest path; validate index and sample; verify environment and database |
| `Slurmsnp2gene_para.sh` | Threads derived from `SLURM_CPUS_PER_TASK`; multistep analysis in a batch allocation | Fix `SAMPLE` versus undefined lowercase `sample` in read paths; propagate failures |
| `SlurmMegahit.sh` | CPU assembly on `Cnode2`, per-sample array | Its 480G request is historical, not a default; check memory headroom and actual need |
| `sample.sh`, `Bakta.sh` | Wrappers generate batch files with heredocs; `Bakta.sh` immediately submits them | Inspect generated files before submission; distinguish generator-time variables from job-time variables |
| `spades_slurm.sh` | Sequential sample loop inside a single allocation | Replace root-directory input/output placeholders; consider an array for independent samples |
| `job_example/ompjob/omp_job.sh` | One task with `OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK` | Verify software and partition; do not copy lowercase `debug` blindly |
| `job_example/mpijob/mpi_job.sh` | Multiple nodes/ranks launched with `srun` | MPI-specific example; verify modules and PMI configuration instead of copying old library paths |

## Controller snapshot

Verified on 2026-10-17 using:

```bash
sinfo -h -O Partition,Available,StateLong,CPUs,Memory,Gres,Time
sinfo -h -o '%P|%a|%l|%c|%m|%G'
scontrol show partition Debug
scontrol show partition Cnode
```

- `Cnode` is the default partition; `Debug`, `Cnode_all`, `Cnode2`, `Cnode3`, `Fnode1`, and `Fnode2` are also advertised. Names are case-sensitive. Advertised availability does not establish the user's association or QoS entitlement.
- `Debug`: one 56-CPU node, 24-hour maximum time. `Cnode`: 56 CPUs per node, approximately 257,429–257,438 MiB memory advertised, two-day default time, 70-day maximum, and `DefMemPerCPU=4096`. Request explicit memory and runtime appropriate to the workload.
- `Cnode2` and `Cnode3` advertise roughly 513,000–515,000 MiB per node; `Fnode1` roughly 1,031,000 MiB and `Fnode2` roughly 2,063,000 MiB. Some partitions contain differing node configurations. Query candidate nodes before committing to a large request.
- `Gnode`, `GnodeA100`, and `Gnode4090` advertise GPU resources. Discover exact GRES and access limits when a GPU task arises; ordinary CPU analyses do not need them.
- No account, user QoS entitlement, submission cap, cluster identity/version, scratch purge rule, or MPI stack was established by this review. Historical scripts omit account/QoS arguments; that does not prove no association limits apply.

Node states and queue pressure are transient and intentionally not retained as defaults.

## Adapting these scripts

### Paths and environments

Many scripts retain `/public/home/bh2022044/...` paths and `~/sunda/...` directories. Treat these as historical references: do not write into another user's tree. Resolve the current project, inputs, database, outputs, and software explicitly. Do not blindly replace usernames and assume the resulting paths exist.

`source ~/.bashrc` followed by `micromamba activate` is common. Environment names include `panaroo`, `bakta`, `asm`, and `snp`; names do not prove that the required executable exists. Confirm working noninteractive activation or use a verified environment executable / `micromamba run`. Batch shells need not load interactive shell initialization. Check legacy startup-file compatibility with strict shell options.

The bioinformatics scripts commonly launch programs directly inside `sbatch` allocations; those programs still run on compute nodes. This observation does not establish a mandatory site launcher policy. Prefer the portable `srun` templates unless a verified application/site requirement calls for another launcher. Never execute the computational body on the login node.

### Arrays and generated jobs

- Existing arrays use `readarray -t list < $inputs` and `${list[$SLURM_ARRAY_TASK_ID-1]}`. Keep the one-based convention only with a matching range; alternatively use zero-based indexing consistently. Quote paths, reject empty/out-of-range entries, and check manifest length and `MaxArraySize` before submission.
- Do not copy fixed ranges such as `1-10` or `1-50` without checking the manifest. Consider `%N` concurrency limits and use `%A_%a` in array log filenames.
- In an unquoted heredoc, generator variables expand immediately. Escape job-time variables, or use a quoted heredoc plus explicit parameters. Inspect the resulting script, not only the generator. Standalone `#SBATCH` directives do not expand shell variables or `~`; use resolved paths or submission options.
- Some wrappers submit inside loops. Reading or editing them is safe; executing them can submit many jobs. Show each complete job-affecting command before execution and stay within the user's authorized task.

### Resources and failure handling

Historical requests span eight to 48 CPUs and 100–480G memory; these are workload examples. Match tool threads to the allocation and leave memory headroom for runtimes and subprocesses. For nested parallel work, keep concurrent workers times threads per worker within allocated CPUs and account for aggregate memory.

Legacy files often omit strict error handling. Add appropriate failure propagation so an early failed analysis cannot be masked by a successful later command. Verify outputs and accounting before treating a job as complete. Keep templates portable and placeholders explicit rather than baking this snapshot into every job.
