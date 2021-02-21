# String Simulation Start-Up:

This is a small tutorial on how to set up simple (but powerfull) string-method simulations from scratch. The slurm-files are adapted the supercomputing environments of the @DelemotteLab but should be adaptable to any other HPC centers.

The files are an example of string-simulation of the beta2 receptor.

## Ingredients:
To run string-method simulations you will need:
+ A starting state configuration: `topology/start.gro`
+ A end state configuration (this one you don't strickly need): `topology/end.gro`
+ A topology file with gmx topology: `topology/topol.top` 
+ A gmx index file: `topology/index0.ndx`. Note it's index0. 
+ An idea of which distances between groups of atom/s could be good cvs for the string. i. e. "The distance between the centers of mass of resid 1 and resid 14" and/or "The distance between CB atoms of resid 131 and resid 378".

You might want to use but not need strickly:
+ An anaconda installation.
+ If you have your own initial string from other simulations or your imagination:
  + A txt file with the string with `np.savetxt` format and shape (ncvs, nbeads): `strings/string0.txt`
  + The starting beads of the initial string: `md/0/0/restrained/confout.gro`, `md/0/1/restrained/confout.gro`, ... 

Put these files in the directories specified above.

## Geting started:
First of all you need to install some python libraries. The most convenient way to do this is with anaconda3:
```bash
conda env create -f environment.yml
conda activate string_method
# Optional if you want to visualize some strings.
jupyter labextension install nglview-js-widgets@2.7.7
jupyter-labextension install @jupyter-widgets/jupyterlab-manager
```
This command will create an environment called string\_method with all the necessary libraries to prepare and run string-method simulations.

Within this environment, open the jupyter-notebook  `input_maker.ipynb`. Using this notebook you will be able to prepare the files for the steering simulation and/or the string-method. You will also be able to visualize your initial `string0.txt`.

## Running Steering:

If you already have the starting configurations of the beads of the string you can just add them as" `md/0/0/restrained/confout.gro`, `md/0/1/restrained/confout.gro`, ...

Otherwise, send this directory to your favourite HPC cluster (tcblab for @DelemotteLab). Modify according to the instructions inside `slurm_tcblab_steering.sh` to your user, anaconda environment and/or HPC set-up. 

Check that `config_steered.json` has the options you want for the steering run. You can also modify the options passed to `gmx mdrun` with the "mdrun\_options\_steered" for example to give mpithread or open mp thread parallelism.

Unfortunatelly the steering simulation cannot be run with mpi-ranks, for this reason using GPUs is the best choice.

Once you are happy with the set-up just send the job to queue

## Check the initial string and configs:
Regardless if you have made the initial string yourself or with steering. You can use `analyze_initial_string.ipynb` to see the correspondance between the `string0.txt` and the initial configs.

## Running String Simulation:
At this point we are ready to start the string simulation. Go to the `slurm_string_method_beskow.sh` slurm file and edit it to adapt it to the your HPC environment since it is currently prepared for beskow (@DelemotteLab). This slurm script can be tailored easily for other CPU-based HPC environments. To choosed the number of mpi-processes make sure to check the main README.md's notes on parallelization.

You should also modify `config.json` to fit your needs. You can also modify the options passed to `gmx mdrun` with the "mdrun\_options\_swarms" and/or "mdrun\_options\_restrained" for example to give mpithread or open mp thread parallelism.

Once you have prepared the `slurm_string_method_beskow.sh` you can send it as:
```bash
sbatch slurm_string_method_beskow.sh
```
But if you choose to do the preparation where one job equals one string iteration, you can take advantage of [slurm-arrays](https://slurm.schedmd.com/job_array.html). This command will send 100 `slurm_string_method_beskow.sh` jobs that will execute one after the other. The will have a single `` but differ in the ``:
```bash
sbatch slurm_string_method_beskow.sh
squeue -u $USER
```

## Analyzing the results:
You can use `analyze_strings.ipynb` to analyze the string-simulations as you go to check for convergence.

May convergence be with you!
