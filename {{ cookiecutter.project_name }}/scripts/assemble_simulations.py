#! /usr/bin/env python

import os
import COBY
import shutil
import argparse
import subprocess
import numpy as np
from pathlib import Path
import MDAnalysis as mda

"""
Assembly replicates for simulation with GROMACS.
Created for coarse-grained system assembly with COBY but can be modified for many other applications.

Tip: comment-out parts of the script such as minimisation and test on 1 rep to ensure that the systems are assembled as expected.
"""

# list of all systems to simulate
SYSTEM_LIST = [
	'system1',
	'system2',
]

# Num of replicates to assemble with each system
N_REPLICATES = 3

def run_COBY(sysname: str, memb_type: str, n_AMPs: str, ff: str) -> None:
	"""Run system assembly with COBY
	See COBY Tutorials for detailed examples https://github.com/MikkelDA/COBY/tree/master/Tutorial"""
	
	# list itps in simulations/toppar.ff to be included 
	include_itps = []
	for file in list(Path('../../toppar.ff').iterdir()):
		if (file.suffix == '.itp') and (file.name != 'forcefield.itp'):
			include_itps.append(str(file))

	COBY.COBY(
		### box size nm
		box = [10, 10, 10],

		# example molecule import 
		# molecule_import = [
		# 	"file:toppar/CDL2.gro moleculetype:CDL2 params:IMPORTED",
		# ],
		
		# membrane
		membrane = "lipid:DPPC",

		### 'solvation' argument solvates the system using the default solvation settings of "solv:W pos:NA neg:CL"
		### The default concentration of water is 55.56 [mol/L] ("solv_molarity:55.56")
		### The default salt concentration is 0.15 [mol/L] ("salt_molarity:0.15")
		solvation = "default salt_method:mean",

		# insert protein(s) 
		protein = [
			" ".join([
				"file:path/to/protein_cg.pdb",
				"moleculetypes:molecule_0",
				# "cx:1.5"
			]),

			# other if needed
			# " ".join([
			#	 "file:path/to/protein_cg.pdb",
			#	 "moleculetypes:molecule_0",
			#	 "cx:-1.5"
			# ]),

		],

		# all itps included in topology
		# assumes that ff parameters live in simulations/toppar.ff
		itp_input = [
			# ff parameters
			"file:../../toppar.ff/forcefield.itp",
			"include:../../../toppar.ff/forcefield.itp",
		] + include_itps,
		
		### File writing
		out_sys = "assembly",
		out_top = "topol.top",
		out_log = "coby.log",
		
		### Designates the system name that is written in .pdb, .gro and .top files
		sn = "assembly",
	)

	return


def create_index(structure: str, out_file: str, groups: list[str], group_names: list[str]) -> None:
	"""
	Create index with custom groups using MDAnalysis selection language
	"""
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

	# assemble each system
	for system in SYSTEM_LIST:

		os.chdir(cwd) # reset cwd
		os.makedirs(system, exist_ok=True)

		# assemble each replicate
		for i in range(1, N_REPLICATES + 1):
			
			os.chdir(f"{cwd}/{system}")

			# skip if minimised system (or other checkpoint file) exists
			if os.path.isfile(f"rep{i}/minimisation/minimisation.gro"):
				continue

			# create rep dir from `template` files assuming `simulations/template` exists and contains
			# folders with mdp files for simulation steps
			shutil.copytree(
				"../template",
				f"rep{i}"
			)

			# create an assembly folder
			os.makedirs(f"rep{i}/assembly", exist_ok=True)
			os.chdir(f"rep{i}/assembly")

			# assemble system with COBY
			run_COBY()

			# create index
			create_index(
				"assembly.gro",
				"index.ndx",
				groups=[
					"resname W NA CL",
					"resname POPE POPG CDL2",
					"protein",
					"protein or resname POPE POPG CDL2",
					"all"
				],
				group_names=['SOLV', 'MEMB', 'SOLU', 'SOLU_MEMB', 'SYSTEM']
			)
			

			os.chdir("../minimisation")

			# run gmx
			gmx_args = ["gmx", "grompp",
						"-p",  "topol.top",
						"-f",  "minimisation.mdp",
						"-c",  "../assembly/assembly.gro",
						# for minimisation with restraints
						# "-r", "../assembly/assembly.gro",
						"-o",  "minimisation.tpr",
						"-maxwarn", "1"]
			process = subprocess.Popen(gmx_args, stdin=subprocess.PIPE)
			returncode = process.wait()

			gmx_args = [
				"gmx", "mdrun",
				"-deffnm", "minimisation", "-v",
				# choose parameters feasible for the current hardware
				# "-nt", "12", "-gpu_id", "0"
			]
			process = subprocess.Popen(gmx_args, stdin=subprocess.PIPE)
			returncode = process.wait()

			# TIP: you can also script other simulation steps, e.g. equilibration

			# edit job name in the run_gmx.sh script
			os.chdir("../")
			path = Path('run_gmx.sh')
			text = path.read_text()
			text = text.replace("#SBATCH -J NAME", f"#SBATCH -J {system}_r{i}")
			path.write_text(text)
