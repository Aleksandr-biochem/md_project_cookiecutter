#! /usr/bin/bash

# Bash script to postprocess GROMACS trajectories by centering them and excluding water
# Tip: run the script on one system first to ensure that everything works as expected

# save initial working directory
cwd=$(pwd)

declare -a groups=("simulations")
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
			cd "${group}/${system}/rep${r}/production"
			
			# check if processed trajectory exists
			if [ ! -f "prodction_no_water.xtc" ]; then

				# convert trajectory
				printf "SOLU\nSOLU_MEMB\n" | gmx trjconv -s production.tpr -f production.xtc -o production_no_water.xtc -center -pbc mol -n ../assembly/index.ndx 

				# convert first frame
				printf "SOLU\nSOLU_MEMB\n" | gmx trjconv -s production.tpr -f production.xtc -o production_no_water_start.gro -center -pbc mol -n ../assembly/index.ndx -dump 0

				# convert last frame
				# NOTE (Sept 26): newer versions of GROMACS will dump the last frame if you specify the time beyound the simualtions length with '-dump'
				# this is not the case with some older versions (seemingly <= 2024), jrjconv will write an empty file, so you will need to specify an existing time 
				printf "SOLU\nSOLU_MEMB\n" | gmx trjconv -s production.tpr -f production.xtc -o production_no_water.gro -center -pbc mol -n ../assembly/index.ndx -dump 10000000000

				# convert tpr
				# NOTE (Sept 26): sometimes MDAnalysis does not work properly with tpr files constructed using convert-tpr,
				# convert-tpr can seemingly affect residue groupings and maybe something else. If encountered, create a new tpr without water using 'gmx grompp'
				printf "SOLU_MEMB\n" | gmx convert-tpr -s production.tpr -n ../assembly/index.ndx -o production_no_water.tpr

				# for CG systems, save the last frame as pdb with CONECT records for the ease of visualisation
				# touch empty.mdp 
				# gmx grompp -f empty.mdp -c production.gro -o production_final_frame.tpr -p ../assembly/topol.top
				# gmx editconf -f production_final_frame.tpr -o production_final_frame.pdb -conect
				##############################################################################################
			fi


		done

	done
	
done