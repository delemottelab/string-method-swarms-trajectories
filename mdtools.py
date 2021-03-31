import os
import shutil

import gmxapi as gmx
import numpy as np

from stringmethod import logger


def grompp(
    structure_file: str,
    mdp_file: str,
    topology_file: str,
    index_file: str,
    tpr_file: str,
    mdp_output_file: str,
):
    input_files = {
        "-n": index_file,
        "-f": mdp_file,
        "-p": topology_file,
        "-c": structure_file,
    }
    output_files = {"-o": tpr_file, "-po": mdp_output_file}
    prep = gmx.commandline_operation(
        executable="gmx",
        arguments=["grompp"],
        input_files=input_files,
        output_files=output_files,
    )
    prep.run()
    output = str(prep.output.erroroutput.result()).strip()
    if output:
        logger.info("grompp output:\n%s", output)
    return prep


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
):
    mpi_rank = mpi_rank - 1
    cwd = os.path.abspath(os.getcwd())
    os.chdir(output_dir)
    input_files = {"-s": tpr_file}
    if check_point_file is not None:
        input_files["-cpi"] = check_point_file
    # SPC increased state printing to every 5 minutes since swarms are short
    if mdrun_options is None:
        mdrun_options_parse = []
    else:
        mdrun_options_parse = mdrun_options

    # Search for -nt number of threads option in mdrun_options.
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

    md = gmx.commandline_operation(
        executable="gmx",
        arguments=["mdrun", "-cpt", "5"] + mdrun_options_parse,
        input_files=input_files,
        output_files={},
    )
    md.run()
    output = str(md.output.erroroutput.result()).strip()
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
    return md


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

    # Since xvg files can have both @ and # as a head we check
    # the size of the header here.
    # genfromtxt ignores lines starting with #.
    # Also extract comments starting with # here.
    nskip = 0
    comments = []
    founddata = False
    with open(file_name) as f:
        for line in f:

            if line.startswith("#"):
                comments.append(line.rstrip("\n").lstrip("#").rstrip().lstrip())

            if line.startswith(("@", "#")):
                if not founddata:
                    nskip += 1
            else:
                founddata = True
    data = np.genfromtxt(
        file_name, skip_header=nskip, invalid_raise=True, usemask=usemask
    )
    if len(data) == 0:
        raise IOError("No data found in file " + file_name)
    return np.array(data)
