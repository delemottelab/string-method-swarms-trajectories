# String Simulation Start-Up

This is a small tutorial on how to set up simple (but powerfull) string-method
simulations from scratch. The slurm-files are adapted the supercomputing
environments of the @DelemotteLab but should be adaptable to any other HPC
centers. Please checkout [PERFORMANCE.md](../../PERFORMANCE.md) for details on
performance and how to run the simulations in parallel and/or with GPUs.

The files are an example of string-simulation of the beta2 adrenergic receptor.

## Ingredients

To run string-method simulations you will need:

+ A starting state configuration: `topology/start.gro`.
+ A end state configuration (this one you don't strickly need):
`topology/end.gro`.
+ A topology file with gmx topology: `topology/topol.top`.
+ A gmx index file: `topology/index0.ndx`. Note it's index0.ndx.
+ An idea of which distances between groups of atom/s could be good cvs for the
string. i. e. "The distance between the centers of mass of resid 1 and resid 14"
and/or "The distance between CB atoms of resid 131 and resid 378".

You might want to use but not need strickly:

+ An anaconda installation.
+ If you have your own initial string obtained from other simulations or obtained
your imagination:
  + A txt file with the string with `np.savetxt` format and shape
(ncvs, nbeads): `strings/string0.txt`.
  + The starting beads of the initial string: `md/0/0/restrained/confout.gro`,
`md/0/1/restrained/confout.gro`, ...

If you have the mentioned files,
put these files in the directories specified above. The initial string and bead
configurations can also be generated from steering simulations.

## Geting started

First of all you need to install some python libraries. The most convenient way
to do this is with anaconda3. Gromacs must be available on the path and to
install gmxapi the environment variable `GMXTOOLCHAINDIR` must be set. gmxapi
can be tricky to install sometimes, but their developers are very nice and
can answer your issues in their [github](https://github.com/kassonlab/gmxapi/issues).
Getting nglview to work can be tricky too but it is not necessary to use, it
just to visualize things in the notebook. You can always use alternitavelly some
other visualization software.

```bash
# SUFFIX are the typical suffixes of gmx "_d", "_mpi" or "".
export GMXTOOLCHAINDIR=/path/to/gromacs/share/cmake/gromacs${SUFFIX}
conda env create -f environment.yml
conda activate string_method
```

This command will create an environment called `string_method` with all the
necessary libraries to prepare and run string-method simulations.

Within this environment, open the jupyter-notebook  `input_maker.ipynb`.
Using this notebook you will be able to prepare the files for the steering
simulation and/or the string-method. You will also be able to visualize your
initial `string0.txt`.

## Running Steering

If you already have the starting configurations of the beads of the string you
can just add them as `md/0/0/restrained/confout.gro`,
`md/0/1/restrained/confout.gro`, ...

Otherwise, send this directory to your favourite HPC cluster (tcblab for
@DelemotteLab). Modify according to the instructions inside
`slurm_steering_tcblab.sh` to your user, anaconda environment and/or HPC set-up.

Check that `config_steered.json` has the options you want for the steering run.
You can also modify the options passed to `gmx mdrun` with the
"mdrun\_options\_steered" for example to give multithread.

The steering simulation can only be run with a single rank. Therefore
acceleration can only be done using GPUs (one or multiple, no need to add any
options to the `config_steered.json`) or using several threads (adding
"mdrun\_options\_steered": ["-nt","number\_of\_threads\_in\_node"] to
`config_steered`).

Once you are happy with the set-up just send the job to queue.

```bash
sbatch slurm_steering_tcblab.sh
```

## Check the initial string and configs

Regardless if you have made the initial string yourself or with steering.
You can use `analyze_initial_string.ipynb` to see the correspondance between
the `string0.txt` and the initial configs.

## Running String Simulation

At this point we are ready to start the string simulation. Go to the
`slurm_string_method_beskow.sh` slurm file and edit it to adapt it to the your
HPC environment. This slurm script can be tailored easily for different
HPC environments.
To choosed the number of threads per rank and adapt `config.json` accordingly.
If you plan on using GPUs you probably want to use
`slurm_string_method_tcblab.sh` and adapt `config.json` accordingly.
Most of these things are done using the "mdrun\_options\_swarms" and/or
"mdrun\_options\_restrained".

Once you have prepared the `slurm_string_method_beskow.sh` you can send it as:

```bash
sbatch slurm_string_method_beskow.sh
```

But if you choose to do the preparation where one job equals one string
iteration (this is how `slurm_string_method_beskow.sh` works),
you can take advantage of [slurm-arrays](https://slurm.schedmd.com/job_array.html).
The option `--array=1-100%1` will send 100 `slurm_string_method_beskow.sh`
jobs that will execute one after the other.

```bash
sbatch --array=1-100%1 slurm_string_method_beskow.sh
squeue -u $USER
```

## Analyzing the results

You can use `analyze_strings.ipynb` to analyze the string-simulations as you go
to check for convergence.

## Tips and tricks

+ For analysis you normally only need `strings/string*.txt` and once converged
`md/*/*/s*/pullx.xvg`. So it might not be worth downloading all that data from
the HPC cluster, but don't errase it since you might need it later.
+ It can take many iterations (100 or so) for the string to converge (oscillate
around average position) only after string convergence you can get FES convergence.
Therefore, initially you might have a poor free energy surface.
+ If your free energy surface does not show a free energy well in your last bead
(the one similar to `end.gro`), your steering simulation might be wrong. Check
the `confout.gro` of the final beads of the steering simulation, you might be
in a different structure due to lack of important cvs or too fast pulling.
+ Another trick is to start a regular MD simulation from one of the last beads of
the steering and see if there is anything wrong. If the steering worked you should
have a trajectory that looks like `end.gro`.

# May convergence be with you!
