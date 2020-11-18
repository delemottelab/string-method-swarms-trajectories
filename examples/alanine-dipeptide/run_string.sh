#!/usr/bin/env bash
export OMP_NUM_THREADS=1
echo "Make sure gmx is loaded in your bash environment before starting"
cmd="mpiexec -n 5 `which python` -m mpi4py ../../main.py --config_file=config.json"
echo $cmd
$cmd
