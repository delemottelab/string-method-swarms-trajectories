# Performance and parallelism of String Method GMXAPI

## Non-technical, non-rigorous description of HPC cluster architecture and parallelism
If the reader is familiar with HPC architecture and the parallelization of gromacs
this section can be skiped.

A computer cluster is made of hierarchical elements.
A **node**
is just a computer that is connected to other nodes through a high speed
connection that allows several nodes to work together on a single job.
In this sense, an HPC cluster is just a group of computers connected such that they
can work together efficiently.

Nodes themselves are composed of several **cores**. Cores are the
processing units that run
the program instructions (boolean algebra, arithmetic, memory operations etc.)
of the job.
Most computers have several cores and in this way they can do several
instructions in parallel.
In some architectures a node can have several **sockets** which group cores giving them
a shared locality and memory.
For our purposes the subdivision of nodes into sockets that contain cores
is not relevant.


Users conect to a **login node** from which jobs (script or program) are submited
to a job scheduler
(slurm typically) that goberns the priority and resource allocation of jobs.
The job scheduler allocates the resources and when they become available it runs
the job in the **work nodes**.
A **job** in this context is just a bash-script (within a slurm file) that is
executed. This script runs in our case `string-method-gmxapi/main.py` but in other
cases it is just a parallel `gmx_mpi mdrun` command.

For a job to run in parallel it has to distribute its work into different processes.
The highest level of these parallel processes are MPI-processes or
MPI-ranks or MPI-tasks or just **rank**. Ranks of a given job can be distributed
over many *cores* even if these cores are from different nodes. For example a
simulation can decompose the simulation box into several domains and send the operations
of each domain to a different MPI-rank. You can find more information on *Domain Decomposition*
[here](https://manual.gromacs.org/documentation/current/reference-manual/algorithms/parallelization-domain-decomp.html).
In most cases, it is best to give a program as many ranks as *cores* are available.

A single process (which can be a rank  or rank-less program) can have a lower level
of parallelism based on threads. Threads are streams of instructions that a core executes.
In this way a rank can have several threads running its instructions in parallel.

Some cores can execute several threads at the same time, this is know as SMT or
hyperthreading. In gromacs, which generally is compiled with the right
[SIMD](https://manual.gromacs.org/documentation/current/user-guide/mdrun-performance.html#intra-core-parallelization-via-simd-sse-avx-etc),
the use of the core is very efficient and using hyperthreading/SMT can be counter productive.
For this reason, we will use no more threads for a program than cores it has available.

In gromacs
thread parallelism is done in two ways: with OpenMP (`-ntomp`) and/or "MPI-threads" (`-ntmpi`).
For
our purpuses it is best to specify generically the number of threads with `-nt` and
let gromacs decide how many will be OpenMP or MPI-threads. These keywords tell gromacs
the number of threads *per rank* to use or in total if the program has a single
rank. It is worth noting that
ranks and OpenMP-threads can be combined or if you run on a single rank
you can combine MPI-threads and OpenMP-threads.

For example, if you ask slurm
for a job with 2 nodes and every node has 2 sockets each with 8 cores each you have available 32 cores
on which you can run a combination of 32 threads and/or ranks. With this set-up you can
run 1 gmx simulation with 32 ranks each with 1 thread per rank:
`mpirun -np 32 gmx mdrun -ntomp 1`. Or 1 gmx simulation with 16 ranks and
 2 threads per rank: `mpirun -np 16 gmx mdrun -ntomp 2`. You can also run 2 gromacs simulations each
with 16 threads: 2 x `gmx mdrun -nt 16`. With the `-nt` keyword gromacs decides
how many threads will be MPI-threads and how many OMPthreads.

If you want to know the hardware specifications of the nodes you can use the
`sinfo` slurm command. The "S:C:T" column will tell you the number of sockets,
sockets per core and threads
per core in a node. The "gres" column will tell you if you have GPUs available
in the node.

The term CPU which is used a lot can be slightly confusing.
CPU refers to a processor generically.
In this sense a core is a CPU but also a processor containing several cores is also
a CPU. In slurm the term CPU is equivalent to core unless cores can
run more than one thread (SMT enabled) in which case CPU is equivalent to thread.
Since this term is somewhat context dependent we shall not use it further.

## Parallelization of String Method in HPC clusters

The string method is well-suited for distributed computing,
where the independent MD simulations run in parallel with very little inter-process communication.
The program implements a master-slave architecture for running multi-node simulations.
One MPI-rank, i.e. the master, won't run GROMACS; it will run the main python script and tell all the other ranks what to do.
The other ranks, the slaves, will receive instructions on what GROMACS commands to execute from the master.
When they are finished they'll notify the master and receive new jobs, if there are any.

So if you want to run MD on `N` ranks, then you should start your program with `N+1` MPI-ranks,
so that there's one for the master. The master is very lightweight and doesn't need many resources to work,
so optimize your nodes and threads to maximize the throughput of the slaves.
If you want to run on `4` cores you can for example start `4+1=5` ranks.

The method is run in two steps for one iteration:
1. Restrained simulations: parallel restrained simulations are run in
`md/iteration_number/bead_number/restrained/`. Every rank will run one bead.
If the number of ranks is lower than the number of beads that move (depends if you
fix or not the endpoints) when a simulation finishes, the idle rank will pickup the next
bead until all restrained simulations are done.
2. Swarm simulations: parallel swarm simulations are run in `md/iteration_number/bead_number/s*`.
One swarm is launched for each rank. Swarms are started from
the first bead and when a rank finishes its simulation, it picks up the next available swarm
simulation in the queue even if this means picking up a swarm of the next bead. This
is repeated until all swarms have been run.
3. The swarms are analyzed, a new string is calculated and the process starts again.


## Choosing number of MPI-ranks, number threads, beads and swarm size

The swarm size is the number of short trajectories per point/bead.
The master-slave architecture will work no matter your swarm size and the number of points on the string.
However, since the algorithm needs to finish one step before it moves on to the next,
it's a bonus if all the MD simulations finish at roughly the same time, to avoid idle nodes.
To do so, the number of beads on the string (excluding the fixed endpoints) should be divisible by `N`, the number MPI slave ranks.

If you have many cores at your disposal, and you want to have the number of beads
be divisible by the number of ranks, you could need to make strings with many
beads which can be hard to converge. To use many cores and not have a string with
many beads, you can choose the number of ranks `N` greater than
the number of beads. This will make some of the ranks idle during the
restrained simulations step making some of your cores idle too. To use these idle
cores you can increase
the number of threads per rank in the restrained portion of the simulation
with `"mdrun_options_restrained":["-nt","X"]`. In this way, you will have simulations
equal to the number of beads during the restrained step but with several threads per
simulation. In the swarm step however, all ranks will be used and each rank will use
one thread which maximizes efficiency.
This would mean that for the restrained
step you will be running less simulations but with more threads and in the swarms
step you will be running more simulations but with less threads.
This is the case
of running the string-method with the slurm file
`examples/start-up/slurm_string_beskow.sh`

The perfect combination of ranks and OMP threads to maximize throughput will
depend on the queue time and how large your system is.
You can change the settings from one iteration to another until you find a
good combination.
You should think of how to make sure that all cores are being
used constantly and that it is better to have many simulations running with
few threads than few simulations with many threads.

## Parallelization with GPU nodes

The string method works great on GPUs! If you have access to nodes with GPUs you
should add one rank (one simulation)
per GPU. The program assigns internally one GPU to one rank so that GPUs are not
shared between simulations which is inneficient. You can run the string method on
several GPU-nodes each containing several GPUs. Nevertheless, you must make sure
that all nodes have **the same number of GPUs** otherwise due to the implementation
of the code some will be idle.

To run the string-method with gpus just add to `config.json` the keyword
`"gpus_per_node": Z` where `Z` is the number of GPUs per node.

## Automatic "-pin on" parameter

When gromacs simulations are being run with threads it is usefull to add the
 "-pin on" parameter for efficiency.
 When you run the string-method you should
always add the keywords
`"mdrun_options_restrained":["-nt","X"]` and `"mdrun_options_swarms":["-nt","Y"]`
even if `X` and `Y` are 1. This keyword is used to add the mdrun parameters
"-pin on", "-pin-offset" and "-pinstride" internally.
If you try to add "-pin on" to the
`"mdrun_options_restrained"` or `"mdrun_options_swarms"` the simulation will fail.

## Optimization to avoid "tune-PME"

Gromacs by default runs a tunepme calculation in all its runs at the begining
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
and also add "-notunepme" to
`"mdrun_options_restrained"` and `"mdrun_options_swarms"` to `config.json`

If not all the beads have the same number of fourier vectors its best to be conservative
and add the highest number. It is not worth doing this optimization if the number
of vectors changes a lot between beads or if it gives little performance improvement.
It has shown to sometimes give a 10% increase in efficiency. As with all optimizations
check that the gain compensates the potential small loss in accuracy.

## Acknoledgements
The authors would like to acknowledge Szilárd Páll and Artem Zhmurov for the
comments and insightfull feedback.
