#!/bin/bash

######################  MODIFY FOR YOUR HPC ###############################

# Submit to the tcb partition
#SBATCH --partition=tcb

# The name of the job in the queue
#SBATCH --job-name=steered
# wall-clock time given to this job
#SBATCH --time=23:30:00

# Number of nodes and number of MPI tasks per node
#SBATCH --nodes=1
# In slurm jargon tasks is like MPI-ranks
#SBATCH --ntasks-per-node=8
# Constraint is the "queue" you choose for slurm.
# In this case choose the gpu queue
#SBATCH --constraint=gpu
# gres requests particular generic consumable resources
# in this case 1 gpu per node
#SBATCH --gres=gpu:1

# Output file names for stdout and stderr
#SBATCH --error=steered.err
#SBATCH --output=steered.out

# Add your email below.
# Receive e-mails when your job fails

#SBATCH --mail-user=anynomous@scilifelab.se
#SBATCH --mail-type=FAIL

# Choose version of gromacs
module unload gromacs
module load gromacs/2020.5

# Path to string-method-gmxapi
path_string_method_gmxapi=../../../string-method-gmxapi

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

cmd=" `which python` ${path_string_method_gmxapi}/main.py --config_file=config_steered.json --start_mode=steered"
echo $cmd
$cmd
