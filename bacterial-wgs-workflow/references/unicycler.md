# Unicycler reference

Unicycler is reserved for hybrid bacterial isolate assembly in this skill.

Use it only when the sample has:

```text
clean Illumina R1
clean Illumina R2
usable ONT or PacBio long reads
```

Hybrid command:

```bash
unicycler \
  -1 CLEAN_R1 \
  -2 CLEAN_R2 \
  -l LONG_READS \
  -o OUTDIR \
  -t CPUS
```

Historical validated pattern:

```bash
unicycler \
  -1 A6_18_HQ_R1.fq.gz \
  -2 A6_18_HQ_R2.fq.gz \
  -l 6-18_filtlong.fastq \
  -o 6_18_unicycler \
  -t 16
```

Do not use Unicycler as the default assembler for Illumina-only samples.
Those samples should use SPAdes.

Do not hard-code another user's binary path. Prefer the project's validated
environment or explicitly configured executable.
