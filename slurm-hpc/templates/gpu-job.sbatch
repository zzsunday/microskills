#!/bin/bash
# Replace the placeholder values below only after discovering valid partitions,
# accounts, QoS, and GRES names on the target cluster.

#SBATCH --job-name=gpu-example
#SBATCH --account=PROJECT_ACCOUNT
#SBATCH --partition=GPU_PARTITION
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gres=gpu:1
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

# Load site-specific environment here.
# module purge
# module load CUDA_MODULE

srun YOUR_PROGRAM YOUR_ARGS
