# Performance and parallelism of String Method GMXAPI

## Non-technical Non-rigorous description of HPC cluster architecture and parallelism

A computer cluster is made of very hierarchical elements. All users login to a
login node from which jobs (script or program) are submited to a queue system
(slurm typically) that goberns the priority and resource allocation of jobs.
When the queue system gives the green light the job is run on the *work nodes*.
A **job** in this context is just a bash-script (within a slurm file) that is
executed. In our case the job will be `string-method-gmxapi/main.py` but in other
cases it is just a parallel `gmx_mpi mdrun` command.
A **node**
is just a computer that is connected to other nodes through a high speed
connection that allows several nodes to work together on a single job.
In this sense, an HPC cluster is just a group of computers connected such that they
can work together efficiently.

Nodes themselves are composed of several processors or **CPU**s. CPUs are the
units run
the mathematical operations (boolean alebra, arithmetic etc.) of the job.
The operations themselves are executed by a part of the CPU known as a **core**.
Some CPUs have several cores and in this way they can do several
operations in parallel. In this sense, nodes contain CPUs which contain cores. In
some architectures a node can have several **sockets** which group these CPUs
but for our purpuses the subdivision of nodes into sockets that group the CPUs
is not relevant.

For a job to run in parallel it has to distribute its work into different processes.
The highest level of these parallel processes that are run are MPI-processes or
**MPI-ranks** or MPI-tasks (slurm jargon). MPI-ranks of a given job can be split
over many *CPUs* even if these CPUs are from different nodes. For example a
gromacs simulation can decompose the simulation box into several domains and send the operations
of each domain to a different MPI-rank. You can give a program as many MPI-ranks as *CPUs* it has available.

A single process (which can be an MPIrank or MPI-less program) can have a lower level
of parallelism based on threads. Threads are streams of instructions that a core executes.
Therefore a process can have as many threads as *cores* it has available. In gromacs
multithreading is done in two ways: with OpenMP (`-ntomp`) and "MPIthreads" (`-ntmpi`).
For
our purpuses it is best to specify generically the number of threads with `-nt` and
let gromacs decide which will be OpenMP or MPIthreads.

Many times thread and MPI parallelism is combined. For example, if you ask slurm
for a job with 2 nodes and every node has 2 sockets each with 8 CPUs each and 2
cores per CPU you have available 32 CPUs and 64 cores. With this set up you can
run 1 gmx simulation with 32 MPI-ranks and 64 threads (2 per MPI-rank):
`mpirun -np 32 gmx mdrun -nt 2` CHECK THIS. You can also run 32 gromacs simulations each
with 2 threads: 32 x `gmx mdrun -nt 2`, this is the sort of parallelism done in
the string method.


## Parallelization of String Method in HPC clusters

The string method is well-suited for distributed computing,
where the independent MD simulations run in parallel with very little inter-process communication.
The program implements a master-slave architecture for running multi-node simulations.
One MPI rank, i.e. the master, won't run GROMACS; it will run the main python script and tell all the other MPI ranks what to do.
The other MPI ranks, the slaves, will receive instructions on what GROMACS commands to execute from the master.
When they are finished they'll notify the master and receive new jobs, if there are any.

So if you want to run MD on `N` MPI ranks, then you should start your program with `N+1` MPI processes,
so that there's one for the master. The master is very lightweight and doesn't need many resources to work,
so optimize your nodes and threads to maximize the throughput of the slaves.
If you want to run on `4` CPUs you can for example start `4+1=5` MPI processes.

The method is run in two steps for one iteration:
+ Restrained simulations: parallel restrained simulations are run in
`md/iteration_number/bead_number/restrained/`. Every rank will run one bead.
If the number of MPI-ranks is lower than the number of beads that move (depends if you
fix or not the endpoints) when a simulation finishes, the idle rank will pickup the next
bead until all restrained simulations are done.
+ Swarm simulations: parallel swarm simulations are run in `md/iteration_number/bead_number/s*`.
One swarm is launched from each MPI-rank. Swarms are started from
the first bead and when a rank finishes its simulation picks up the next available swarm
simulation in the queue even if this means picking up a swarm of the next bead. This
is repeated until all swarms have been run.
+ The swarms are analyzed, a new string is calculated and the process starts again.

## Choosing number of MPIranks, number threads, beads and swarm size

The swarm size is the number of short trajectories per point/bead.
The master-slave architecture will work no matter your swarm size and the number of points on the string.
However, since the algorithm needs to finish one step before it moves on to the next,
it's a bonus if all the MD simulations finish at roughly the same time, to avoid idle nodes.
To do so, the number of beads on the string (excluding the fixed endpoints) should be divisible by `N`, the number MPI slave ranks.
If your CPUs have several cores you can give can add to `config.json` the keyword
`"mdrun_options_restrained":["-nt","X"]` and `"mdrun_options_swarms":["-nt","Y"]`
where `X` and `Y` is the number of cores per CPU. In this way you would always be running `N` CPUs
with `N` MPIranks each with  `X` or `Y` threads per simulation depending if you are
in the restrained or swarms step.

If you have many CPUs at your disposal, and you want to have the number of beads
be divisible by the number of MPIranks, you could need to make strings with many
beads which can be hard to converge. In this case, you can choose `N` greater than
the number of beads. This will make some of the MPIranks idle during the
restrained simulations step but you can increase
the number of threads per rank in the restrained portion of the simulation
with `"mdrun_options_restrained":["-nt","X"]`. This would mean that for the restrained
step you will be running less simulations but with more threads and in the swarms
step you will be running more simulations but with less threads.
This is the case
of running the string-method with the slurm file
`examples/start-up/slurm_string_beskow.sh`

The perfect combination of MPI ranks and OMP threads to maximize throughput will
depend on the queue time and how large your system is.
You can change the settings from one submission to another until you find a
good combination.
You should think of how to make sure that all cores are being
used constantly and that it is better to have many simulations running with
few threads than few simulations with many threads.

## Parallelization with GPU nodes

The string method works great on GPUs!! If you have access to nodes with GPUs you
should add one MPI-rank (one simulation)
per GPU. The program assigns internally one GPU to one rank so that GPUs are not
shared between simulations which is inneficient. You can run the string method on
several GPU-nodes each containing several GPUs. Nevertheless, you must make sure
that all nodes have **the same number of GPUs** otherwise due to the implementation
of the code some will be idle.

To run the string-method with gpus just add to `config.json` the keyword
`"gpus_per_node": Z` where `Z` is the number of GPUs per node.
This is the case
of running the string-method with the slurm file
`examples/start-up/slurm_string_tcblab.sh`

## Automatic "-pin on" parameter

When gromacs simulations are being run with threads it is usefull to add the
( "-pin on" )[] parameter for efficiency. When you run the string-method you should
always add the keywords
`"mdrun_options_restrained":["-nt","X"]` and `"mdrun_options_swarms":["-nt","Y"]`
even if `X` and `Y` are 1. This keyword is used to add the mdrun parameters
"-pin on", "-pin-offset" and "-pinstride" internally.
If you try to add "-pin on" to the
`"mdrun_options_restrained"` or `"mdrun_options_swarms"` the simulation will fail.

## Optimization to avoid "tune-PME"

Gromacs by default runs a [tunepme]() calculation in all its runs at the begining
of the simulation to find out the most efficient number of PME vectors in fourier
space and then proceed with this optimimum number. This is a great feature, but
for our purpuses it is a bit wastefull. Restrained simulations and specially swarms
are very short and thus the time spent by gromacs in tuning the PME is big compared
to how show short the simulation is. Nevertheless we can take advantage of the fact
that many times the charge distribution and box size does not depend much on
bead number and does not change much with iterations. We can run one string and find
which are the optimimum number of vectors in fourier space:

```bash
grep "optimal pme" md/1/*/restrained/md.log
```
Once you find which is the best number of PME vectors, add them to `swarms.mdp` and
`restrained.mdp` with the keywords "fourier-nx","fourier-ny" and "fourier-nz"
also you can add "-notunepme" to
`"mdrun_options_restrained"` and `"mdrun_options_swarms"` to `config.json`

If not all the beads have the same number of fourier vectors its best to be conservative
and add the highest number. It is not worth doing this optimization of the number
of vectors changes a lot between beads or if it gives little performance improvement.
It has shown to sometimes give a 10% increase in efficiency.
