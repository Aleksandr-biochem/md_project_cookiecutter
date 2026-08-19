# Molecular Dynamics Project Cookiecutter

A cookiecutter template to quick start and organise new Molecular Dynamics or generally Computational Biology projects. 

Read more [about cookiecutters](https://cookiecutter.readthedocs.io/en/stable/README.html).

**This cookiecutter is under development, watch for updates**

-------------

## What does this template do?

- Creates a directory structure (e.g. `data`, `plots`, `scripts`, `simulations` etc.)

- Runs `venv` to create a new Python environment for the project with requested libraries.

-`git init` a new repository in the project directory.


## Use this template by fetching from GitHub

```bash
cookiecutter gh:Aleksandr-biochem/md_project_cookiecutter
```

This will promt you to choose project name, sign your authorship, and whether to create new environment and init a git repository. 

## Customise for your needs

Customising for your work style and project logic is essential. Here is how you can do this in a few steps:

- Clone this repository locally **OR** fork it to customise.

```bash
# clone the repository
git clone git@github.com:Aleksandr-biochem/md_project_cookiecutter.git

cd md_project_cookiecutter
```

**Edit folders structure and files** in `{{ cookiecutter.project_name }}`. You can create any new folders and add any files that you want in your template. **Note:** it is recommended to place empty `__placeholder_file__` in empty folders so that they can be tracked with `git`. Placeholders are cleaned up by post-generation hooks.

**Advanced customisation with hooks:** a lot of steps can be run as [pre- or post-generation hooks](https://cookiecutter.readthedocs.io/en/stable/advanced/hooks.html). You can implement new hooks in `post_gen_ptoject.py` as functions with signatures `Callable[[None], int]` *(additional instructions incoming)*.

Run your customised cookicutter:

```
# from local clone
cookiecutter local/path/to/md_project_cookiecutter

# from your GitHub fork
cookiecutter gh:User/md_project_cookiecutter
```

## Elements of an organised computational project

This is a general account of how I like to structure my computational projects, which inspired this cookiecutter.

A lot of great ideas and points to consider can be found in [The Good Research Code Handbook](https://goodresearch.dev/zipf).

### 1. File structure 

General file structure that I found convenient through the years:

```
project_name
│   
├─ README.md (for general project notes, file and dir annotation, and other info for archiving)
│   
├─ simulation_setup_and_analysis.ipynb (lab notebook and interactive analysis code)
│   
└───data (input data, pdb files, datases on your molecules etc.)
│   ├─ protein1.pdb
│   │  ...
│    
└───simulations (a folder with your simulations)
│   │
│   ├─ assemble_and_run.py (a script to assemble and run systems replicates in this group)
│   │
│   ├─ template (folder with template files, e.g. .mdp from GROMACS, to be copied in each replicate)
│   │
│   └───system1
│       ├───rep1
|       │   ├─ assembly_minimisation
|       │   ├─ equilibration
|       │   ├─ production
│       │   ├─ production_analysis (data extracted from this system, e.g. rmsd, lipid data etc)
│       │   
│       ├───rep2
│       │   ...
│   
└───scripts (used for postprocessing and analysis of the simulations)
│   ├─ postprocess_trjs.sh
│   │  ...
│   
└───analysis (folder for output data that you aggregated from simulation analysis)
│   ├─ rmsd.csv
│   ├─ ...
│   │  ...
│  
└───plots (plots generated in jupyter notebook)
│   ├─ rmsd_plot.jpg
│   │  ...
│
└───venv (dedicated environment for your project)

```


### A dedicated environment for the project

Ideally, each project should have its own environment. Especially if you are using some niche packages or developing custom code in course of the project.

### Script the steps for reproducibility and provenance

Scripting steps such as system setup, simulation, and postprocessingcan be exceptionally helpful. If you want to rerun simulations with other parameters, add replicates, simulate altered composition etc. you can just take the script, edit it and launch *(or add parametrers to the script allowing to configure execution)*.

Also, looking back you will know for fact how the systems were generated. 

`assemble_and_run.py` is an example for setup of several repliacates of a solvated POPC bilayer in Martini2 force field using [COBY Coarse Grained System Builder](https://github.com/MikkelDA/COBY). 

I also included `scripts/postprocess_trjs.sh` as an example of how you can script postprocessing of the GROMACS trajectories. 

The next levelof automation would be to wrap your project in an executable workflow with tools like [Snakemake](https://snakemake.readthedocs.io/en/stable/). I actually love to do this for the analysis stage. I also have a [tutorial on starting with Snakemake](https://github.com/Aleksandr-biochem/snakemake_md_tutorial). 

### Keep file descriptions in `README.md`.

README is a very helpful format to provide annotation to all the files and directories in you projects. I have a habit of revising and updating `README.md` files across my system regularly to ensure that necessary files are annotated, while unnecessary relics are deleted.

### Jupyter notebook is you lab notebook. 

I like to document my work from start to finish, as well as analyse and plot data in jupyter notebooks. Your notebook can contain details like:

- Comments on the project (scientific questions, how the data was obtained, conclusions, observations, thoughts etc)

- Setup and execution of your simulations/analyses. Step-by-step explanation of how things are done, which scripts are called and how.

- **Document failures as well!** Comments on which approaches failed and why, and why certain method choices were made. This is truly valuable for your future self and for your colleagues who may reuse your work.

- Separate some side-experiments and test versions into other notebooks. Some may contain preliminary experiments and side-explorations. Keep the naming and notes in the notebooks clear. This allows to keep the logic in your main notebook straightforward and intelligeble.

- Notebooks should run top to bottom without failures.

### Version your files and push to remote

As projects evolve you can keep track of changes by using `git` and pushing the files (code and notes rather than huge data files) to a remore private repository.

When the project reaches a milestone (e.g. publication), you can create a tag that will allow to identify this particular version in the future.
