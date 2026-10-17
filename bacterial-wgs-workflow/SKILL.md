---
name: bacterial-wgs-workflow
description: >
  End-to-end bacterial whole-genome sequencing workflow for bacterial isolates.
  Use this skill when processing bacterial Illumina paired-end sequencing data,
  optionally combined with Oxford Nanopore or PacBio long reads. The workflow
  performs input discovery and validation, Illumina preprocessing with fastp,
  adaptive short-read assembly with SPAdes and hybrid short+long-read assembly
  with Unicycler, assembly quality assessment with QUAST, and species-independent
  genome annotation with Bakta.
  Use this skill for isolate WGS, not metagenomic sequencing, unless explicitly
  instructed otherwise.
---

# Bacterial WGS Workflow

## 1. Purpose

This skill implements a standardized bacterial whole-genome sequencing workflow
from raw sequencing reads to an annotated bacterial genome.

Primary use cases:

1. Illumina paired-end bacterial isolate sequencing.
2. Illumina paired-end sequencing combined with ONT long reads.
3. Illumina paired-end sequencing combined with PacBio long reads.

Assembly policy:
- Illumina-only bacterial isolates → SPAdes.
- Illumina + ONT/PacBio hybrid isolates → Unicycler.
- Unicycler must not be used as the default short-read-only assembler.

Standard workflow:

```text
Raw sequencing reads
        ↓
Input discovery and validation
        ↓
Determine sequencing configuration
        ↓
Illumina preprocessing with fastp
        ↓
Determine assembly strategy
        ↓
┌──────────────────────┬──────────────────────┐
│ Short-read assembly  │ Hybrid assembly      │
│ Illumina only        │ Illumina + long read │
│ SPAdes               │ Unicycler -1 -2 -l   │
└──────────┬───────────┴──────────┬───────────┘
           └───────────┬──────────┘
                       ↓
              Canonical assembly
                       ↓
                     QUAST
                       ↓
                     Bakta
                       ↓
              Standardized outputs
                       ↓
                Workflow summary
```

Adapt the workflow to the actual sequencing data. Do not force all samples
through one fixed assembly command.

## 2. Scope

Use this skill for bacterial isolate WGS.

Do not automatically use this workflow for:

- metagenomic sequencing;
- amplicon/16S sequencing;
- viral or eukaryotic genomes;
- mixed microbial communities.

If input appears metagenomic or mixed-community, stop and determine whether a
metagenomic workflow is required.

## 3. General principles

Always:

1. inspect actual input files before choosing a workflow;
2. preserve original sequencing data;
3. distinguish short-read and hybrid samples;
4. keep samples in independent output directories;
5. follow all applicable parent/project `AGENTS.md` rules;
6. run computation through Slurm when required by `AGENTS.md`;
7. validate outputs after every major stage;
8. record commands, versions, parameters, and failures;
9. avoid hard-coded biological assumptions;
10. do not specify Bakta `--genus` or `--species` by default;
11. do not treat process exit alone as proof of successful analysis.

## 4. Supported sequencing configurations

### SHORT

Illumina paired-end reads only:

```text
R1 + R2
  ↓
fastp
  ↓
clean R1 + clean R2
  ↓
SPAdes isolate assembly
```

Set `ASSEMBLY_MODE=SHORT`.

### HYBRID_ONT

Illumina paired-end + Oxford Nanopore:

```text
Illumina R1/R2 → fastp ────────┐
                               ├→ Unicycler hybrid
ONT reads → validate/QC ───────┘
```

Set `ASSEMBLY_MODE=HYBRID` and `LONG_PLATFORM=ONT`.

### HYBRID_PACBIO

Illumina paired-end + PacBio:

```text
Illumina R1/R2 → fastp ────────┐
                               ├→ Unicycler hybrid
PacBio reads → validate/QC ────┘
```

Set `ASSEMBLY_MODE=HYBRID` and `LONG_PLATFORM=PACBIO`.

### Long-read-only

Long-read-only data are not the primary target of this skill.

If only ONT/PacBio data are present, do not fake paired-end inputs or silently
force the sample through this workflow. Determine whether a long-read-only
assembler such as Flye is appropriate. Ask the user if the strategy cannot be
resolved reliably.

## 5. Input discovery

Recognize common paired-end patterns:

```text
sample_1.fq.gz / sample_2.fq.gz
sample_R1.fq.gz / sample_R2.fq.gz
sample_1.fastq.gz / sample_2.fastq.gz
sample_R1.fastq.gz / sample_R2.fastq.gz
```

Existing cleaned reads may include:

```text
sample_HQ_R1.fq.gz
sample_HQ_R2.fq.gz
```

Possible long-read names include:

```text
sample_filtlong.fastq
sample_filtlong.fastq.gz
sample_ONT.fastq.gz
sample_nanopore.fastq.gz
sample_hifi.fastq.gz
sample_pacbio.fastq.gz
```

File names are hints only. Validate pairing and file integrity.

## 6. Sample manifest

For multiple samples, use `samples.tsv`:

```text
sample_id	r1	r2	long_reads	long_platform
6-18	/path/A6_18_R1.fq.gz	/path/A6_18_R2.fq.gz	/path/6-18_filtlong.fastq	ONT
SA001	/path/SA001_R1.fq.gz	/path/SA001_R2.fq.gz
SA002	/path/SA002_R1.fq.gz	/path/SA002_R2.fq.gz	/path/SA002_hifi.fastq.gz	PACBIO
```

Optional fields may be empty. Do not require genus/species.

## 7. Recommended project structure

```text
project/
├── data/
│   ├── raw/
│   └── clean/
├── qc/
│   ├── fastp/
│   └── quast/
├── assembly/
├── annotation/
├── scripts/
├── logs/
├── summary/
└── samples.tsv
```

Never allow multiple samples to write to the same output directory.

## 8. Raw-data protection

Original sequencing files are read-only inputs.

Never overwrite/delete raw FASTQ or long-read data. Write all processed outputs
to separate directories.

## 9. HPC and Slurm execution

Follow all applicable `AGENTS.md` instructions.

If computation must run through Slurm, then fastp, SPAdes, Unicycler, QUAST,
Bakta, long-read filtering, and other computational stages must run through
Slurm.

For multiple isolates, prefer Slurm arrays.

When using the bundled stage scripts from an installed skill, export `WGS_SKILL`
to this skill directory before submission so each job can load
`scripts/array_common.sh`. Alternatively, copy all scripts together into the
project's `scripts/` directory. See [README.md](README.md) for manifest layout,
stage dependencies, and manual Slurm usage. Validate the manifest before
submission; scripts require exactly five columns in the documented order.

Do not hard-code partitions or excessive resources. Inspect the current HPC and
match resources to the workload.

## 10. Resource selection

Historical scripts may have requested large resources. Do not reuse them
blindly.

Match software threads to `SLURM_CPUS_PER_TASK`.

Avoid oversubscription.

## 11. Software discovery

Primary tools:

```text
fastp
SPAdes
Unicycler
QUAST
Bakta
```

Optional tools:

```text
Filtlong
Flye
GFF→GenBank helper
```

Use the validated environment configured by the project. Do not silently switch
to another environment or system binary.

Record software versions.

## 12. Stage 1 — Illumina preprocessing

Use `fastp` for ordinary Illumina paired-end bacterial WGS.

Standardized outputs:

```text
data/clean/<sample>/<sample>_HQ_R1.fq.gz
data/clean/<sample>/<sample>_HQ_R2.fq.gz
qc/fastp/<sample>_QC.json
qc/fastp/<sample>_QC.html
```

Starting command:

```bash
fastp \
  -i "${R1}" \
  -I "${R2}" \
  -o "data/clean/${sample}/${sample}_HQ_R1.fq.gz" \
  -O "data/clean/${sample}/${sample}_HQ_R2.fq.gz" \
  --length_required 50 \
  --thread "${CPUS}" \
  --json "qc/fastp/${sample}_QC.json" \
  --html "qc/fastp/${sample}_QC.html"
```

These are defaults, not immutable scientific thresholds.

Do not aggressively trim without evidence.

## 13. Adapter trimming policy

For normal Illumina paired-end bacterial WGS, fastp is the default.

Do not manually hard-code adapter sequences unless supported by the library
protocol or data.

For unusual primers, UMIs, linked adapters, or special library designs,
reconsider whether Cutadapt or another specialized tool is more appropriate.

Do not apply Illumina trimming logic to ONT/PacBio reads.

## 14. Stage 1 validation

Verify:

- clean R1/R2 exist and are non-empty;
- fastp JSON/HTML exist;
- fastp exited successfully;
- paired reads remain available.

Inspect fastp metrics if filtering is unexpectedly severe.

## 15. Long-read handling

Do not send ONT/PacBio reads through ordinary Illumina fastp preprocessing.

Determine:

- platform;
- whether reads are raw or already filtered;
- whether adapter/barcode trimming was already performed;
- whether quality filtering already occurred.

If a file is already documented as `*_filtlong.fastq`, treat it as previously
filtered unless evidence indicates otherwise. Do not automatically filter it
again.

## 16. Long-read validation

Before hybrid assembly, check that long reads exist, are non-empty, and contain
valid FASTQ records.

When practical, summarize:

- read count;
- total bases;
- length distribution;
- read N50;
- estimated coverage when genome size can be reasonably estimated.

Do not classify a sample as hybrid merely because a long-read filename exists.

## 17. Stage 2 — Assembly mode selection

Decision:

```text
clean R1 + clean R2
        │
        ▼
usable long reads?
    /          \
   no          yes
   │            │
   ▼            ▼
SHORT        HYBRID
```

Record the selected mode.

## 18. Stage 3A — Short-read assembly

For ordinary bacterial isolate Illumina paired-end sequencing, use SPAdes.

Unicycler is **not** the default short-read-only assembler in this skill.

Input:

```text
data/clean/<sample>/<sample>_HQ_R1.fq.gz
data/clean/<sample>/<sample>_HQ_R2.fq.gz
```

Recommended bacterial isolate command:

```bash
spades.py \
  --isolate \
  -1 "data/clean/${sample}/${sample}_HQ_R1.fq.gz" \
  -2 "data/clean/${sample}/${sample}_HQ_R2.fq.gz" \
  -o "assembly/${sample}/spades" \
  -t "${CPUS}" \
  -m "${SPADES_MEM_GB}"
```

If the installed SPAdes version does not support or does not recommend
`--isolate` for the current input, use ordinary paired-end SPAdes mode instead:

```bash
spades.py \
  -1 "data/clean/${sample}/${sample}_HQ_R1.fq.gz" \
  -2 "data/clean/${sample}/${sample}_HQ_R2.fq.gz" \
  -o "assembly/${sample}/spades" \
  -t "${CPUS}" \
  -m "${SPADES_MEM_GB}"
```

Expected primary assembly:

```text
assembly/<sample>/spades/contigs.fasta
```

Optionally inspect:

```text
assembly/<sample>/spades/scaffolds.fasta
```

Use `contigs.fasta` as the default canonical assembly source unless the project
has an explicit reason to prefer scaffolds.

Do not use:

```bash
spades.py --meta
```

for ordinary cultured bacterial isolates.

The historical `--meta` usage belongs to metagenomic/mixed-community data and
must not be copied into the bacterial-isolate branch.

# 19. Stage 3B — Hybrid assembly

For Illumina + validated ONT/PacBio:

```bash
unicycler \
  -1 "data/clean/${sample}/${sample}_HQ_R1.fq.gz" \
  -2 "data/clean/${sample}/${sample}_HQ_R2.fq.gz" \
  -l "${LONG_READS}" \
  -o "assembly/${sample}" \
  -t "${CPUS}"
```

A validated historical pattern is:

```bash
unicycler \
  -1 A6_18_HQ_R1.fq.gz \
  -2 A6_18_HQ_R2.fq.gz \
  -l 6-18_filtlong.fastq \
  -o 6_18_unicycler \
  -t 16
```

Use current project paths; never hard-code the historical sample/directory.

## 20. Canonical assembly FASTA

All assembly branches must expose:

```text
assembly/<sample>/<sample>.fna
```

Create it safely from SPAdes `spades/contigs.fasta` or Unicycler
`unicycler/assembly.fasta` without deleting the original.

Downstream QC and annotation must use the canonical FASTA.

## 21. SPAdes policy

SPAdes is the default assembler for Illumina-only bacterial isolate samples.

Use:

```text
SHORT → SPAdes
```

Do not use `--meta` for ordinary bacterial isolates.

`--meta` is reserved for metagenomic or mixed-community datasets.

Use `--isolate` when appropriate for a single bacterial isolate and supported by
the installed SPAdes version. Do not force `--isolate` if the actual data or
software version makes it unsuitable.

Unicycler is reserved for hybrid samples in this skill:

```text
HYBRID → Unicycler -1 -2 -l
```

Do not use Unicycler merely because it is installed if the sample contains only
Illumina paired-end reads.

# 22. Stage 4 — Assembly QC

Run QUAST for each successful assembly:

```bash
quast.py \
  "assembly/${sample}/${sample}.fna" \
  -o "qc/quast/${sample}" \
  -t "${CPUS}"
```

Collect at least:

- contig count;
- total length;
- largest contig;
- N50;
- L50;
- GC%;
- N content when available.

## 23. Assembly QC interpretation

Do not impose one universal bacterial genome-size/GC threshold.

Possible status values:

```text
PASS
WARNING
FAIL
```

Flag suspicious assemblies; do not automatically delete them.

## 24. Circularization

For hybrid assemblies, inspect Unicycler circular-contig reports.

Record circular contigs, but do not automatically label every circular contig
as chromosome or plasmid without additional evidence.

## 25. Stage 5 — Bakta annotation

Use Bakta as the default annotation tool.

The routine annotation must be species-independent.

Do **not** add:

```text
--genus
--species
```

by default.

Standard command:

```bash
bakta \
  "assembly/${sample}/${sample}.fna" \
  --db "${BAKTA_DB}" \
  --keep-contig-headers \
  --threads "${CPUS}" \
  --output "annotation/${sample}" \
  --prefix "${sample}"
```

Do not infer taxonomy from directory names, sample names, or previous projects.

## 26. Bakta database

Do not guess the Bakta database path.

Use the project configuration, a validated historical path, or user-provided
path, and verify it exists before submission.

Record Bakta version and database version/path.

## 27. Bakta output validation

Verify the annotation directory and major output files are non-empty.

Typical outputs include:

```text
<sample>.gff3
<sample>.gbff
<sample>.faa
<sample>.ffn
<sample>.fna
<sample>.tsv
```

## 28. GenBank policy

Prefer Bakta native GenBank-compatible output.

Do not routinely convert GFF3 to GenBank.

Use a custom GFF→GenBank helper only when a downstream tool specifically
requires it and Bakta native output is insufficient.

## 29. Batch processing

For many isolates, prefer staged Slurm arrays:

```text
samples.tsv
  ↓
fastp array
  ↓
assembly array
  ↓
QUAST array
  ↓
Bakta array
```

Small batches may run multiple stages in one allocation if efficient and
allowed by `AGENTS.md`.

## 30. Array indexing safety

For `#SBATCH --array=1-N` and `readarray`, use:

```bash
sample=${list[$SLURM_ARRAY_TASK_ID-1]}
```

Verify array bounds match the manifest before submission.

## 31. Environment handling

Use validated environments available to the project.

Do not assume historical environment names or another user's absolute software
paths are portable.

Verify tool resolution before submitting jobs when appropriate.

## 32. Workflow state tracking

Recommended sample states:

```text
INPUT_READY
FASTP_COMPLETE
FASTP_FAILED
ASSEMBLY_COMPLETE
ASSEMBLY_FAILED
QUAST_COMPLETE
QUAST_FAILED
BAKTA_COMPLETE
BAKTA_FAILED
COMPLETE
```

## 33. Workflow summary

Generate:

```text
summary/workflow_summary.tsv
```

Recommended columns:

```text
sample_id
input_type
r1
r2
long_reads
long_platform
fastp_status
reads_before
reads_after
assembly_mode
assembler
assembler_version
assembly_status
contigs
genome_size
largest_contig
n50
l50
gc_percent
circular_contigs
bakta_status
bakta_version
warning
```

Genus/species are not required.

## 34. Logging

Use unique log names. For arrays, prefer:

```text
%x.%A_%a.out
%x.%A_%a.err
```

Do not overwrite previous logs.

## 35. Existing results

Before running a stage, inspect existing outputs.

Do not silently overwrite completed assembly/annotation directories.

Reuse valid results, create versioned outputs, or ask the user when replacement
would be destructive.

## 36. Failure handling

On failure:

1. inspect exit code;
2. inspect stderr/stdout;
3. identify the failing stage;
4. check input integrity;
5. check environment/tool resolution;
6. check resources;
7. check output conflicts.

Do not blindly increase CPU/RAM/time.

## 37. Resume behavior

Resume from the first incomplete/failed stage.

Do not repeat fastp if clean reads are valid and only assembly failed.

Do not rerun assembly if only Bakta failed.

## 38. Reproducibility

Record at minimum:

- fastp version;
- Unicycler version;
- QUAST version;
- Bakta version;
- Bakta DB path/version;
- SPAdes version when relevant;
- commands;
- Slurm resources;
- input/output paths;
- sample manifest.

## 39. Scientific safety

This workflow produces:

```text
clean reads
assembly
assembly QC
annotation
```

It does not automatically prove:

- species/strain identity;
- AMR phenotype;
- virulence phenotype;
- plasmid identity;
- epidemiological relatedness.

Those require explicit downstream analyses.

## 40. Stop-and-ask conditions

Stop and ask when:

- R1/R2 pairing is ambiguous;
- sample identity is ambiguous;
- raw vs clean reads cannot be distinguished;
- long-read platform materially affects processing but is unknown;
- input appears metagenomic rather than isolate;
- existing outputs would require destructive replacement;
- long reads appear unusable;
- sequencing design differs substantially from supported workflows;
- scientifically consequential assembly choices cannot be resolved reliably.

Do not stop for routine reversible operations.

## 41. Autonomous operations

Subject to Runtime approval policy and `AGENTS.md`, routine operations may
proceed autonomously:

- inspect inputs;
- construct/validate `samples.tsv`;
- create output directories;
- submit fastp jobs;
- validate fastp outputs;
- select SHORT/HYBRID;
- submit Unicycler;
- create canonical FASTA;
- submit QUAST;
- collect QC;
- submit Bakta;
- validate annotation;
- generate summaries;
- record versions/commands;
- inspect logs;
- resume after a diagnosed fix.

## 42. Default decision tree

```text
                         INPUT
                           │
                           ▼
                 bacterial isolate data?
                     /            \
                   yes             no
                    │               │
                    │          reconsider
                    │          workflow
                    ▼
               paired Illumina?
                     │
                    yes
                     │
                     ▼
                   fastp
                     │
                     ▼
              clean R1 + clean R2
                     │
                     ▼
            usable long reads?
                /            \
              no              yes
              │                │
              ▼                ▼
            SHORT            HYBRID
              │                │
              ▼                ▼
           SPAdes           Unicycler
                            -1 -2 -l
              │                │
              └───────┬────────┘
                      ▼
             assembly.fasta
                      │
                      ▼
        assembly/<sample>/<sample>.fna
                      │
                      ▼
                    QUAST
                      │
                      ▼
                    Bakta
              no genus/species
                      │
                      ▼
              workflow summary
```

## 43. Final deliverables

Per sample:

```text
clean paired FASTQ
fastp JSON + HTML
SPAdes or Unicycler output
canonical assembly FASTA
QUAST output
Bakta annotation
logs
workflow status
```

Project-level:

```text
samples.tsv
summary/workflow_summary.tsv
summary/software_versions.txt
Slurm scripts
logs
```

## 44. Core principle

```text
inspect actual input
        ↓
classify sequencing configuration
        ↓
preprocess appropriately
        ↓
choose short-read or hybrid assembly
        ↓
normalize to one assembly interface
        ↓
perform common QC
        ↓
perform species-independent annotation
        ↓
validate outputs
        ↓
record provenance
```

> Adapt the workflow to the sequencing data; do not adapt the sequencing data
> to a fixed workflow.
