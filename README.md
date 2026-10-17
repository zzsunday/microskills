# Microbiome Codex Skills

Reusable **Codex Skills for microbial genomics, metagenomics, microbiome analysis, and bioinformatics workflows**.

This repository provides modular, reproducible, and HPC-friendly workflows that enable Codex to perform common microbial bioinformatics tasks using established tools and explicit analysis rules.

The goal is not to build a single monolithic pipeline. Instead, each workflow is implemented as an independent **Codex Skill** that can be selected and combined according to the biological question and sequencing data.

---

## Overview

Microbial sequencing projects often require many independent tools and analysis decisions:

```text
Raw sequencing data
        ↓
Quality control
        ↓
Genome / metagenome assembly
        ↓
Annotation
        ↓
Taxonomic analysis
        ↓
AMR / virulence analysis
        ↓
Pangenome / phylogenomics
        ↓
Microbiome profiling
        ↓
Functional analysis
        ↓
Statistical interpretation
```

`Microbiome Codex Skills` converts these workflows into reusable Codex Skills.

Each skill defines:

- when the workflow should be used;
- required inputs;
- software and environment requirements;
- analysis logic;
- recommended execution strategy;
- output structure;
- validation rules;
- failure handling;
- reproducibility requirements.

The underlying bioinformatics tools remain standard community software. Codex is responsible for understanding the task, selecting the appropriate workflow, generating or adapting commands, executing the workflow, validating outputs, and summarizing results.

---

# Why Codex Skills?

Traditional pipelines are usually designed around a fixed set of commands:

```text
input
  ↓
command 1
  ↓
command 2
  ↓
command 3
```

Real sequencing projects are often more complicated.

For example:

```text
Illumina only
    ↓
SPAdes

Illumina + ONT
    ↓
Unicycler

Metagenomic reads
    ↓
metaSPAdes / MEGAHIT

RNA-Seq reads
    ↓
rnaSPAdes
```

A Codex Skill can encode this decision logic while keeping the actual workflow reproducible.

The intended model is:

```text
User request
     ↓
Codex
     ↓
Select appropriate Skill
     ↓
Inspect real input data
     ↓
Choose appropriate workflow
     ↓
Execute bioinformatics tools
     ↓
Validate outputs
     ↓
Report results and provenance
```

---

# Repository Scope

This repository is intended to cover three major areas.

## Microbial Genome Analysis

Workflows for isolate whole-genome sequencing and comparative genomics.

Planned or supported analyses include:

```text
FASTQ quality control
Genome assembly
Hybrid assembly
Assembly QC
Genome annotation
Species identification
MLST
AMR gene detection
Virulence gene detection
Plasmid analysis
SNP calling
Core-genome analysis
Pangenome analysis
Phylogenomics
k-mer / unitig analysis
Genome comparison
```

Typical data:

```text
Illumina paired-end
Oxford Nanopore
PacBio
Illumina + long-read hybrid sequencing
```

---

## Metagenomics

Workflows for shotgun metagenomic sequencing.

Planned analyses include:

```text
Read quality control
Host-read removal
Taxonomic profiling
Metagenomic assembly
Gene prediction
Functional annotation
AMR profiling
Virulence profiling
Metagenome binning
MAG reconstruction
MAG quality assessment
Taxonomic classification of MAGs
Abundance estimation
Pathway profiling
Comparative metagenomics
```

Potential workflow:

```text
Raw FASTQ
    ↓
QC
    ↓
Host removal
    ↓
Taxonomic profiling
    ↓
Metagenome assembly
    ↓
Gene prediction
    ↓
Functional annotation
    ↓
Binning
    ↓
MAG QC
    ↓
Taxonomy
    ↓
Abundance / functional analysis
```

---

## Microbiome Analysis

Workflows for microbial community analysis.

Planned analyses include:

```text
16S / amplicon sequencing
Taxonomic abundance analysis
Alpha diversity
Beta diversity
Differential abundance
Community composition
Functional profiling
Metadata integration
Visualization
Statistical analysis
Multi-group microbiome comparisons
```

The repository may support multiple ecosystems, including:

```text
human microbiome
animal microbiome
gut microbiome
environmental microbiome
food microbiome
clinical microbiology
wastewater microbiology
```

---

# Skill Architecture

Each workflow is stored as an independent Skill.

Recommended structure:

```text
skills/
├── bacterial-wgs-workflow/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   └── assets/
│
├── bacterial-amr-analysis/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   └── assets/
│
├── pangenome-analysis/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   └── assets/
│
├── metagenomics-workflow/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   └── assets/
│
└── microbiome-analysis/
    ├── SKILL.md
    ├── references/
    ├── scripts/
    └── assets/
```

A Skill directory may contain:

```text
SKILL.md
    ↓
Workflow instructions and decision logic

references/
    ↓
Methods, tool-specific guidance, biological interpretation rules

scripts/
    ↓
Reusable deterministic scripts

assets/
    ↓
Templates, sample sheets, configuration examples, output schemas
```

---

# Current Skills

## `bacterial-wgs-workflow`

End-to-end workflow for bacterial isolate sequencing.

Supported sequencing configurations:

```text
Illumina paired-end
        ↓
fastp
        ↓
SPAdes
        ↓
QUAST
        ↓
Bakta
```

and:

```text
Illumina paired-end
        +
ONT / PacBio
        ↓
fastp + long-read validation
        ↓
Unicycler hybrid assembly
        ↓
QUAST
        ↓
Bakta
```

The workflow supports:

```text
automatic sample discovery
paired-end validation
Slurm execution
multiple micromamba environments
batch processing
Slurm arrays
assembly QC
species-independent Bakta annotation
workflow summaries
failure detection
resume behavior
```

Bakta annotation is species-independent by default:

```text
no --genus
no --species
```

---

# Planned Skills

Future skills may include:

```text
bacterial-wgs-workflow
bacterial-rnaseq-workflow
bacterial-amr-analysis
bacterial-virulence-analysis
mlst-analysis
plasmid-analysis
snp-analysis
phylogenomics
pangenome-analysis
kmer-unitig-analysis
genome-comparison
metagenomics-qc
metagenomics-taxonomy
metagenomics-assembly
metagenomics-binning
mag-analysis
metagenomics-functional-analysis
microbiome-16s
microbiome-diversity
microbiome-differential-abundance
microbiome-visualization
```

The repository is intended to grow incrementally rather than attempting to implement every workflow at once.

---

# HPC-Oriented Design

Many microbial genomics and metagenomics workflows require substantial CPU,
memory, and storage.

Skills in this repository are therefore designed to work well on shared HPC
systems.

A typical architecture is:

```text
Codex
   ↓
AGENTS.md
   ↓
Skill
   ↓
Slurm
   ↓
micromamba environment
   ↓
Bioinformatics software
```

Computationally intensive operations can be submitted through:

```text
srun
sbatch
Slurm arrays
```

Large sample collections should preferably use parallel sample-level execution
rather than large serial shell loops.

---

# Software Environments

Different bioinformatics tools may exist in different environments.

For example:

```text
tool          environment
--------------------------------
fastp         fastp
SPAdes        unicycler
Unicycler     unicycler
Bakta         bakta
QUAST         quast
Panaroo       panaroo
```

Skills should not assume that every tool belongs to the same environment.

A recommended execution pattern is:

```text
Slurm allocation
      ↓
micromamba activation
      ↓
command -v <tool>
      ↓
<tool> --version
      ↓
workflow execution
```

Project-specific environment mappings should be stored separately from general
Skill logic whenever possible.

---

# Databases

Many microbial bioinformatics tools require external databases.

Examples include:

```text
Bakta database
AMRFinderPlus database
CARD
VFDB
GTDB
Kraken2 database
MetaPhlAn database
eggNOG database
CheckM database
```

Database paths should normally be defined by the local project or HPC
configuration rather than hard-coded into a reusable Skill.

A Skill should:

```text
identify the required database
        ↓
read the configured path
        ↓
verify that the database exists
        ↓
record database version/path
        ↓
run the analysis
```

---

# Reproducibility

Every workflow should preserve sufficient information to reproduce the
analysis.

Whenever possible, Skills should record:

```text
input files
sample IDs
software versions
environment names
database versions
command-line parameters
CPU resources
memory resources
Slurm job IDs
output paths
warnings
workflow status
```

A typical project may contain:

```text
project/
├── data/
├── results/
├── scripts/
├── logs/
├── config/
├── summary/
└── samples.tsv
```

Raw sequencing data should be treated as read-only.

---

# Safety Principles

Skills should never assume unlimited access simply because Codex has permission
to execute commands.

Important principles include:

```text
preserve raw data
do not silently overwrite completed results
do not delete another user's data
do not cancel another user's jobs
do not use sudo unless explicitly authorized
do not silently switch software environments
do not fabricate metadata
do not infer biological conclusions unsupported by the analysis
```

Potentially destructive or scientifically consequential decisions should be
surfaced explicitly.

---

# Installation

A Skill can be installed at the project level:

```bash
mkdir -p .codex/skills

cp -r skills/<skill-name> \
    .codex/skills/
```

or at the user level:

```bash
mkdir -p ~/.codex/skills

cp -r skills/<skill-name> \
    ~/.codex/skills/
```

After installation, start a new Codex session so that the Skill can be
discovered.

---

# Example Usage

For bacterial genome sequencing:

```text
Use the bacterial WGS workflow.

The Illumina paired-end FASTQ files are located in:
01_RawData/

Perform:
quality control → assembly → assembly QC → annotation

Use 16 threads and follow all applicable AGENTS.md instructions.
```

For hybrid sequencing:

```text
Use the bacterial WGS workflow.

The sample contains paired-end Illumina reads and filtered ONT long reads.

Perform hybrid genome assembly, assembly QC, and annotation.
```

For metagenomics:

```text
Use the metagenomics workflow.

Process the paired-end shotgun metagenomic reads in:
01_RawData/

Perform read QC, host filtering, taxonomic profiling, metagenomic assembly,
and functional annotation.
```

---

# AGENTS.md vs Skills

`AGENTS.md` and Skills serve different purposes.

```text
AGENTS.md
    ↓
Persistent project/HPC rules

Skill
    ↓
Task-specific workflow
```

For example, `AGENTS.md` may define:

```text
all computation must use Slurm
raw data must remain read-only
do not operate on other users' files
which micromamba environments are valid
where databases are located
```

while a Skill defines:

```text
which tool to use
which order to run the tools
how to choose among workflow branches
how outputs should be validated
how failures should be handled
```

This separation keeps reusable workflow logic independent from a specific HPC
installation.

---

# Design Philosophy

The project follows several core principles:

```text
Reusable rather than project-specific
Modular rather than monolithic
Adaptive rather than blindly hard-coded
Reproducible rather than interactive-only
HPC-friendly rather than workstation-only
Biologically aware rather than command-only
Conservative with raw data
Explicit about uncertainty
```

The central principle is:

> **Use Codex for workflow reasoning and orchestration while keeping the
> underlying bioinformatics transparent, reproducible, and based on established
> scientific tools.**

---

# Project Roadmap

The long-term goal is to build a reusable collection of Codex Skills covering:

```text
Microbial Genomics
        +
Comparative Genomics
        +
Antimicrobial Resistance
        +
Metagenomics
        +
Microbiome Analysis
        +
Microbial Transcriptomics
```

so that a user can describe the biological task and input data, while Codex
selects and executes an appropriate reproducible workflow.

Conceptually:

```text
Sequencing data
      +
Biological question
      ↓
Codex
      ↓
Microbiome Codex Skills
      ↓
Reproducible bioinformatics workflow
      ↓
Validated results
```

---

# Contributing

Contributions are welcome.

A new Skill should preferably provide:

```text
SKILL.md
references/
scripts/
assets/
README or usage documentation
```

New workflows should avoid hard-coded local paths, usernames, software
installations, database paths, and species-specific assumptions unless they
are intrinsic to the Skill.

---

# Disclaimer

These Skills automate bioinformatics workflows but do not replace scientific
judgment.

Users should independently evaluate:

```text
sequencing design
sample metadata
quality-control thresholds
assembly quality
taxonomic interpretation
statistical assumptions
biological conclusions
```

before using results for research, clinical, diagnostic, or regulatory
purposes.

---

# License

Add the appropriate open-source license for this repository.

A permissive license such as MIT or Apache-2.0 may be suitable depending on the
intended use.
