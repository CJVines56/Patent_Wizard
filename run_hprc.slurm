#!/bin/bash
# SLURM job script to run backend/app/test_connection.py on a GPU node.

#SBATCH --job-name=patent_ingest
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --output=/scratch/user/%u/patent_ingest_%j.out
#SBATCH --error=/scratch/user/%u/patent_ingest_%j.err

# Fail fast on errors / unset vars / pipe failures
set -euo pipefail

echo "==== SLURM ENVIRONMENT ===="
echo "Host:        $(hostname)"
echo "User:        $USER"
echo "Job ID:      $SLURM_JOB_ID"
echo "Job Name:    $SLURM_JOB_NAME"
echo "Nodes:       $SLURM_JOB_NUM_NODES"
echo "CPUs/Task:   $SLURM_CPUS_PER_TASK"
echo

# ---- Load modules (adjust versions if needed) ----
module purge

# If these exact versions don't exist on Grace, run `module avail Python` and adjust.
module load GCCcore/12.2.0 || { echo "Failed to load GCCcore/12.2.0"; exit 1; }
module load Python/3.10.8  || { echo "Failed to load Python/3.10.8"; exit 1; }
module load CUDA/11.8.0    || { echo "Failed to load CUDA/11.8.0"; exit 1; }

# ---- Paths ----
PROJECT_ROOT="/home/cjvines56/backend"
SCRATCH_ROOT="/scratch/user/$USER"
VENV_PATH="$SCRATCH_ROOT/patent_venv"
EXPORT_PATH="$SCRATCH_ROOT/chunks_with_vectors.jsonl.gz"

echo "Project root:  $PROJECT_ROOT"
echo "Scratch root:  $SCRATCH_ROOT"
echo "Venv path:     $VENV_PATH"
echo "Export path:   $EXPORT_PATH"
echo

# ---- Sanity checks ----
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "ERROR: PROJECT_ROOT '$PROJECT_ROOT' does not exist."
  exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
  echo "ERROR: VENV_PATH '$VENV_PATH' does not exist."
  echo "Create it on a login node with:"
  echo "  cd $SCRATCH_ROOT"
  echo "  python -m venv patent_venv"
  echo "  source patent_venv/bin/activate"
  echo "  pip install -r /home/$USER/backend/requirements.txt"
  exit 1
fi

# ---- Activate venv ----
source "$VENV_PATH/bin/activate"

mkdir -p "$SCRATCH_ROOT"

# ---- Run the job ----
cd "$PROJECT_ROOT"

export USPTO_DATA_ROOT="$SCRATCH_ROOT"
export EMBED_EXPORT_PATH="$EXPORT_PATH"
export INGEST_MODE="export"
export TRANSFORMERS_OFFLINE=1
export HF_HOME="/scratch/user/$USER"
export TRANSFORMERS_CACHE="/scratch/user/$USER"
export COLBERT_MODEL_PATH=/scratch/user/$USER/colbertv2
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1

echo "Running: python app/test_connection.py"
python app/test_connection.py &> "$SCRATCH_ROOT/test_connection.log"

echo
echo "Done. Log:      $SCRATCH_ROOT/test_connection.log"
echo "Embeddings (if written): $EXPORT_PATH"
