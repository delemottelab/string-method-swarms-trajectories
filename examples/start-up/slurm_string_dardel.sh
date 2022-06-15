#!/bin/bash -l

# Include your account in your cluster.
#SBATCH --account=snic2021-3-15
# The name of the job in the queue
#SBATCH --job-name=string
#SBATCH --partition main

# Output file names for stdout and stderr
#SBATCH --error=slurm_out/string-%J_%a.err
#SBATCH --output=slurm_out/string-%J_%a.out

# Add your email below.
# Receive e-mails when your job fails
#SBATCH --mail-user=sergiopc@kth.se
#SBATCH --mail-type=ALL

# Time should slightly greater than the time for one full iteration
# if you want to do one iteration per slurm job (recomended).
# If you can allocate big chunks of time in your cluster you can put the time
# of N-iterations and add this number of interations in the variable
# `max_iteration=$((($iteration+1)))` bellow.
#SBATCH --time=0:30:00

# Total number of nodes and MPI tasks
# This number of nodes and tasks has been found to work well for 60-80k atoms in beskow (@DelemotteLab).
# You can of course adapt it to your HPC environment following the guidelines of the main README.md

# Number of nodes and number of MPI tasks per node
#SBATCH --nodes=2
# In slurm jargon tasks is like MPI-ranks
#SBATCH --ntasks-per-node=128

# Choose version of gromacs
ml PDC
ml GROMACS/2020.5-cpeCray-21.11
ml Anaconda3/2021.05

# Path to string-method repostory
path_string_method=../../../string-method-swarms-trajectories

# This code finds the last iteration done a feeds it to the string-method so
# it doesn't have to check every directory in md/

iteration=$(ls -vd strings/string[0-9]*.txt|tail -n 1| sed  "s:strings/string\([0-9]*\).txt:\1:")

######################  MODIFY ###############################

# This code modifies config.json such that this slurm job only does one iteration.
# This is a way of sending many small jobs rather
# than one big one that takes longer to get through the queue.
# If you would rather have one long job, increase iterations per job
# or errase these lines and add a high max_iteration to config.json.
# If you do one iteration per slurm job it is important that the
# allocated time of the job is not longer than the time of a full iteration.

# If you want more than one iterations_per_job just modify bellow
iterations_per_job=1
max_iteration=$((($iteration+$iterations_per_job)))
sed -i "s/\"max_iterations\": [0-9]*/\"max_iterations\": $max_iteration/" config.json

# This number of parallel processes and number of nodes has been found to
# work well for 60-80k atoms in beskow (@DelemotteLab).
# You can of course adapt it to your HPC environment following the guidelines
# of the main README.md
cmd="`which python`  ${path_string_method}/stringmethod/main.py --config_file=config.json"
echo "Command Run:"
echo $cmd

echo "Started at:"
date
$cmd
echo "Finished at:"
date
