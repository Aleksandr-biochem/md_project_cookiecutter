#! /usr/bin/bash

# Create visualisation states for coarse-grained trajectories using martiniglass
# Tip: test one one rep to ensure that everything runs as expected

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
		# replicates
		for r in {1..3}
		do
		
			cd $cwd
			cd "${group}/${system}/rep${r}/"
			
			# check if a completed trajectory exists
			if [ -f "production/production.gro" ]; then

				# if no visualisation files exist, make them
				if [ ! -f "visualisation/vis.gro" ]; then

					mkdir visualisation
					cd visualisation

					# if martiniglass complains about itp files, it might need ff parameters in this folder for martiniglass
					# cp -r ../../../toppar.ff ./

					# run martiniglass
					# alternatively, use trajectory without water
					martiniglass -p ../assembly/topol.top -f ../equilibration/equilibration.gro -traj ../production/production.xtc -vf -el

				fi

			fi


		done

	done
	
done