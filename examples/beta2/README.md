[Image of beta2 receptor](beta2_receptor.png)
String method to find the activation pathway of a G protein-coupled receptor (GPCR).
We study the beta2 adrenergic receptor in its native apo state.

# Running the example
There are two bash scripts, **run_omp.sh**, for running it on a single machine without MPI support, and **run_mpi.sh**, for running it in an MPI environment.  
You need to run steered MD before string MD. 
There's also a script **submit_beskow.sh** for running it in a slurm environment with MPI.


You don't need to run steered MD before string MD here; the input files for the first iteration are already provided.  

For tips on postprocessing, we recommend you to check out the [alanine-dipeptide example.](../alanine-dipeptide) 


# References
Read [the following paper for details](https://doi.org/10.1021/acs.biochem.9b00842):

Fleetwood, Oliver, et al. "Energy Landscapes Reveal Agonist Control of G Protein-Coupled Receptor Activation via Microswitches." Biochemistry 59.7 (2020): 880-891.