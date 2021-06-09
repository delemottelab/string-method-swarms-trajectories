import os
import shutil
from subprocess import run, PIPE
from glob import glob
from typing import List

try:
    import gmxapi as gmx
except:
    pass
import numpy as np

from stringmethod import logger


def grompp(
    structure_file: str,
    mdp_file: str,
    topology_file: str,
    index_file: str,
    tpr_file: str,
    mdp_output_file: str,
    use_api: bool = True,
    grompp_options: list = None,
    gmx_executable: str = 'gmx'
):
    input_files = {
        "-n": index_file,
        "-f": mdp_file,
        "-p": topology_file,
        "-c": structure_file,
        "-r": structure_file,
    }
    if grompp_options is None:
        grompp_options = []
    output_files = {"-o": tpr_file, "-po": mdp_output_file}
    if use_api:
        prep = gmx.commandline_operation(
            executable="gmx",
            arguments=["grompp"] + grompp_options,
            input_files=input_files,
            output_files=output_files,
        )
        prep.run()
        output = str(prep.output.erroroutput.result()).strip()
    else:
        infiles = ' '.join([k + ' ' + v for k, v in input_files.items()])
        outfiles = ' '.join([k + ' ' + v for k, v in output_files.items()])
        gmx = "mpiexec -n 1 gmx_mpi" if gmx_executable == "gmx_mpi" else "gmx"
        parse_options =  ' '.join(grompp_options)
        result = run(f"{gmx} grompp {parse_options} {infiles} {outfiles}", stdout=PIPE, stderr=PIPE, shell=True)
        output = result.stderr

    if output:
        logger.info("grompp output:\n%s", output)


def grompp_all(task_list: List[dict]):
    from multiprocessing import Pool
    proc_per_core = int(os.environ["SLURM_CPUS_ON_NODE"]) if "SLURM_CPUS_ON_NODE" in os.environ.keys() else 1
    with Pool(proc_per_core) as p:
        p.map(_grompp, task_list)


def _grompp(args: dict):
    return grompp(**args.update({'gmx_executable': 'gmx_mpi'}))


def _move_all_files(src, dest):
    files = os.listdir(src)
    for f in files:
        shutil.move(os.path.join(src, f), os.path.join(dest, f))


def mdrun(
    mpi_rank: int,
    output_dir: str,
    tpr_file: str,
    check_point_file: str = None,
    mdrun_options: list = None,
    gpus_per_node: int = None,
    plumed_file: str = None,
    use_api: bool = True
):
    mpi_rank = max(mpi_rank - 1,0)
    cwd = os.path.abspath(os.getcwd())
    os.chdir(output_dir)
    input_files = {"-s": tpr_file}
    if check_point_file is not None:
        input_files["-cpi"] = check_point_file
    if plumed_file is not None:
        input_files["-plumed"] = plumed_file
    # SPC increased state printing to every 5 minutes since swarms are short
    if mdrun_options is None:  # TODO
        mdrun_options_parse = []
    else:
        mdrun_options_parse = mdrun_options[:]

    # Search for -nt number of threads option in mdrun_options.
    if mdrun_options is not None:
        for i, o in enumerate(mdrun_options):
            if o == "-nt":
                number_threads = int(mdrun_options[i + 1])
                pin_offset = str(mpi_rank * number_threads)
                mdrun_options_parse += [
                    "-pin",
                    "on",
                    "-pinoffset",
                    f"{pin_offset}",
                    "-pinstride",
                    "1",
                ]
                break

    if gpus_per_node is not None:
        mpi_rank = str(mpi_rank % gpus_per_node)
        mdrun_options_parse += ["-gpu_id", f"{mpi_rank}"]

    if use_api:
        md = gmx.commandline_operation(
            executable="gmx",
            arguments=["mdrun", "-cpt", "5"] + mdrun_options_parse,
            input_files=input_files,
            output_files={},
        )
        md.run()
        output = str(md.output.erroroutput.result()).strip()
    else:
        infiles = ' '.join([k + ' ' + v for k, v in input_files.items()])
        options = ' '.join(mdrun_options_parse)
        result = run(f"gmx mdrun -cpt 5 {infiles} {options}", stdout=PIPE, stderr=PIPE, shell=True)
        output = result.stderr
    if output:
        logger.info("mdrun output:\n%s", output)
    os.chdir(cwd)
    # simulation_input = gmx.read_tpr(tpr_file)
    # md = gmx.mdrun(input=simulation_input)
    # md.run()
    # path = md.output.trajectory.result()
    # path = path[:path.rfind("/") + 1]
    # _move_all_files(path, output_dir)
    # os.removedirs(path)


def mdrun_all(task_list: List[dict]):
    output_dirs = [t['output_dir'] for t in task_list]
    tpr_file = task_list[0]['tpr_file'].split('/')[-1]
    plumed_file = task_list[0]['plumed_file'].split('/')[-1] if task_list[0]['plumed_file'] is not None else None
    input_files = {"-s": tpr_file, "-cpi": ""}
    if plumed_file is not None:
        input_files["-plumed"] = plumed_file
    infiles = ' '.join([k + ' ' + v for k, v in input_files.items()])
    n_cpu = int(os.environ['SLURM_NPROCS'])
    if len(output_dirs) >= n_cpu:
        n_jobs = n_cpu  # one or more batches
    else:
        cpu_per_node = int(os.environ['SLURM_CPUS_ON_NODE'])
        divisors = [x for x in range(1, cpu_per_node+1) if cpu_per_node % x == 0]
        n_jobs = 1
        for div in divisors:
            if div * len(output_dirs) <= n_cpu:
                n_jobs = div * len(output_dirs)
    while output_dirs:
        if plumed_file is not None:
            for ddir in output_dirs[:n_jobs]:
                if 'restrained' not in ddir:
                    try:
                        os.symlink(ddir + '/../restrained/' + plumed_file, ddir + '/' + plumed_file)
                    except:
                        pass
        dirs = ' '.join(output_dirs[:n_jobs])
        del(output_dirs[:n_jobs])
        mpie = "-n {}".format(len(dirs.split())) if len(dirs.split()) < n_jobs else "-n {}".format(n_jobs)
        result = run(f"mpiexec {mpie} gmx_mpi mdrun -cpt 5 -cpo state.cpt {infiles} -multidir {dirs}", stdout=PIPE, stderr=PIPE, shell=True)
        output = result.stderr
        if plumed_file is not None:
            for ddir in dirs.split():
                try:
                    os.symlink(glob(f'{ddir}/colvar*')[0], ddir + '/' + 'colvar')
                except:
                    pass
        if output:
            logger.info("mdrun output:\n%s", output)


def mdrun_one(task: dict):
    output_dir = task['output_dir']
    wdir = os.getcwd()
    os.chdir(output_dir)
    tpr_file = task['tpr_file']
    plumed_file = task['plumed_file']
    input_files = {"-s": tpr_file, "-cpi": ""}
    if plumed_file is not None:
        input_files["-plumed"] = plumed_file
    infiles = ' '.join([k + ' ' + v for k, v in input_files.items()])
    n_cpu = int(os.environ['SLURM_NPROCS'])
    result = run(f"srun -n {n_cpu} gmx_mpi mdrun -cpt 5 -cpo state.cpt {infiles}", stdout=PIPE, stderr=PIPE, shell=True)
    output = result.stderr
    if output:
        logger.info("mdrun output:\n%s", output)
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
    data_lines = [line for line in open(file_name) if not line.startswith(('#', '@'))]
    # then convert them to lists of floats
    data_lines_num = [[float(x) for x in line.split()] for line in data_lines]
    # and remove lines that have inconsistent number of fields (e.g. due to write errors during restarting).
    data = [line for line in data_lines_num if len(line) == len(data_lines_num[0])]
    if len(data) == 0:
        raise IOError("No data found in file " + file_name)
    return np.array(data)
