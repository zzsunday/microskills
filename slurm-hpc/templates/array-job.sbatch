#!/bin/bash
# Update the array range only after checking MaxArraySize and local norms.
# Keep the array size synchronized with the number of inputs below.

#SBATCH --job-name=array-example
#SBATCH --account=PROJECT_ACCOUNT
#SBATCH --partition=CPU_PARTITION
#SBATCH --time=00:10:00
#SBATCH --array=0-2%1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --output=%x-%A_%a.out
#SBATCH --error=%x-%A_%a.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

INPUTS=(
  input_a
  input_b
  input_c
)

ITEM="${INPUTS[$SLURM_ARRAY_TASK_ID]}"

srun YOUR_PROGRAM "$ITEM"
