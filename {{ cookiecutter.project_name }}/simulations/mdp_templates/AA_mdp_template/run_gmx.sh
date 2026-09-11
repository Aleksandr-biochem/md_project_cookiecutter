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

mini_prefix="../minimisation/minimisation"
equi_prefix="step%d_equilibration"

# Equilibration steps
cd equilibration

cnt=1
cntmax=6
while [ ${cnt} -le ${cntmax} ]
do
    pcnt=$(expr ${cnt} - 1)
    istep=$(printf "${equi_prefix}" ${cnt})
    pstep=$(printf "${equi_prefix}" ${pcnt})
    if [ ${cnt} == 1 ]
    then
        pstep=${mini_prefix}
    fi
    gmx grompp -f ${istep}.mdp -o ${istep}.tpr -c ${pstep}.gro -r ../assembly/assembly.gro -p ../assembly/topol.top -n ../assembly/index.ndx
    gmx mdrun -v -deffnm ${istep} -ntomp 8 -ntmpi 1
    ((cnt+=1))
done


# Production
cd ../production

gmx grompp -f production.mdp -c ../equilibration/step6_equilibration.gro -p ../assembly/topol.top -n ../assembly/index.ndx -o production.tpr
gmx mdrun -deffnm production -v -ntomp 8 -ntmpi 1
# -cpi production.cpt
