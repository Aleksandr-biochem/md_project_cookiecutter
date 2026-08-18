#! /usr/bin/env python

import os
import COBY
import shutil
import subprocess
import MDAnalysis as mda

#########################################################
# This is an example script that uses COBY to set up several replicates
# of the solvated POPC bilayer in MARTINI2
#########################################################

def CreateIndex(structure, out_file, groups, group_names):

	# read system
	system = mda.Universe(structure)

	# write index
	print("Creating index...")
	with mda.selections.gromacs.SelectionWriter(out_file, mode='w') as ndx:
		for group, name in zip(groups, group_names):

			# make a selection
			selection = system.select_atoms(group)

			# print selection info
			n_atoms = len(selection)
			n_residues = len(selection.residues)
			print(f"Selection {group} named {name} has:\t{n_atoms} atoms\t{n_residues} residues")

			#write the group into index
			ndx.write(selection, name=name)
	return

if __name__ == "__main__":

	# save current working directory
	cwd = os.getcwd()

	N_REPLICATES = 3

	for i in range(1, N_REPLICATES + 1):
		
		# reset cwd
		os.chdir(cwd)

		# create rep dir 
		os.makedirs(f"rep{i}", exist_ok=True)
		os.makedirs(f"rep{i}/assembly_minimisation", exist_ok=True)

		# go to assembly folder
		os.chdir(f"rep{i}/assembly_minimisation")

		# copy toppar from template folder
		shutil.copytree(
			'../../template/toppar',
			'./toppar'
		)

		sysname = 'POPC_bilayer'
		COBY.COBY(
			
			### box size nm
			box = [15, 15, 8.5],
			
			# membrane consisting of 1 lipid type
			membrane = "lipid:POPC apl:0.682",
			
			### 'solvation' argument solvates the system using the default solvation settings of "solv:W pos:NA neg:CL"
			### The default concentration of water is 55.56 [mol/L] ("solv_molarity:55.56")
			### The default salt concentration is 0.15 [mol/L] ("salt_molarity:0.15")
			# solvation = "default",
			solvation = "default salt_method:mean",

			itp_input = [
				# ff parameters
				f"file:toppar/martini_v2.2.itp",
				f"include:toppar/martini_v2.2.itp",

				# additional definitions
				f"include:toppar/martini_v2.0_lipids_combined.itp",
				f"include:toppar/martini_v2.0_ions.itp",
			],
			
			### File writing
			out_sys = sysname,
			out_top = "topol.top",
			out_log = f"{sysname}.log",
			
			### Designates the system name that is written in .pdb, .gro and .top files
			sn = sysname
		)
		
		# create index
		CreateIndex(
			"POPC_bilayer.gro",
			"index.ndx",
			groups=[
				"resname W NA CL",
				"resname POPC",
				"all"
			],
			group_names=['SOLV', 'MEMB', 'SYSTEM']
		)
		
		# run minimisation
		shutil.copy(
			'../../template/minimisation.mdp',
			'./minimisation.mdp'
		)

		# run gmx
		gmx_args = ["gmx", "grompp",
					"-p",  "topol.top",
					"-f",  "minimisation.mdp",
					"-c",  "POPC_bilayer.gro",
					"-o",  "minimisation.tpr",
					"-maxwarn", "1"]
		process = subprocess.Popen(gmx_args, stdin=subprocess.PIPE)
		returncode = process.wait()

		gmx_args = ["gmx", "mdrun",
					"-deffnm", "minimisation", "-v",
					"-nt", "12"]
		process = subprocess.Popen(gmx_args, stdin=subprocess.PIPE)
		returncode = process.wait()

		# copy files for equilibration and production
		os.chdir('../')

		shutil.copytree(
			'../template/equilibration',
			'./equilibration'
		)

		shutil.copytree(
			'../template/production',
			'./production'
		)

		# you can also add equilibration and production steps you want to run them locally
