#!/bin/bash
#SBATCH --job-name=fastp_bac
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x.%A_%a.out
#SBATCH --error=logs/%x.%A_%a.err
# Set --array=1-N at submission time, e.g. sbatch --array=1-100 scripts/run_fastp_array.sh samples.tsv

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"

SAMPLES="${1:?Usage: $0 samples.tsv}"
CPUS="${SLURM_CPUS_PER_TASK:-1}"

mkdir -p logs data/clean qc/fastp

# Optional project-specific environment activation:
# eval "$(micromamba shell hook --shell bash)"
# micromamba activate <ENV>

command -v fastp >/dev/null 2>&1 || { echo "ERROR: fastp not found" >&2; exit 127; }

source "${WGS_SKILL:-$PWD}/scripts/array_common.sh"

[[ -n "${sample:-}" ]] || { echo "ERROR: no sample at array index ${SLURM_ARRAY_TASK_ID}" >&2; exit 2; }
[[ -s "$r1" && -s "$r2" ]] || { echo "ERROR: missing R1/R2 for $sample" >&2; exit 2; }

outdir="data/clean/${sample}"
for existing in "$outdir/${sample}_HQ_R1.fq.gz" "$outdir/${sample}_HQ_R2.fq.gz" "qc/fastp/${sample}_QC.json" "qc/fastp/${sample}_QC.html"; do
  [[ ! -e "$existing" && ! -L "$existing" ]] || { echo "ERROR: refusing overwrite: $existing" >&2; exit 4; }
done
mkdir -p "$outdir"

fastp \
  -i "$r1" \
  -I "$r2" \
  -o "${outdir}/${sample}_HQ_R1.fq.gz" \
  -O "${outdir}/${sample}_HQ_R2.fq.gz" \
  --length_required 50 \
  --thread "$CPUS" \
  --json "qc/fastp/${sample}_QC.json" \
  --html "qc/fastp/${sample}_QC.html"

[[ -s "${outdir}/${sample}_HQ_R1.fq.gz" && -s "${outdir}/${sample}_HQ_R2.fq.gz" && -s "qc/fastp/${sample}_QC.json" && -s "qc/fastp/${sample}_QC.html" ]] \
  || { echo "ERROR: clean FASTQ missing for $sample" >&2; exit 3; }

echo "FASTP_COMPLETE $sample"
