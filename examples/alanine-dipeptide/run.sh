#!/usr/bin/env bash
cmd="mpiexec -n 2 `which python` -m mpi4py ../../main.py --config_file=config.json"
echo $cmd
$cmd
