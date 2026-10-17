#!/bin/bash
#SBATCH --job-name=quast_bac
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x.%A_%a.out
#SBATCH --error=logs/%x.%A_%a.err
# Submit with --array=1-N

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

SAMPLES="${1:?Usage: $0 samples.tsv}"
CPUS="${SLURM_CPUS_PER_TASK:-1}"
mkdir -p logs qc/quast

# Optional activation:
# eval "$(micromamba shell hook --shell bash)"
# micromamba activate <QUAST_ENV>

QUAST_BIN="${QUAST_BIN:-$(command -v quast.py || command -v quast || true)}"
[[ -n "$QUAST_BIN" ]] || { echo "ERROR: QUAST not found" >&2; exit 127; }

source "${WGS_SKILL:-$PWD}/scripts/array_common.sh"

asm="assembly/${sample}/${sample}.fasta"
[[ -s "$asm" ]] || { echo "ERROR: assembly missing for $sample: $asm" >&2; exit 2; }

out="qc/quast/${sample}"
if [[ -e "$out" || -L "$out" ]]; then
  echo "ERROR: existing QUAST result for $sample; refusing silent overwrite: $out" >&2
  exit 4
fi

"$QUAST_BIN" "$asm" -o "$out" -t "$CPUS"
[[ -s "$out/report.tsv" ]] || { echo "ERROR: QUAST report.tsv missing for $sample" >&2; exit 3; }

echo "QUAST_COMPLETE $sample"
