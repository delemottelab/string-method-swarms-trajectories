#!/bin/bash

# Include your allocation number
#SBATCH -A XXXX-XX-XX

# The name of the job in the queue
#SBATCH -J adpString

# Total number of nodes
#SBATCH --nodes 2

# length in hours
#SBATCH -t 00:20:59

# Receive e-mails when your job starts and ends
#SBATCH --mail-type=FAIL

# Output file names for stdout and stderr
#SBATCH -e error.log
#SBATCH -o output.log

echo "Starting beta2 string simulation on the Beskow super computer"

__conda_setup="$('/pdc/vol/anaconda/2019.03/py37/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/pdc/vol/anaconda/2019.03/py37/etc/profile.d/conda.sh" ]; then
        . "/pdc/vol/anaconda/2019.03/py37/etc/profile.d/conda.sh"
    else
       export PATH="/pdc/vol/anaconda/2019.03/py37/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

#module swap PrgEnv-cray PrgEnv-gnu
module load gromacs/2020.1


cmd="conda activate /cfs/klemming/nobackup/o/oliverfl/py37"
echo $cmd
$cmd
#Launch 8 jobs per node -> 32/8 = 4 threads per mdrun and 16 MPI ranks (parallell MD runs)
export OMP_NUM_THREADS=4
# Note how we start one more MPI process than we need. This is to have one process delegating jobs to the other
cmd="mpiexec -n 17 `which python` -m mpi4py ../../main.py --config_file=config.json"
echo $cmd
$cmd
