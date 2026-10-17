#!/bin/bash
#SBATCH --job-name=spades_bac
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x.%A_%a.out
#SBATCH --error=logs/%x.%A_%a.err
# Submit with --array=1-N.
# This script intentionally processes SHORT samples only.

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

SAMPLES="${1:?Usage: $0 samples.tsv}"
CPUS="${SLURM_CPUS_PER_TASK:-1}"
# Leave 10% of the Slurm allocation for overhead. Slurm reports memory in MiB.
slurm_mem_mb="${SLURM_MEM_PER_NODE:-$(( ${SLURM_MEM_PER_CPU:-0} * CPUS ))}"
[[ "$slurm_mem_mb" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: cannot determine Slurm memory allocation" >&2; exit 2; }
spades_budget_gb=$((slurm_mem_mb * 9 / 10240))
SPADES_MEM_GB="${SPADES_MEM_GB:-$spades_budget_gb}"
[[ "$SPADES_MEM_GB" =~ ^[1-9][0-9]*$ ]] && ((SPADES_MEM_GB <= spades_budget_gb)) || {
  echo "ERROR: SPADES_MEM_GB must be a positive integer <= $spades_budget_gb for this allocation" >&2; exit 2;
}

mkdir -p logs assembly

# Optional project-specific activation:
# eval "$(micromamba shell hook --shell bash)"
# micromamba activate <SPADES_ENV>

SPADES_BIN="${SPADES_BIN:-$(command -v spades.py || true)}"
[[ -n "$SPADES_BIN" ]] || {
  echo "ERROR: spades.py not found. Activate the validated SPAdes environment or set SPADES_BIN." >&2
  exit 127
}

source "${WGS_SKILL:-$PWD}/scripts/array_common.sh"

[[ -n "${sample:-}" ]] || {
  echo "ERROR: no sample at array index ${SLURM_ARRAY_TASK_ID}" >&2
  exit 2
}

# SHORT samples only.
if [[ -n "${long_reads:-}" ]]; then
  echo "SKIP: $sample has long reads and belongs to HYBRID/Unicycler branch."
  exit 0
fi

clean_r1="data/clean/${sample}/${sample}_HQ_R1.fq.gz"
clean_r2="data/clean/${sample}/${sample}_HQ_R2.fq.gz"

[[ -s "$clean_r1" && -s "$clean_r2" ]] || {
  echo "ERROR: clean R1/R2 missing for $sample" >&2
  exit 2
}

sample_dir="assembly/${sample}"
outdir="${sample_dir}/spades"

if [[ -e "${sample_dir}/${sample}.fna" || -L "${sample_dir}/${sample}.fna" || -e "$outdir" || -L "$outdir" ]]; then
  echo "ERROR: existing assembly detected for $sample; refusing silent overwrite: $sample_dir" >&2
  exit 4
fi

mkdir -p "$sample_dir"

# Prefer bacterial-isolate mode. If your installed SPAdes version does not
# support --isolate, set SPADES_ISOLATE=0 at submission time.
if [[ "${SPADES_ISOLATE:-1}" == "1" ]]; then
  "$SPADES_BIN" \
    --isolate \
    -1 "$clean_r1" \
    -2 "$clean_r2" \
    -o "$outdir" \
    -t "$CPUS" \
    -m "$SPADES_MEM_GB"
else
  "$SPADES_BIN" \
    -1 "$clean_r1" \
    -2 "$clean_r2" \
    -o "$outdir" \
    -t "$CPUS" \
    -m "$SPADES_MEM_GB"
fi

[[ -s "${outdir}/contigs.fasta" ]] || {
  echo "ERROR: SPAdes contigs.fasta missing for $sample" >&2
  exit 3
}

cp -n "${outdir}/contigs.fasta" "${sample_dir}/${sample}.fna"

[[ -s "${sample_dir}/${sample}.fna" ]] || {
  echo "ERROR: canonical FASTA missing for $sample" >&2
  exit 3
}

echo "ASSEMBLY_COMPLETE SHORT SPADES $sample"
