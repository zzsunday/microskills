#!/bin/bash
#SBATCH --job-name=<JOB_NAME>
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=<CPUS>
#SBATCH --mem=<MEM>
#SBATCH --time=<TIME>
#SBATCH --output=logs/%x.%A_%a.out
#SBATCH --error=logs/%x.%A_%a.err
#SBATCH --array=1-<N>

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"
CPUS="${SLURM_CPUS_PER_TASK:-1}"

# Activate the validated project environment here if needed.
# eval "$(micromamba shell hook --shell bash)"
# micromamba activate <ENV>

# Replace with stage command.
