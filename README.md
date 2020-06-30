        .___     .__                         __    __         .__        ___.    
      __| _/____ |  |   ____   _____   _____/  |__/  |_  ____ |  | _____ \_ |__  
     / __ |/ __ \|  | _/ __ \ /     \ /  _ \   __\   __\/ __ \|  | \__  \ | __ \ 
    / /_/ \  ___/|  |_\  ___/|  Y Y  (  <_> )  |  |  | \  ___/|  |__/ __ \| \_\ \ 
    \____ |\___  >____/\___  >__|_|  /\____/|__|  |__|  \___  >____(____  /___  /
         \/    \/          \/      \/                       \/          \/    \/ 
    
    by Oliver Fleetwood and Marko Petrovic 2017-2020.
    https://github.com/delemottelab/string-method-gmxapi

This repository contains an implementation of the string method with swarms of trajectories [[1,2]](#references)
using [GROMACS' python API](http://manual.gromacs.org/current/gmxapi/userguide/usage.html)[[3,4]](#references).


# Using the code

## Python dependencies
 * [gmxapi](http://manual.gromacs.org/current/gmxapi/userguide/usage.html) linked to [GROMACS](http://manual.gromacs.org/). 
 * numpy
 * [mpi4py](https://mpi4py.readthedocs.io/en/stable/index.html)
 * [dataclasses](https://anaconda.org/conda-forge/dataclasses)
 * [typing](https://anaconda.org/anaconda/typing)
 
We plan on automating dependency management with pip or conda.  

## Preparing the files
To launch a simulation you first need to set up a system, configure Collective Variables (CVs; a.k.a reaction coordinates) with GROMACS' pull code, and provide an initial string.
We recommend you to use one of the [examples below](#examples) as a template. 


### Molecular Dynamics Properties (MDP) files
You need two MDP files:

**restrained.mdp**

Contains the settings to run a short equilibration with pull code restraints before launching the swarms. 
All required pull code parameters except for ```pull-code-init``` should be set in this file. 

**swarms.mdp** 

Contains the settings to run the unrestrained swarm simulations. 
Note that you still need to define the pull code properties in this file to print the CV values to a xvg-file, but no force should be applied.
This is acheived by seeting ```pull-coord-k=0```.

**Pull code MDP example**
```
pull = yes      
pull-ngroups = 2                 
pull-group1-name = residue_1 ; name of groups defined in the index file 
pull-group2-name = residue_2

; Define the first collective variable (CV)
pull-ncoords = 1
pull-coord1-geometry = distance
pull-coord1-groups = 1 2 ; Center of mass distnace between the two groups
pull-coord1-k = 0 ; strength of harmonic potential. Set to a high value in restrained.mdp and to 0 in swarms.mdp
; .... Define more CVs below

; Handle output
pull-print-components = no ; output pull coordinates
pull-nstxout = 50000 ; Step interval to output the coordinate values to the pullx.xvg. Should match the 'nstepsä property
pull-nstfout = 0
````

### Topology
You need to have a valid topology file called **topol.top** and an index file called **index.ndx**. 
The index file should define all groups used by the pull code. 

### Input string
#### String files
You define your initial pathway in a [numpy .txt](https://numpy.org/doc/stable/reference/generated/numpy.loadtxt.html) format called ```string0.txt```.
Every row in your file defines the CV coordinates for a point on the string. 
The first column refers to the first CV/pull coordinate etc.

#### Input coordinates
For every point on your string your need a snapshot with all atom coordinates called **confout.gro**. 
Create one directory per point and put the corresponding snaphot in that directory according to the layout below.
You don't need to provide .gro-files for the first and last point on the string if your endpoints are fixed, which is the default. 

Note that these snapshots should be well-equilibrated and be close to the coordinates defined in **string0.txt**. 
This can for example be acheived by running steered-MD along your initial string between two endpoints.
The script will only equilibrate the system according to ```nsteps``` in **restrained.mdp**. 

### File organization
We recommend you to organize your simulation files according to the following default layout:
``` 
simulation_directory
├── config.json
├── md
│   └── 0
│       ├── 0 
│       │   └── restrained
│       │       └── confout.gro
│       ├── 1
│       │   └── restrained
│       │       └── confout.gro
│       ├── 2
│       │   └── restrained
│       │       └── confout.gro
        ...        
├── mdp
│   ├── restrained.mdp
│   └── swarms.mdp
├── strings
│   ├── rescale_string.py
│   ├── string0-scaled.txt
│   └── string0.txt
└── topology
    ├── end.gro
    ├── index.ndx
    ├── start.gro
    ├── topol.top

```
As the program progresses it will create new directories in the **md** directory, one new directory for every string iterations.
At the end of every iteration, it will output new string coordinates **strings/string1.txt**, **strings/string2.txt**", etc. 

We know it requires some effort to get started. We're working on a script which helps you with CV selection and string preparation.

### config.json (optional)
This JSON file will be loaded as a `` Config`` object defined in **stringmethod/config.py**. 
You can override parameters such as the number of trajectories in a swarm, the maximum number of iterations and if the endpoints should be fixed.
You can also change the location of the input/output directories.

## Running a string simulation
The main entry point to start a program is via ```main.py``` with the optional parameters  ```iteration```, ```start_mode``` and ```config_file```.
You can also write your own python wrapper and import the stringmethod module. 
The program can run either in an MPI environment, automatically distributing the work to multiple nodes, or on a single machine.


### Running on a single machine
```bash
python main.py --config_file=config.json
```
Here we've also provided an optional config file

### Running with MPI in a HPC environment
Assume that you want to run in parallel with 4 MPI rank and that you have 128 CPUs at your disposal. 
To achieve good performance we need to tell GROMACS to use ```128/4=32``` threads per rank and tell our MPI provider to start ```4+1=5``` MPI processes. 
The reason is that one process acts
as master and delegates simulation jobs to the other nodes. Note that this might change in future versions.

```bash 
export OMP_NUM_THREADS=32
mpiexec -n 5 -m mpi4py main.py 
```

# Examples
In the **examples** directory you'll find complete sets of input files for running a simulation. 
These can be used for testing your python environment or as a template to set up your own simulation.

## Alanine dipeptide in vaccuum
We analyse the transition between two metastable states of alanine dipeptide using the two dihedral angles ϕ and Ψ. 
This simulation can run a regular laptop.

## beta2: G protein-coupled receptor (GPCR) activation
We study the beta2 adrenergic receptor in its native apo state using five C-alpha distances as CVs. 
Read [our paper [2]](https://doi.org/10.1021/acs.biochem.9b00842) for more details.
This simulation takes time. To obtain useful results you need a desktop with a good GPU or an HPC environment.

# References
1. Pan, Albert C., Deniz Sezer, and Benoît Roux. "Finding transition pathways using the string method with swarms of trajectories." The journal of physical chemistry B 112.11 (2008): 3432-3440.
2. Fleetwood, Oliver, et al. "Energy Landscapes Reveal Agonist Control of G Protein-Coupled Receptor Activation via Microswitches." Biochemistry 59.7 (2020): 880-891.
3. Abraham, Mark James, et al. "GROMACS: High performance molecular simulations through multi-level parallelism from laptops to supercomputers." SoftwareX 1 (2015): 19-25.
4. Irrgang, M. Eric, Jennifer M. Hays, and Peter M. Kasson. "gmxapi: a high-level interface for advanced control and extension of molecular dynamics simulations." Bioinformatics 34.22 (2018): 3945-3947.