#!/usr/bin/env bash
export OMP_NUM_THREADS=2
echo "Make sure gmx is loaded in your bash environment before starting"
cmd="python ../../main.py --config_file=config.json --start_mode=steered"
echo $cmd
$cmd
