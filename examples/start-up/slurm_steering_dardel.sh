#!/bin/bash -l

# Include your account in your cluster.
#SBATCH --account=snic2021-3-15
# The name of the job in the queue
#SBATCH --job-name=steered
#SBATCH --partition main

# Output file names for stdout and stderr
#SBATCH --error=slurm_out/steered.err
#SBATCH --output=slurm_out/steered.out

# Add your email below.
# Receive e-mails when your job fails
#SBATCH --mail-user=sergiopc@kth.se
#SBATCH --mail-type=ALL

#SBATCH --time=0:30:00

# Total number of nodes and MPI tasks

######################  MODIFY ###############################

# Number of nodes and number of MPI tasks per node
#SBATCH --nodes=1
# In slurm jargon tasks is like MPI-ranks
#SBATCH --ntasks-per-node=128

# Choose version of gromacs
ml PDC
ml GROMACS/2020.5-cpeCray-21.11
ml Anaconda3/2021.05

# Path to string-method repository
path_string_method=../../../string-method-swarms-trajectories

###################### DO NOT  MODIFY ###############################

cmd=" `which python` ${path_string_method}/stringmethod/main.py --config_file=config_steered.json --start_mode=steered"
echo "Command Run:"
echo $cmd

echo "Started at:"
date
$cmd
echo "Finished at:"
date
