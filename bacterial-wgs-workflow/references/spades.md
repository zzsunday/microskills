# SPAdes reference

SPAdes is the default assembler for Illumina-only bacterial isolate WGS in this
skill.

Preferred logic:

```text
Illumina PE only
    ↓
fastp
    ↓
SPAdes
```

Suggested command:

```bash
spades.py \
  --isolate \
  -1 CLEAN_R1 \
  -2 CLEAN_R2 \
  -o OUTDIR \
  -t CPUS \
  -m MEMORY_GB
```

If `--isolate` is not appropriate or supported, use ordinary paired-end mode
without `--isolate`.

Do not use `--meta` for a normal cultured bacterial isolate.

The historical `spades.py --meta` script supplied with this project was written
for wastewater/metagenomic data, so that option must not be transferred into
the isolate workflow.

Use `contigs.fasta` as the default canonical source unless the project
explicitly requires scaffolds.
