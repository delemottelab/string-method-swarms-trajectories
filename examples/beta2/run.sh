#!/usr/bin/env bash
export OMP_NUM_THREADS=2
echo "Make sure gmx is loaded in your bash environment before starting"
cmd="mpiexec -n 3 `which python` -m mpi4py ../../main.py --config_file=config.json"
echo $cmd
$cmd
