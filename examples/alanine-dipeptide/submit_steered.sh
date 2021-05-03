#!/bin/bash -l
#SBATCH -J test-ala
#SBATCH -N 1
#SBATCH -n 24
#SBATCH --ntasks-per-node=24
#SBATCH --time=00:50:00
#SBATCH -p plgrid-testing
 
cd $SLURM_SUBMIT_DIR

module purge
module load plgrid/apps/gromacs/2018.8-plumed-2.5.2

~/anaconda3/bin/python ../../main.py --config_file=config_steered.json --start_mode=steered

