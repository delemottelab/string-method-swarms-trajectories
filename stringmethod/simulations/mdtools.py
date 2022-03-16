import os
import shutil
import sys
from glob import glob
from subprocess import PIPE, run
from typing import List

import numpy as np

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
sys.path.append(parent)


from stringmethod import logger


def grompp_one(args: dict):
    input_files = {
        "-n": args["index_file"],
        "-f": args["mdp_file"],
        "-p": args["topology_file"],
        "-c": args["structure_file"],
        "-r": args["structure_file"],
    }
    grompp_options = (
        args["grompp_options"] if args["grompp_options"] is not None else []
    )
    output_files = {"-o": args["tpr_file"], "-po": args["mdp_output_file"]}
    infiles = " ".join([k + " " + v for k, v in input_files.items()])
    outfiles = " ".join([k + " " + v for k, v in output_files.items()])
    if shutil.which("gmx_seq") is not None:
        gmx = "gmx_seq"
    elif shutil.which("gmx") is not None:
        gmx = "gmx"
    else:
        gmx = "srun -n 1 gmx_mpi"
        logger.warning(
            "The program is calling many times `srun -n 1 gmx_mpi grompp` in a short period of time. So much communication with the slurm server can cause problems. Please try to have an accesible gmx binary that doesn't require srun."
        )
    parse_options = " ".join(grompp_options)
    command = f"{gmx} grompp {parse_options} {infiles} {outfiles}"
    logger.info(f"Running command {command}")
    result = run(
        command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
    )
    output = result.stderr

    if output:
        logger.info("grompp output:\n%s", output.decode())


def grompp_all(task_list: List[dict]):
    from multiprocessing import Pool

    proc_per_core = (
        int(os.environ["SLURM_CPUS_ON_NODE"])
        if "SLURM_CPUS_ON_NODE" in os.environ.keys()
        else 1
    )
    with Pool(proc_per_core) as p:
        p.map(grompp_one, task_list)


def _move_all_files(src, dest):
    files = os.listdir(src)
    for f in files:
        shutil.move(os.path.join(src, f), os.path.join(dest, f))


def mdrun_all(task_list: List[dict]):
    output_dirs = [t["output_dir"] for t in task_list]
    tpr_file = task_list[0]["tpr_file"].split("/")[-1]
    mdrun_options = task_list[0]["mdrun_options"]
    plumed_file = (
        task_list[0]["plumed_file"].split("/")[-1]
        if task_list[0]["plumed_file"] is not None
        else None
    )
    input_files = {"-s": tpr_file}
    if plumed_file is not None:
        input_files["-plumed"] = plumed_file
    mdrun_options_parsed = mdrun_options[:] if mdrun_options is not None else []
    infiles = " ".join([k + " " + v for k, v in input_files.items()])
    mdrun_options_parsed = " ".join(mdrun_options_parsed)
    n_cpu = int(os.environ["SLURM_NPROCS"])
    if len(output_dirs) >= n_cpu:
        n_jobs = n_cpu  # one or more batches
    else:
        cpu_per_node = int(os.environ["SLURM_CPUS_ON_NODE"])
        divisors = [x for x in range(1, cpu_per_node + 1) if cpu_per_node % x == 0]
        n_jobs = 1
        for div in divisors:
            if div * len(output_dirs) <= n_cpu:
                n_jobs = div * len(output_dirs)
    while output_dirs:
        if plumed_file is not None:
            for ddir in output_dirs[:n_jobs]:
                if "restrained" not in ddir:
                    try:
                        os.symlink(
                            ddir + "/../restrained/" + plumed_file,
                            ddir + "/" + plumed_file,
                        )
                    except:
                        pass
        dirs = " ".join(output_dirs[:n_jobs])
        del output_dirs[:n_jobs]
        mpie = f"-n {n_cpu}"
        logger.info(f"Running {n_jobs} simulation with {n_cpu} cpus.")
        command = f"srun {mpie} gmx_mpi mdrun -cpo state.cpt {infiles} -multidir {dirs} {mdrun_options_parsed}"
        logger.info(f"Running command {command}")
        result = run(
            command,
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
        )
        output = result.stderr
        if plumed_file is not None:
            for ddir in dirs.split():
                try:
                    os.symlink(glob(f"{ddir}/colvar*")[0], ddir + "/" + "colvar")
                except:
                    pass
        if output:
            logger.info("mdrun output:\n%s", output.decode())


def mdrun_one(task: dict):
    output_dir = task["output_dir"]
    wdir = os.getcwd()
    os.chdir(output_dir)
    tpr_file = task["tpr_file"]
    plumed_file = task["plumed_file"]
    check_point_file = task["check_point_file"]
    input_files = {"-s": tpr_file, "-cpi": ""}
    mdrun_options_parsed = (
        task["mdrun_options"][:] if task["mdrun_options"] is not None else []
    )
    if check_point_file is not None:
        input_files["-cpi"] = check_point_file
    if plumed_file is not None:
        input_files["-plumed"] = plumed_file
    infiles = " ".join([k + " " + v for k, v in input_files.items()])
    mdrun_options_parsed = " ".join(mdrun_options_parsed)
    n_cpu = int(os.environ["SLURM_NPROCS"])
    logger.info(f"Running one simulation with {n_cpu} cpus.")
    command = f"srun -n {n_cpu} gmx_mpi mdrun -cpt 5 -cpo state.cpt {infiles} {mdrun_options_parsed}"
    logger.info(f"Running command {command}")
    result = run(
        command,
        stdout=PIPE,
        stderr=PIPE,
        shell=True,
    )
    output = result.stderr
    if output:
        logger.info("mdrun output:\n%s", output.decode())
    os.chdir(wdir)


def load_xvg(file_name: str, usemask: bool = False) -> np.array:
    """
    Originally from https://github.com/vivecalindahl/awh-use-case/blob/master/scripts/analysis/read_write.py
    if file does not exist, exit
    if exists, check number of commentlines to skip
    extract data and return
    :param file_name:
    :param usemask:
    :return:
    """

    if not os.path.exists(file_name):
        raise FileNotFoundError("WARNING: file " + file_name + " not found.")

    # Since xvg/colvar files can have both @ and # as a head, we only read lines that don't start with these chars
    data_lines = [line for line in open(file_name) if not line.startswith(("#", "@"))]
    # then convert them to lists of floats
    data_lines_num = [[float(x) for x in line.split()] for line in data_lines]
    # and remove lines that have inconsistent number of fields (e.g. due to write errors during restarting).
    data = [line for line in data_lines_num if len(line) == len(data_lines_num[0])]
    if len(data) == 0:
        raise IOError("No data found in file " + file_name)
    return np.array(data)
