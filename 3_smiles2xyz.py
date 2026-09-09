#!/usr/bin/env python3
import sys
import os
import re
import numpy as np
from tempfile import NamedTemporaryFile
from rdkit import Chem
from rdkit.Chem import AllChem, rdchem
from ase.io import read
from ase.visualize import view

# ========================
# Polymer definitions (start/repeat/end)
# ========================
POLYMERS = {
    "PEO": {
        "fullname": "Poly(ethylene oxide)",
        "start": "O",
        "repeat": "CCO",
        "end": ""
    },
    "PMMA": {
        "fullname": "Poly(methyl methacrylate)",
        "start": "",
        "repeat": "C(C)(C(=O)OC)C",
        "end": ""
    },
    "PVDF": {
        "fullname": "Poly(vinylidene fluoride)",
        "start": "",
        "repeat": "C(F)(F)C",  # [-CH2-CF2-]
        "end": ""
    },
    "PAA": {
        "fullname": "Poly(acrylic acid)",
        "start": "",
        "repeat": "CC(C(=O)O)",
        "end": ""
    },
    "PVA": {
        "fullname": "Poly(vinyl alcohol)",
        "start": "",
        "repeat": "C(CO)",
        "end": ""
    },
    "PAN": {
        "fullname": "Polyacrylonitrile",
        "start": "",
        "repeat": "C(C#N)C",
        "end": ""
    },
    "PE": {
        "fullname": "Polyethylene",
        "start": "",
        "repeat": "CC",
        "end": ""
    },
}

# ========================
# Helpers
# ========================
MIN_DIST = 0.7
VALENCY = {"H":1,"C":4,"N":3,"O":2,"F":1,"Cl":1,"Br":1,"I":1,"S":2,"P":3}

def get_next_molecule_filename():
    files = [f for f in os.listdir(".") if re.match(r"molecule\d+\.mol$", f)]
    if not files:
        return "molecule1.mol"
    nums = [int(re.findall(r"\d+", f)[0]) for f in files]
    return f"molecule{max(nums)+1}.mol"

def visualize_mol(mol, label=""):
    with NamedTemporaryFile(suffix=".mol", delete=False) as tmp:
        Chem.MolToMolFile(mol, tmp.name, kekulize=False)
        atoms = read(tmp.name)
        print(f"👁️ Visualizing {label} ...")
        view(atoms)

def separate_close_atoms(positions, min_dist=0.2, max_iter=100):
    positions = positions.copy()
    for _ in range(max_iter):
        moved = False
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                vec = positions[i] - positions[j]
                dist = np.linalg.norm(vec)
                if dist < min_dist:
                    if dist == 0:
                        vec = np.random.rand(3) - 0.5
                        dist = np.linalg.norm(vec)
                    displacement = 0.5 * (min_dist - dist) * (vec / dist)
                    positions[i] += displacement
                    positions[j] -= displacement
                    moved = True
        if not moved:
            break
    return positions

# ========================
# Hydrogen addition (keeps original bonds)
# ========================
def add_hydrogens_keep_bonds(mol):
    conf = mol.GetConformer()
    positions = [np.array(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]
    new_atoms = []
    new_positions = []

    original_atoms = list(mol.GetAtoms())
    for i, atom in enumerate(original_atoms):
        sym = atom.GetSymbol()
        val = VALENCY.get(sym, 0)
        n_bonds = sum([b.GetBondTypeAsDouble() for b in atom.GetBonds()])
        n_h_needed = max(int(val - n_bonds), 0)

        for _ in range(n_h_needed):
            direction = np.random.rand(3) - 0.5
            direction /= np.linalg.norm(direction)
            new_pos = positions[i] + direction * MIN_DIST

            while any(np.linalg.norm(new_pos - p) < MIN_DIST for p in positions + new_positions):
                direction = np.random.rand(3) - 0.5
                direction /= np.linalg.norm(direction)
                new_pos = positions[i] + direction * MIN_DIST

            new_atom_idx = mol.AddAtom(Chem.Atom("H"))
            mol.AddBond(i, new_atom_idx, Chem.BondType.SINGLE)
            new_positions.append(new_pos)
            new_atoms.append(new_atom_idx)

    for idx, pos in zip(new_atoms, new_positions):
        conf.SetAtomPosition(idx, tuple(pos))

    return mol


# ========================
# Polymer builder (generalized for start/repeat/end)
# ========================
def build_polymer_from_units(units, buffer=1.2):
    """
    Build polymer from a list of SMILES units (start + repeat*n + end).
    Each unit is embedded and then connected sequentially.
    """
    # Pre-embed all units
    embedded = []
    for smi in units:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smi}")
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        if AllChem.EmbedMolecule(mol, params) != 0:
            params.useRandomCoords = True
            if AllChem.EmbedMolecule(mol, params) != 0:
                raise RuntimeError(f"Embedding failed for {smi}")
        embedded.append(mol)

    polymer_rw = Chem.RWMol()
    positions_all = []
    prev_offset = None
    prev_last_idx = None

    for rep, mol in enumerate(embedded):
        conf = mol.GetConformer()
        n_atoms = mol.GetNumAtoms()
        pos = np.array([list(conf.GetAtomPosition(i)) for i in range(n_atoms)])

        # First and last atom (connection points)
        idx_first = 0
        idx_last = n_atoms - 1

        # Vector for spacing based on this monomer’s geometry
        vec = pos[idx_last] - pos[idx_first]
        norm = np.linalg.norm(vec)
        if norm < 1e-8:
            unit = np.array([1.0, 0.0, 0.0])
            spacing = buffer
        else:
            unit = vec / norm
            spacing = norm + buffer

        offset = polymer_rw.GetNumAtoms()
        for i in range(n_atoms):
            at = mol.GetAtomWithIdx(i)
            polymer_rw.AddAtom(Chem.Atom(at.GetAtomicNum()))
            translated_pos = pos[i] + unit * spacing * rep
            positions_all.append(translated_pos)

        # Internal bonds of this unit
        for b in mol.GetBonds():
            polymer_rw.AddBond(int(offset + b.GetBeginAtomIdx()),
                               int(offset + b.GetEndAtomIdx()),
                               b.GetBondType())

        # Connect to previous unit
        if prev_offset is not None:
            curr_first_idx = int(offset + idx_first)
            polymer_rw.AddBond(prev_last_idx, curr_first_idx, Chem.BondType.SINGLE)
        prev_offset = offset
        prev_last_idx = int(offset + idx_last)

    # Separate overlapping atoms slightly
    positions_all = separate_close_atoms(np.array(positions_all), min_dist=0.2)

    # Build final conformer
    polymer = polymer_rw.GetMol()
    conf = Chem.Conformer(polymer.GetNumAtoms())
    for i, p in enumerate(positions_all):
        conf.SetAtomPosition(i, tuple(p))
    polymer.AddConformer(conf)

    try:
        Chem.SanitizeMol(polymer)
    except Exception as e:
        print("⚠️ Warning: SanitizeMol failed:", e)

    polymer_with_h = add_hydrogens_keep_bonds(Chem.RWMol(polymer))

    outfile = get_next_molecule_filename()
    Chem.MolToMolFile(polymer_with_h, outfile)
    print(f"✅ Saved {outfile} with hydrogens and original bonds preserved")
    return outfile


# ========================
# Main logic
# ========================
def print_usage_and_list():
    print("Available polymers:")
    for short, pdata in POLYMERS.items():
        print(f"  {short:<5}: {pdata['fullname']}")
    print(f"\nUsage: {sys.argv[0]} <polymer_name> <num_repeats>")

if len(sys.argv) < 3:
    print_usage_and_list()
    sys.exit(0)

poly_name = sys.argv[1]
try:
    num_repeats = int(sys.argv[2])
except Exception:
    print("Error: <num_repeats> must be an integer.")
    sys.exit(1)

if poly_name not in POLYMERS:
    print(f"Error: Polymer '{poly_name}' not found.")
    print_usage_and_list()
    sys.exit(1)

if num_repeats < 1:
    print("Error: number of repeats must be >= 1")
    sys.exit(1)

pdef = POLYMERS[poly_name]
units = []
if pdef["start"]:
    units.append(pdef["start"])
units.extend([pdef["repeat"]] * num_repeats)
if pdef["end"]:
    units.append(pdef["end"])

# 1. Build the polymer and catch the returned filename AND the molecule object
# Change your function return or simply reload the mol from the file you just saved
print(f"Building {poly_name} ({num_repeats} repeats) with units: {units}")
outfile_mol = build_polymer_from_units(units, buffer=1.2)

# Load the molecule back from the file to ensure we have the full RDKit object
mol_to_opt = Chem.MolFromMolFile(outfile_mol, removeHs=False)

# ========================
# Optimization & Output (Open Babel UFF)
# ========================
import subprocess

if outfile_mol and os.path.exists(outfile_mol):
    # 1. Define filenames
    # We will use the same filename for the optimized version
    outfile_xyz = outfile_mol.replace(".mol", ".xyz")
    
    print(f"⚖️ Optimizing {outfile_mol} with Open Babel UFF (Steepest Descent)...")
    
    try:
        # Step A: Optimize the .mol file (Overwrites the raw file with optimized coords)
        # --minimize --ff UFF --sd: Runs Steepest Descent optimization
        opt_cmd = f"obabel {outfile_mol} -O {outfile_mol} --minimize --ff UFF --sd"
        subprocess.run(opt_cmd, shell=True, check=True, capture_output=True)
        
        # Step B: Create the .xyz file from the NOW optimized .mol file
        conv_cmd = f"obabel {outfile_mol} -O {outfile_xyz}"
        subprocess.run(conv_cmd, shell=True, check=True, capture_output=True)
        
        print(f"✅ Success! Optimized files created:")
        print(f"   - {outfile_mol}")
        print(f"   - {outfile_xyz}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Open Babel failed: {e.stderr.decode()}")
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
else:
    print("⚠️ No input .mol file found to optimize.")

# Optional: visualize the final result
final_mol = Chem.MolFromMolFile(outfile_mol, removeHs=False)
if final_mol:
    visualize_mol(final_mol, label=f"OBabel Optimized {poly_name}")

print("Done.")