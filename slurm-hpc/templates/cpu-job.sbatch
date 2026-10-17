#!/bin/bash
# Replace the placeholder values below with cluster-specific values discovered
# from sinfo, scontrol, sacctmgr, and local site documentation.

#SBATCH --job-name=cpu-example
#SBATCH --account=PROJECT_ACCOUNT
#SBATCH --partition=CPU_PARTITION
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

# Load site-specific environment here.
# module purge
# module load TOOLCHAIN_MODULE

srun YOUR_PROGRAM YOUR_ARGS
