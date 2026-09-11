import pandas as pd
import numpy as np
import MDAnalysis as mda
from MDAnalysis import transformations


#########################################################
# This SnakeMake workflow defines analyses on simulations
# Run from `simulations` directory
# snakemake --cores N --snakefile ../scripts/analyse_simulations.smk --dry-run
#########################################################

# define wildcards
SYSTEMS = [
	"system1",
	"system2",
] 

REP_IDS = [rep_id for rep_id in range(1, 6)]


#### AUXILIARY FUNCTIONS #####################################

def load_system(top: str, trj: str) -> mda.Universe:
	"""Load and transform the system for analysis"""
	system = mda.Universe(top, trj)

	# transform to centrer protein
	prot = system.select_atoms("protein")
	ag = system.atoms

	workflow = (transformations.unwrap(ag),
				transformations.center_in_box(protein, center='mass'),
				transformations.wrap(ag, compound='residues'))

	system.trajectory.add_transformations(*workflow)

	# add segment ids
	for seg_ind, seg_name in enumerate('ABCDEFGHIJKL'):
		chain_segment = system.add_Segment(segid=seg_name)
		chain_atoms = system.select_atoms(...)
		chain_atoms.residues.segments = chain_segment

	# reset resids for convenient analysis if needed 
	new_resids = [...]
	for seg_ind, seg_name in enumerate('ABCDEFGHIJKL'):
		chain_atoms = system.select_atoms(f'segid {seg_name}')
		chain_atoms.residues.resids = new_resids

	return system

#### OUTPUT DEFINITIONS ######################################

out_files1= expand(
	"{sys_setup}/rep{rep}/analysis/output.csv",
	sys_setup=SYSTEMS,
	rep=REP_IDS
)

out_files2 = expand(...)

target_files = out_files1 + out_files2 # + ...
##############################################################


rule target:
	"""
	A pseudo-rule that sets the final target files
	"""
	input: target_files
		

rule template_analysis:
	"""
	Template rule to run some analysis on trajectory and save output data
	"""
	input:
		trj="{sys_setup}/rep{rep}/production/production_no_water.xtc",
		top="{sys_setup}/rep{rep}/production/production_no_water.tpr"
	output:
		out_file = "{sys_setup}/rep{rep}/analysis/output.csv"
	retries: 1
	run:
		system = load_system(input[1], input[0])
			
		# run analysis on system

		# save output
		with open(output[0], 'w') as out_file:
			...

		# clear memory from large objects 
		del system
