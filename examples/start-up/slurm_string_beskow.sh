#!/bin/bash -l

# Include your allocation in your cluster.
#SBATCH -A 2020-3-28
# Name your job
#SBATCH -J my_string_simulation

# Output file names for stdout and stderr
#SBATCH -e string-%j-%A_%a.err -o string-%j-%A_%a.out

######################  MODIFY ###############################
# Add your email below.
# Receive e-mails when your job fails 

#SBATCH --mail-user=sergiopc@kth.se --mail-type=ALL

# If you want to do one iteration per slurm job (recomended) the 
# time should greater than the time for one full iteration.

#SBATCH -t 04:00:00

# Total number of nodes and MPI tasks
# This number of nodes and tasks has been found to work well for 60-80k atoms in beskow (@DelemotteLab).
# You can of course adapt it to your HPC environment following the guidelines of the main README.md

#SBATCH --nodes 8 --ntasks-per-node=32 

# Choose version of gromacs
module unload gromacs
module load gromacs/2020.5

# Path to string-method-gmxapi
path_string_method_gmxapi=../../../string-method-gmxapi

# Path to anaconda3 instalation with string_method environment
my_conda_env=/cfs/klemming/nobackup/s/sergiopc/anaconda3


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

max_iteration=$((($iteration+1)))
sed -i "s/\"max_iterations\": [0-9]*/\"max_iterations\": $max_iteration/" config.json

# This number of parallel processes and number of nodes has been found to work well for 60-80k atoms in beskow (@DelemotteLab).
# You can of course adapt it to your HPC environment following the guidelines of the main README.md
iteration=$((($iteration-1)))
cmd="mpiexec -n 257 `which python`  ${path_string_method_gmxapi}/main.py --config_file=config.json --iteration=$iteration"
echo "Command Run:"
echo $cmd

echo "Started at:"
date
$cmd
echo "Finished at:"
date
