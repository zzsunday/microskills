#!/bin/bash
# Shared manifest handling. Source only from a Slurm array stage.
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_ARRAY_TASK_ID:-}" =~ ^[1-9][0-9]*$ ]] || {
  echo "ERROR: submit this stage as a Slurm array (indices start at 1)." >&2
  exit 2
}
expected_header=$'sample_id\tr1\tr2\tlong_reads\tlong_platform'
IFS= read -r manifest_header < "$SAMPLES"
[[ "$manifest_header" == "$expected_header" ]] || {
  echo "ERROR: manifest must have exactly these five columns: $expected_header" >&2
  exit 2
}
line=$((SLURM_ARRAY_TASK_ID + 1))
row=$(sed -n "${line}p" "$SAMPLES")
tabs=${row//[!$'\t']/}
[[ ${#tabs} == 4 && "$row" != *$'\r'* && "$row" != *$'\034'* ]] || {
  echo "ERROR: missing or malformed manifest row at array index $SLURM_ARRAY_TASK_ID" >&2
  exit 2
}
# Bash collapses adjacent whitespace delimiters (including tabs). A non-whitespace
# delimiter preserves empty optional columns, avoiding accidental branch changes.
IFS=$'\034' read -r sample r1 r2 long_reads long_platform <<< "${row//$'\t'/$'\034'}"
[[ "$sample" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || {
  echo "ERROR: unsafe sample_id: $sample" >&2
  exit 2
}
[[ -n "$long_reads" && "$long_platform" =~ ^(ONT|PACBIO)$ || -z "$long_reads" && -z "$long_platform" ]] || {
  echo "ERROR: long reads require long_platform ONT or PACBIO; short samples leave both empty." >&2
  exit 2
}
