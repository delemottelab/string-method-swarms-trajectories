import gmxapi as gmx
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n_ranks = comm.Get_size()


def grompp():
  tprfile = "topol{}.tpr".format(rank)
  prep =  gmx.commandline_operation(executable = "gmx",
                                    arguments = ["grompp"],
                                    input_files= {'-n': 'index.ndx'},
                                    output_files={'-o': tprfile})
  prep.run()
  print("grompp :\n" +str(prep.output.erroroutput.result()))
  return prep

def run(prep):
  # Providing several .tpr files will launch an ensemble simu
  md = gmx.read_tpr([
    "topol{}.tpr".format(r)
    for r in range(n_ranks)
  ]) 
  md = gmx.mdrun(md, label="swarms")
  md.run()
  print("mdrun :\n" +str(prep.output.erroroutput.result()))
  return md

def is_root():
  return rank == 0

if __name__ == "__main__":
  if is_root():
    print("Runing ", n_ranks, " MPI ranks")
    data = dict(init_success=True)
  else:
    print("Waiting on rank ", rank, " for root to finish")
    data = None
  data = comm.bcast(data, root=0) 

  if not data.get('init_success', False):
    print("Init failed")
    System.exit(1)
  print("started on rank ", rank)
  prep = grompp()
  md = run(prep)
  print("finished on rank ", rank)