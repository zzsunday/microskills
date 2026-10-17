# Bacterial isolate WGS workflow

Quality control, assembly, assembly assessment, and annotation for cultured
bacterial isolates. Use as a Codex skill or run the included Slurm stage scripts.

```text
Illumina paired-end → fastp → SPAdes ────────────┐
                                               ├→ canonical FASTA → QUAST → Bakta
Illumina paired-end → fastp ──┐                 │
Validated ONT/PacBio reads ───┴→ Unicycler hybrid┘
```

This workflow expects one isolate per sample. Metagenomes, amplicons, and
long-read-only projects need a different workflow. Long reads are not filtered
automatically. Bakta runs without inferred genus/species metadata.

## Use with Codex

Install this directory at `~/.codex/skills/bacterial-wgs-workflow`, or in your
project's `.codex/skills/` directory, then start a new session. Example request:

> Use $bacterial-wgs-workflow to process the isolates in data/raw. Review the
> sample pairing, run all computation through Slurm, and use my validated Bakta
> database. Inspect existing results before submitting jobs.

The remaining instructions describe manual operation. All commands assume the
current directory is your analysis project, where results should be stored.

## Requirements

- Bash, Python 3 (standard library for manifest/summary helpers), and Slurm.
- Validated installations of fastp, SPAdes, Unicycler for hybrid samples,
  QUAST, and Bakta with its dependencies.
- A downloaded Bakta database compatible with the installed Bakta release.
- Sufficient project storage for reads, assembler intermediates, and annotations.

Activate the appropriate environment before submitting each stage, or add its
activation to a project copy of the stage script. Slurm must inherit a usable
`PATH`. Different stages may use different environments. The optional
`gff3_to_gbk.py` helper has additional dependencies; prefer Bakta's native `.gbff`.

Official tool documentation: [fastp](https://github.com/OpenGene/fastp),
[SPAdes](https://ablab.github.io/spades/running.html),
[Unicycler](https://github.com/rrwick/Unicycler),
[QUAST](https://quast.sourceforge.net/docs/manual.html), and
[Bakta](https://github.com/oschwengers/bakta).

## 1. Prepare the project and resources

Set `WGS_SKILL` to the installed workflow directory. The following default uses
the user-level installation; adjust it if installed elsewhere.

```bash
export WGS_SKILL="$HOME/.codex/skills/bacterial-wgs-workflow"
mkdir -p data/raw logs summary
sinfo -h -O Partition,Available,StateLong,CPUs,Memory,Gres,Time
```

Select a permitted CPU partition, account/QoS if required, memory, CPUs, and
runtime from actual cluster limits and sample size. GPU resources are unnecessary.
The scripts provide starting allocations, which can be overridden at submission:

| Stage | CPUs per sample | Memory | Time limit |
| --- | ---: | ---: | ---: |
| fastp | 16 | 16G | 4 hours |
| SPAdes | 16 | 32G | 12 hours |
| Unicycler | 16 | 32G | 12 hours |
| QUAST | 8 | 8G | 2 hours |
| Bakta | 8 | 16G | 4 hours |

These are starting requests, not measured guarantees. Reassess them for large or
high-coverage genomes. Set shell variables `PARTITION` and, for helper commands,
`PYTHON` to your chosen partition and Python executable (for example `python3`).
Examples below assume your default account/QoS is valid; add `--account`/`--qos`
when required. Never run unresolved examples. Create `logs/` before submission:
Slurm opens its logs before the script starts.

All Python execution, validation, and analysis must use Slurm under this
project's HPC policy. File inspection, editing, downloads, and installation may
run on the login node. Print each fully expanded `srun`/`sbatch` command before
executing it; the examples below do so.

## 2. Create and validate samples.tsv

You can write the manifest manually using `assets/samples_template.tsv`, or
generate a starter manifest from filenames:

```bash
cmd=(srun -p "${PARTITION:?Set PARTITION}" -N 1 -n 1 -c 1 --mem=1G -t 00:05:00
     "${PYTHON:?Set PYTHON}" "$WGS_SKILL/scripts/build_samplesheet.py" data/raw -o samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
"${cmd[@]}"
```

The builder recognizes `_R1`/`_R2` (including `_001`) and `_1`/`_2` FASTQ names,
with `.fq`/`.fastq` and optional gzip compression. It searches recursively,
refuses duplicate mates/long-read candidates, and refuses to overwrite a manifest.
Multi-lane reads require deliberate preparation; filenames alone do not reliably
identify lane relationships. Long-read filename hints require manual review.

Use this exact header and five tab-separated columns in every row:

```text
sample_id<TAB>r1<TAB>r2<TAB>long_reads<TAB>long_platform
```

`<TAB>` above means a literal tab. For Illumina-only rows, keep the last two
fields empty, including both trailing tabs. For hybrid rows, provide a long-read
path and exactly `ONT` or `PACBIO`. Use Unix LF line endings, a final newline,
and no blank lines. IDs must start with a letter or digit and contain only
letters, digits, underscores, periods, or hyphens. Use absolute read paths when
possible; relative paths resolve against the project working directory.

Review sample identities and paths, then validate:

```bash
cmd=(srun -p "$PARTITION" -N 1 -n 1 -c 1 --mem=1G -t 00:05:00
     "$PYTHON" "$WGS_SKILL/scripts/validate_samplesheet.py" samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
"${cmd[@]}"
```

Validation checks layout, IDs, duplicate/reused inputs, non-empty files, and
platform values. It does **not** decompress reads, validate FASTQ records, check
mate synchronization, or establish sample purity. Check FASTQ/gzip integrity and
paired read names with suitable tools in a Slurm allocation before production
assembly. Review long-read quality, lengths, coverage, and preprocessing history.
Do not filter already filtered reads again without a reason.

## 3. Submit fastp

Freeze the validated manifest for the run; do not reorder or edit it while jobs
are pending/running. Set `N` from its number of sample rows:

```bash
N=$(awk 'END {print NR-1}' samples.tsv)
[[ "$N" =~ ^[1-9][0-9]*$ ]] || { echo 'No samples'; exit 1; }
cmd=(sbatch --parsable --partition="$PARTITION" --array="1-$N%4"
     "$WGS_SKILL/scripts/run_fastp_array.sh" samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
fastp_job=$("${cmd[@]}")
fastp_job=${fastp_job%%;*}
printf 'fastp job: %s\n' "$fastp_job"
```

`%4` limits concurrent samples; adapt it to site limits and shared storage.
The minimum retained read length is 50 bases. Quality filtering and adapter
processing follow fastp defaults. Adjust settings for your libraries and inspect
the JSON/HTML reports.

## 4. Submit assembly and downstream stages

The same manifest can feed both assemblers: SPAdes skips hybrid rows and
Unicycler skips short-only rows. For a uniform batch, submit only the relevant
assembler and use only its job ID in downstream dependencies.

The mixed-batch example below queues assembly after fastp succeeds:

```bash
cmd=(sbatch --parsable --partition="$PARTITION" --array="1-$N%4"
     --dependency="afterok:$fastp_job"
     "$WGS_SKILL/scripts/run_spades_array.sh" samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
spades_job=$("${cmd[@]}"); spades_job=${spades_job%%;*}

cmd=(sbatch --parsable --partition="$PARTITION" --array="1-$N%4"
     --dependency="afterok:$fastp_job"
     "$WGS_SKILL/scripts/run_unicycler_array.sh" samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
hybrid_job=$("${cmd[@]}"); hybrid_job=${hybrid_job%%;*}

cmd=(sbatch --parsable --partition="$PARTITION" --array="1-$N%4"
     --dependency="afterok:$spades_job:$hybrid_job"
     "$WGS_SKILL/scripts/run_quast_array.sh" samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
quast_job=$("${cmd[@]}"); quast_job=${quast_job%%;*}
```

`afterok` waits for the entire upstream array to succeed. One failed task blocks
the dependent stage; it does not automatically retry failures. Review QUAST
before annotation. This reference-free report describes contiguity, length, and
GC; it does not establish completeness, purity, or correct structure. Interpret
metrics using organism-specific expectations and additional analyses as needed.

SPAdes defaults to `--isolate`, intended for high-coverage isolate data. Set
`SPADES_ISOLATE=0` in the submission environment when ordinary paired-end mode
is more appropriate. Its memory cap defaults to 90% of allocated Slurm memory,
rounded down to integer GiB; `SPADES_MEM_GB` may set a smaller cap. Override
Slurm `--mem` too if more memory is needed. `SPADES_BIN`, `UNICYCLER_BIN`, and
`QUAST_BIN` can select validated executables explicitly.

Set `BAKTA_DB` to your real compatible database directory and submit annotation
once assembly QC is acceptable:

```bash
: "${BAKTA_DB:?Export BAKTA_DB to the validated database directory}"
export BAKTA_DB
cmd=(sbatch --parsable --partition="$PARTITION" --array="1-$N%4"
     --dependency="afterok:$quast_job"
     "$WGS_SKILL/scripts/run_bakta_array.sh" samples.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
bakta_job=$("${cmd[@]}"); bakta_job=${bakta_job%%;*}
```

Keep a record of job IDs, the manifest, software/environment versions, Bakta
database version/path, resource overrides, and commands. The helpers do not
automatically populate all provenance fields.

## 5. Monitor, verify, and summarize

```bash
squeue -j "$bakta_job"
sacct -j "$fastp_job,$spades_job,$hybrid_job,$quast_job,$bakta_job" \
  --format=JobID,JobName,State,Elapsed,ExitCode,AllocCPUS,MaxRSS
```

For a single assembly branch, omit the unused job variable from accounting.
Inspect `logs/*.out` and `logs/*.err`, verify successful exit codes, and inspect
non-empty, plausible stage outputs before reporting completion. Submission alone
does not mean success. After jobs finish, generate the summary:

```bash
cmd=(srun -p "$PARTITION" -N 1 -n 1 -c 1 --mem=1G -t 00:05:00
     "$PYTHON" "$WGS_SKILL/scripts/summarize_workflow.py" samples.tsv
     -o summary/workflow_summary.tsv)
printf '%q ' "${cmd[@]}"; printf '\n'
"${cmd[@]}"
```

Summary statuses are based on available report/output files, not Slurm exit
status or a biological PASS/FAIL decision. Missing QUAST metrics produce a
warning. `reads_before`/`reads_after` are fastp total read counts across both
mates, not read-pair counts. Assembler/Bakta version and circular-contig columns
remain empty unless populated separately. Inspect Unicycler reports for
circularization; circularity alone does not identify a chromosome or plasmid.

## Outputs

| Result | Location |
| --- | --- |
| Clean paired reads | `data/clean/SAMPLE/SAMPLE_HQ_R{1,2}.fq.gz` |
| Read QC | `qc/fastp/SAMPLE_QC.json`, `SAMPLE_QC.html` |
| Short-read assembly | `assembly/SAMPLE/spades/contigs.fasta` |
| Hybrid assembly | `assembly/SAMPLE/unicycler/assembly.fasta` |
| Canonical assembly, copied from the selected assembler | `assembly/SAMPLE/SAMPLE.fasta` |
| Assembly QC | `qc/quast/SAMPLE/report.tsv` and other QUAST reports |
| Annotation | `annotation/SAMPLE/SAMPLE.{gff3,gbff,faa,ffn,fna,tsv}` |
| Slurm logs | `logs/STAGE.JOBID_TASKID.{out,err}` |
| Combined summary | `summary/workflow_summary.tsv` |

## Failures and reruns

Scripts refuse existing stage outputs, including partial assembly directories.
They do not automatically resume, skip completed results, or delete failed data.
Diagnose stderr/accounting first. Preserve an old or failed output directory by
moving it to a reviewed archive location before deliberately rerunning that
stage. Keep canonical FASTA and assembler outputs together when archiving an
assembly. Raw reads must remain untouched.

To retry selected samples, use their original manifest row indices (for example
`--array=2,5`) and submit only the failed stage after correcting the cause.
If only Bakta failed, reuse the validated assembly. A failed upstream dependency
may leave old downstream jobs pending indefinitely: inspect those jobs and
replace their submissions/dependencies deliberately. Never resubmit a full
array blindly over successful outputs.

This workflow does not automatically establish species identity, AMR/virulence
phenotype, contamination level, or epidemiological relatedness. Plan those
analyses separately when they are part of the research question.
