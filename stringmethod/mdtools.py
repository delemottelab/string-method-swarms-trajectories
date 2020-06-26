from typing import Optional

import gmxapi as gmx

from . import mpi, logger



def grompp(structure_file: str, mdp_file: str, topology_file: str, index_file: str, tpr_file: str):
    input_files = {
        '-n': index_file,
        '-f': mdp_file,
        '-p': topology_file,
        '-c': structure_file,
    }
    output_files = {'-o': tpr_file}
    prep = gmx.commandline_operation(executable="gmx",
                                     arguments=["grompp"],
                                     input_files=input_files,
                                     output_files=output_files)
    prep.run()
    if mpi.is_root:
        logger.info("grompp output:\n%s", str(prep.output.erroroutput.result()))
    return prep


def mdrun(tpr_files: list, mdp_properties: Optional[dict] = None):
    # Providing several .tpr files will launch an ensemble simu.
    # No need to control MPI in python here, gmxapi does that for you
    simulation_input = gmx.read_tpr(tpr_files)
    modified_input = gmx.modify_input(input=simulation_input, parameters=mdp_properties)
    md = gmx.mdrun(input=modified_input)
    md.run()
    if mpi.is_root:
        logger.info("mdrun output:\n%s", str(md.output.erroroutput.result()))
    return md
