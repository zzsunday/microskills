# fastp reference

Default use case: ordinary Illumina paired-end bacterial isolate WGS.

Starting defaults:

```bash
--length_required 50
```

These are starting parameters, not universal biological thresholds.

Always output JSON + HTML QC reports.

Do not hard-code adapters unless the library protocol or observed data supports
doing so.

Do not use this Illumina preprocessing logic for ONT/PacBio reads.
