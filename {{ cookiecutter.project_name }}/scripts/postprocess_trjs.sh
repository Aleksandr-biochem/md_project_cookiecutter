#! /usr/bin/bash

# This is an example bash script to postprocess trajectories
# by centering them and excluding water

# save initial working directory
cwd=$(pwd)

declare -a groups=("group1" "group2")
declare -a systems=("system1" "system2")

# go though each group
for group in ${groups[@]}
do 	

	# postprocess replicates in each system
	for system in ${systems[@]}
	do 
		# e.g. 3 replicates
		for r in {1..3}
		do
		
			cd $cwd
			cd "simulations_${group}/${system}/rep${r}/production"
			
			# check if processed trajectory exists
			if [ ! -f "mdrun_no_water.xtc" ]; then

				# convert trajectory
				printf "SOLU\nSOLU_MEMB\n" | gmx trjconv -s mdrun.tpr -f mdrun.xtc -o mdrun_no_water.xtc -center -pbc nojump -n ../assembly_minimisation/index.ndx 

				# convert first frame
				printf "SOLU\nSOLU_MEMB\n" | gmx trjconv -s mdrun.tpr -f mdrun.xtc -o mdrun_no_water.gro -center -pbc nojump -n ../assembly_minimisation/index.ndx -dump 0

				# convert tpr
				printf "SOLU_MEMB\n" | gmx convert-tpr -s mdrun.tpr -n ../assembly_minimisation/index.ndx -o mdrun_no_water.tpr
			fi


		done

	done
	
done