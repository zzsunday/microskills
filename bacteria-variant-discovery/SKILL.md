---
name: bacteria-variant-discovery
description: Detect bacterial SNPs and small INDELs from paired-end reads or genome assemblies using VariantDetective, annotate the reference with Bakta, and map variants to gene context with ~/03_scripts/snp2gene.py. Use for reference-based variant calling and gene mapping, not read preprocessing, assembly, or phenotype association.
---

# Bacteria Variant Discovery

## Purpose and inputs

Run the user's three-stage workflow:

```text
reference FASTA + query paired-end reads (or query assembly)
    ↓
VariantDetective snp_indel
    ↓
Bakta annotation of the same reference FASTA
    ↓
snp2gene.py → sample_snp2gene.tab
```

The preferred mode when paired-end reads are supplied is `-1 R1 -2 R2`. A query assembly is not required in that mode. Retain assembly-based `-g` calling as an alternative when only a query FASTA is supplied and the installed version supports it. Do not assemble reads merely to run this skill, substitute an assembly for supplied reads, or require reads when the user selects assembly mode.

Required inputs:

- One bacterial reference FASTA, used consistently for calling and annotation.
- Per query sample: paired-end R1/R2 FASTQ, preferably already cleaned, or an assembled FASTA (`.fasta`, `.fa`, or `.fna`).
- Unique sample IDs and independent output directories.
- Validated VariantDetective, Bakta, and Python environments; the mapper's Python must contain `click` and `pandas`.
- A verified Bakta database directory and the local mapper `~/03_scripts/snp2gene.py`.

Inspect actual files, read pairing, and reference/query compatibility. Do not infer pairing or biological suitability solely from names. Preserve original reads, assemblies, reference, and variant outputs. Read preprocessing, genome assembly, standalone annotation, AMR screening, phylogeny, and phenotype association belong to separate workflows.

For batches, use a manifest such as:

```text
sample_id\tr1\tr2\tquery_fasta
sample01\t/path/sample01_HQ_R1.fq.gz\t/path/sample01_HQ_R2.fq.gz\t
sample02\t\t\t/path/sample02.fasta
```

The displayed `\t` denotes a tab. Select one input mode per sample and validate the selected fields. Keep accession periods intact when deriving sample IDs from filenames; remove only the final extension. Reject duplicate sample IDs and ambiguous input-mode choices.

## Execution and environment policy

Follow project `AGENTS.md`. Run variant detection, Bakta, mapping, computational conversions, and executable tests through Slurm. File inspection and editing may run on the login node. Before a new computational stage, inspect:

```bash
sinfo -h -O Partition,Available,StateLong,CPUs,Memory,Gres,Time
```

Select CPU, memory, partition, and runtime for the actual workload; default to CPU. Match tool threads to `SLURM_CPUS_PER_TASK`. Show exact complete job-affecting commands before execution. Use `srun` for short checks and `sbatch` for production workflows. All execution examples below are compute-job bodies.

Verify installed command syntax with local help inside a short Slurm allocation when needed. Do not invent options. Resolve actual environments explicitly; do not copy another user's environment paths. Use validated executable paths or explicit environment activation for each stage. Switching from the caller to Bakta and then to the mapper's Python is allowed and often necessary.

## 1. Detect variants

Inside the job, initialize and validate the supplied values:

```bash
set -euo pipefail
: "${REF:?Set REF to the reference FASTA}"
: "${SAMPLE:?Set SAMPLE to a unique sample ID}"
: "${SLURM_CPUS_PER_TASK:?Run inside a Slurm allocation}"
THREADS="$SLURM_CPUS_PER_TASK"
test -s "$REF"
```

For paired-end input, follow the user's command:

```bash
: "${R1:?Set R1 to the first paired-end FASTQ}"
: "${R2:?Set R2 to the second paired-end FASTQ}"
test -s "$R1"
test -s "$R2"
test ! -e "$SAMPLE" && test ! -L "$SAMPLE"

variantdetective snp_indel \
    -r "$REF" \
    -1 "$R1" \
    -2 "$R2" \
    -t "$THREADS" \
    -o "$SAMPLE"
```

For assembly input instead, after confirming local support:

```bash
: "${QUERY_FASTA:?Set QUERY_FASTA to the query assembly}"
test -s "$QUERY_FASTA"
test ! -e "$SAMPLE" && test ! -L "$SAMPLE"

variantdetective snp_indel \
    -r "$REF" \
    -g "$QUERY_FASTA" \
    -t "$THREADS" \
    -o "$SAMPLE"
```

Use a project working directory and a safe sample ID; `$SAMPLE` above is the per-sample detection directory. A project may instead set a distinct `sample_out` path and use that consistently below. Do not silently overwrite results or skip an existing directory without checking completion.

Confirm the final call table. The user's local workflow expects:

```bash
SNP_TABLE="$SAMPLE/snp_indel/snp_final.tab"
test -s "$SNP_TABLE"
```

Inspect actual outputs and the header before relying on that path; installed versions can differ. Preserve all final SNP and INDEL calls, including any VCFs. Do not replace final consensus/filtered calls with intermediate caller-specific outputs.

## 2. Annotate the reference with Bakta

Annotate the same `$REF` used for detection. `--keep-contig-headers` is essential for matching SNP `CHROM` to reference features. Use the user's skip flags when supported by the installed version. Inside the validated Bakta environment:

```bash
: "${BAKTA_DB:?Set BAKTA_DB to the verified Bakta database}"
test -d "$BAKTA_DB"
bakta_out="bakta/${SAMPLE}"
test ! -e "$bakta_out" && test ! -L "$bakta_out"
mkdir -p bakta

bakta "$REF" \
    --db "$BAKTA_DB" \
    --keep-contig-headers \
    --threads "$THREADS" \
    --skip-ncrna-region \
    --skip-crispr \
    -o "$bakta_out" \
    --prefix "$SAMPLE"

Anno="$bakta_out/${SAMPLE}.tsv"
test -s "$Anno"
```

The example uses `bakta/<sample>` to avoid batch collisions. For multiple queries using an identical reference, annotate it once in a reference-specific directory and set `Anno` to that shared TSV for all matching samples. Verify reference identity and sequence IDs before reusing annotation; do not annotate a query genome for reference-coordinate calls.

The historical example includes `--force`. Add it only when deliberate replacement is authorized and existing results have been inspected/preserved; it is unnecessary for a new output directory. Do not copy historical user-specific software or database paths blindly. Do not add genus/species assumptions.

## 3. Map variants to genes

Read [the mapper compatibility and validation procedure](references/snp-gene-annotation.md) before this step. Confirm the final table has reference `CHROM`/`POS` fields and matches the Bakta TSV format. Then use the user's mapper, with the current home directory:

```bash
: "${SNP2GENE_PYTHON:?Set SNP2GENE_PYTHON to Python with click and pandas}"
snp2gene_script="$HOME/03_scripts/snp2gene.py"
annotation_out="${SAMPLE}_snp2gene.tab"
test -s "$snp2gene_script"
test -s "$Anno"
test ! -e "$annotation_out" && test ! -L "$annotation_out"

"$SNP2GENE_PYTHON" "$snp2gene_script" \
    --snp "$SNP_TABLE" \
    --anno "$Anno" \
    --out "$annotation_out"

test -s "$annotation_out"
```

If the active Python is already validated, `python "$HOME/03_scripts/snp2gene.py" ...` is equivalent. Handle a zero-row final table before invocation as documented in the reference.

The mapper assigns coding genes or intergenic neighbors by reference position. If the final table contains INDELs, retain their original calls; mapping their anchor positions is permitted, but must not be described as a full interval/consequence annotation. A SNP-only secondary deliverable may be derived if requested.

## Batch execution, validation, and resume

Use the same reference for samples whose genomic coordinates will be compared. Prefer per-sample Slurm arrays; annotate a shared reference once and make mapping depend on successful calling and annotation. Keep output directories and log names unique, cap concurrency appropriately, and avoid oversubscribing CPUs or memory.

Capture job IDs, monitor through completion, and inspect accounting state/exit codes, logs, and expected outputs. Verify mapping row counts equal the selected input rows, original variant fields are preserved, and sequence IDs match. Record detection, Bakta, and mapping status separately; an existing output directory or disappearance from `squeue` alone does not prove success.

On failure, diagnose input, environment, format, memory, runtime, and output conflicts before retrying. Reuse verified calls/annotation and resume mapping without repeating completed stages. Do not delete or overwrite raw inputs or important results.

## Deliverables and interpretation

For each sample provide original VariantDetective calls, the matching reference Bakta annotation (shared where appropriate), and `<sample>_snp2gene.tab`. For no variants, preserve the header-only input, produce a header-only annotation table, and report `NO_VARIANTS`; use `NO_SNPS` for an empty SNP-only selection.

Record sample ID, input mode/paths, reference identity, variant table, Bakta TSV, annotation table, stage status, commands, software versions, mapper checksum/version, environment, Bakta database version/path, and Slurm resources. Keep REF/ALT and variant types; do not discard INDELs from the primary calls.

Gene-context annotation does not establish synonymous/nonsynonymous effects, protein changes, antimicrobial resistance, virulence, adaptation, or causality. Preserve supported functional annotations from other tools without fabricating missing fields. Those interpretations require separate analyses.
