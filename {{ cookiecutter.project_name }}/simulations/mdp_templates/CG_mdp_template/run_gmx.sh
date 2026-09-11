#!/bin/bash -l
# Parameters for sbatch
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --gres-flags=enforce-binding
#SBATCH --time=1440:00:00
#SBATCH -J NAME
#SBATCH -p 

# Script to run gmx simulation steps

# Load gromacs module if needed
# module load all/GROMACS/2026.0-CUDA-12.1.1


# Equilibration steps
cd equilibration

gmx grompp -f equilibration.mdp -c ../minimisation/minimisation.gro -p ../assembly/topol.top -n ../assembly/index.ndx -o equilibration.tpr
gmx mdrun -deffnm equilibration -v -ntomp 8 -ntmpi 1


# Production
cd ../production

gmx grompp -f production.mdp -c ../equilibration/step6_equilibration.gro -p ../assembly/topol.top -n ../assembly/index.ndx -o production.tpr
gmx mdrun -deffnm production -v -ntomp 8 -ntmpi 1
# -cpi production.cpt
