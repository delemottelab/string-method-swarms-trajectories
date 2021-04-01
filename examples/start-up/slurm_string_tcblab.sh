#!/bin/bash -l

######################  MODIFY FOR YOUR HPC ###############################
# Include your partition in your cluster.
#SBATCH --partition=tcb
# The name of the job in the queue
#SBATCH --job-name=my_string_simulation

# Output file names for stdout and stderr
#SBATCH --error=string-%j-%A_%a.err
#SBATCH --output=string-%j-%A_%a.out

######################  MODIFY ###############################
# Add your email below.
# Receive e-mails when your job fails
#SBATCH --mail-user=anynomous@scilifelab.se
#SBATCH --mail-type=FAIL

# Time should slightly greater than the time for one full iteration
# if you want to do one iteration per slurm job (recomended).
# If you can allocate big chunks of time in your cluster you can put the time
# of N-iterations and add this number of interations in the variable
# `max_iteration=$((($iteration+1)))` bellow.
#SBATCH --time=23:00:00

# Number of nodes and number of MPI processes per node
#SBATCH --nodes=3
# In slurm jargon tasks is like MPI-ranks
#SBATCH --ntasks-per-node=32
# Constraint is the "queue" you choose for slurm.
# In this case choose the gpu queue
#SBATCH --constraint=gpu
# gres requests particular generic consumable resources
# in this case 1 gpu per node
#SBATCH --gres=gpu:2

# Choose version of gromacs
module unload gromacs
module load gromacs/2020.5

# Path to string-method-gmxapi
path_string_method_gmxapi=../../../string-method-gmxapi/

# Path to anaconda3 instalation with string_method environment
my_conda_env=/nethome/sperez/bin/anaconda3

######################  DON'T MODIFY ###############################
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
var=$("${my_conda_env}/bin/conda" 'shell.bash' 'hook' 2> /dev/null)
__conda_setup=$var
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$my_conda_env/etc/profile.d/conda.sh" ]; then
        . "$my_conda_env/etc/profile.d/conda.sh"
    else
        export PATH="$my_conda_env/bin/$PATH"
    fi
fi
unset __conda_setup
conda activate string_method

# This code finds the last iteration done a feeds it to the string-method so it doesn't have to check every directory in md/

iteration=$(ls -vd md/*|tail -n 1|sed  "s:md/\([0-9]*\):\1:")

######################  MODIFY ###############################

# This code modifies config.json such that this slurm job only does one iteration. This is a way of sending many small jobs rather
# than one big one that takes longer to get through the queue. If you would rather have one long job, increase iterations per job
# or errase these lines and add a high max_iteration to config.json. If you do one iteration per slurm job it is important that the
# allocated time of the job is not longer than the time of a full iteration.

# If you want more than one iterations_per_job just modify bellow
iterations_per_job=1
max_iteration=$((($iteration+$iterations_per_job)))
sed -i "s/\"max_iterations\": [0-9]*/\"max_iterations\": $max_iteration/" config.json

# This number of parallel processes and number of nodes has been found to work well for 60-80k atoms in beskow (@DelemotteLab).
# You can of course adapt it to your HPC environment following the guidelines of the main README.md
iteration=$((($iteration-1)))
processes=$((($SLURM_NTASKS+1)))
processes=7
cmd="time srun -n $processes `which python`  ${path_string_method_gmxapi}/main.py --config_file=config.json --iteration=$iteration"
echo "Running on $SLURM_JOB_NODELIST , with $processes processes"
echo "GPU ids"
echo "$CUDA_VISIBLE_DEVICES"
echo "Command Run:"
echo $cmd
echo "Started at:"
date
$cmd
echo "Finished at:"
date
