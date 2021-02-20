#!/bin/bash

######################  MODIFY FOR YOUR HPC ###############################

# Submit to the tcb partition
#SBATCH -p tcb

# The name of the job in the queue
#SBATCH -J steered
# wall-clock time given to this job
#SBATCH -t 23:30:00

# Number of nodes and number of MPI processes per node
#SBATCH -N 1 -n 8 
# Request a GPU node and two GPUs (per node)
# Remove if you don't need a GPU
#SBATCH -C gpu --gres=gpu:1 -x gpu04

# Output file names for stdout and stderr
#SBATCH -e steered.err
#SBATCH -o steered.out



######################  MODIFY ###############################
# Add your email below.
# Receive e-mails when your job fails 

#SBATCH --mail-user=anynomous@scilifelab.se --mail-type=FAIL

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
