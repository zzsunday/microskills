#!/bin/bash
#SBATCH --job-name=bakta_bac
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x.%A_%a.out
#SBATCH --error=logs/%x.%A_%a.err
# Submit with --array=1-N

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

SAMPLES="${1:?Usage: $0 samples.tsv}"
: "${BAKTA_DB:?Set BAKTA_DB to the Bakta database directory}"
CPUS="${SLURM_CPUS_PER_TASK:-1}"

mkdir -p logs annotation

# Optional activation:
# eval "$(micromamba shell hook --shell bash)"
# micromamba activate <BAKTA_ENV>

command -v bakta >/dev/null 2>&1 || { echo "ERROR: bakta not found" >&2; exit 127; }
[[ -d "$BAKTA_DB" ]] || { echo "ERROR: BAKTA_DB does not exist: $BAKTA_DB" >&2; exit 2; }

source "${WGS_SKILL:-$PWD}/scripts/array_common.sh"

asm="assembly/${sample}/${sample}.fna"
[[ -s "$asm" ]] || { echo "ERROR: assembly missing for $sample: $asm" >&2; exit 2; }

out="annotation/${sample}"
if [[ -e "$out" || -L "$out" ]]; then
  echo "ERROR: annotation directory already contains files; refusing silent overwrite: $out" >&2
  exit 4
fi

bakta \
  "$asm" \
  --db "$BAKTA_DB" \
  --keep-contig-headers \
  --threads "$CPUS" \
  --output "$out" \
  --prefix "$sample"

# Species-independent by design: no --genus / --species.
for ext in gff3 gbff faa ffn fna tsv; do
  [[ -s "$out/$sample.$ext" ]] || { echo "ERROR: Bakta output missing/empty: $out/$sample.$ext" >&2; exit 3; }
done

echo "BAKTA_COMPLETE $sample"
