#!/bin/bash
#SBATCH --job-name=unicycler_hybrid
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x.%A_%a.out
#SBATCH --error=logs/%x.%A_%a.err
# Submit with --array=1-N.
# This script intentionally processes HYBRID samples only.

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

SAMPLES="${1:?Usage: $0 samples.tsv}"
CPUS="${SLURM_CPUS_PER_TASK:-1}"
mkdir -p logs assembly

# Optional activation:
# eval "$(micromamba shell hook --shell bash)"
# micromamba activate <UNICYCLER_ENV>

UNICYCLER_BIN="${UNICYCLER_BIN:-$(command -v unicycler || true)}"
[[ -n "$UNICYCLER_BIN" && -x "$UNICYCLER_BIN" ]] || {
  echo "ERROR: unicycler not found. Activate environment or set UNICYCLER_BIN." >&2
  exit 127
}

source "${WGS_SKILL:-$PWD}/scripts/array_common.sh"

[[ -n "${sample:-}" ]] || {
  echo "ERROR: no sample at index ${SLURM_ARRAY_TASK_ID}" >&2
  exit 2
}

# HYBRID samples only.
if [[ -z "${long_reads:-}" ]]; then
  echo "SKIP: $sample has no long reads and belongs to SHORT/SPAdes branch."
  exit 0
fi

clean_r1="data/clean/${sample}/${sample}_HQ_R1.fq.gz"
clean_r2="data/clean/${sample}/${sample}_HQ_R2.fq.gz"

[[ -s "$clean_r1" && -s "$clean_r2" ]] || {
  echo "ERROR: clean reads missing for $sample" >&2
  exit 2
}

[[ -s "$long_reads" ]] || {
  echo "ERROR: long reads listed but missing/empty for $sample: $long_reads" >&2
  exit 2
}

sample_dir="assembly/${sample}"
outdir="${sample_dir}/unicycler"

if [[ -e "${sample_dir}/${sample}.fna" || -L "${sample_dir}/${sample}.fna" || -e "$outdir" || -L "$outdir" ]]; then
  echo "ERROR: existing assembly detected for $sample; refusing silent overwrite: $sample_dir" >&2
  exit 4
fi

mkdir -p "$sample_dir"

echo "ASSEMBLY_MODE=HYBRID sample=$sample long_platform=${long_platform:-UNKNOWN}"

"$UNICYCLER_BIN" \
  -1 "$clean_r1" \
  -2 "$clean_r2" \
  -l "$long_reads" \
  -o "$outdir" \
  -t "$CPUS"

[[ -s "${outdir}/assembly.fasta" ]] || {
  echo "ERROR: Unicycler assembly.fasta missing for $sample" >&2
  exit 3
}

cp -n "${outdir}/assembly.fasta" "${sample_dir}/${sample}.fna"

[[ -s "${sample_dir}/${sample}.fna" ]] || {
  echo "ERROR: canonical FASTA missing for $sample" >&2
  exit 3
}

echo "ASSEMBLY_COMPLETE HYBRID UNICYCLER $sample"
