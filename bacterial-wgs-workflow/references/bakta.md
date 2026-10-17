# Bakta reference

Default annotation is species-independent.

Do not specify:

```text
--genus
--species
```

Standard pattern:

```bash
bakta ASSEMBLY \
  --db "$BAKTA_DB" \
  --keep-contig-headers \
  --threads "$CPUS" \
  --output "annotation/$sample" \
  --prefix "$sample"
```

Verify `BAKTA_DB` exists before submission.

Prefer Bakta native GenBank-compatible output. GFF→GenBank conversion is only an
optional compatibility step.
