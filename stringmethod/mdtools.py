import os
import shutil
from typing import Optional

import gmxapi as gmx

from . import logger


def grompp(structure_file: str, mdp_file: str, topology_file: str, index_file: str, tpr_file: str,
           mdp_output_file: str):
    input_files = {
        '-n': index_file,
        '-f': mdp_file,
        '-p': topology_file,
        '-c': structure_file,
    }
    output_files = {
        '-o': tpr_file,
        '-po': mdp_output_file
    }
    prep = gmx.commandline_operation(executable="gmx",
                                     arguments=["grompp"],
                                     input_files=input_files,
                                     output_files=output_files)
    prep.run()
    output = str(prep.output.erroroutput.result()).strip()
    if output:
        logger.info("grompp output:\n%s", output)
    return prep


def _move_all_files(src, dest):
    files = os.listdir(src)
    for f in files:
        shutil.move(os.path.join(src, f), os.path.join(dest, f))


def mdrun(output_dir: str, tpr_file: str):
    cwd = os.path.abspath(os.getcwd())
    os.chdir(output_dir)

    md = gmx.commandline_operation(executable="gmx",
                                   arguments=["mdrun"],
                                   input_files={'-s': tpr_file},
                                   output_files={})
    md.run()
    output = str(md.output.erroroutput.result()).strip()
    if output:
        logger.info("grompp output:\n%s", output)
    os.chdir(cwd)
    # simulation_input = gmx.read_tpr(tpr_file)
    # md = gmx.mdrun(input=simulation_input)
    # md.run()
    # path = md.output.trajectory.result()
    # path = path[:path.rfind("/") + 1]
    # _move_all_files(path, output_dir)
    # os.removedirs(path)
    return md
