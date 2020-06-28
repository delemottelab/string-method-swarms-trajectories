#!/usr/bin/env bash
echo "Make sure gmx is loaded in your bash environment before starting"
cmd="mpiexec -n 4 `which python` -m mpi4py ../../main.py --config_file=config.json"
echo $cmd
$cmd
