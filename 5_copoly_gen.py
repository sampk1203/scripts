import random
import subprocess
import io
import os
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from ase.visualize import view
from ase.io import read
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
## Some atoms may overlap after optimisation, be careful before using for packing.
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# =================================================================
# 1. CONFIGURATION & POLYMER DATA
# =================================================================
CHAIN_LENGTH = 5 # Increased length to better reflect statistical ratios
MOL_OUTPUT = "copolymer_output.mol"
XYZ_OUTPUT = "copolymer_output.xyz"

# Markov Transition Table (Probability of Row -> Column)
# Example: PVDF-HFP (FKM-type) where HFP rarely follows HFP
TRANSITIONS = {
    "PEO": {"PEO": 1.0}
    }

POLYMERS = {
    "PEO":  {"smiles": "[*]CCO[*]"},
    "PMMA": {"smiles": "[*]CC(C)(C(=O)OC)[*]"},
    "PVDF": {"smiles": "[*]CC(F)(F)[*]"},
    "HFP":  {"smiles": "[*]C(F)(F)C(F)(C(F)(F)F)[*]"},
    "PAA":  {"smiles": "[*]CC(C(=O)O)[*]"},
    "PVA":  {"smiles": "[*]CC(O)[*]"},
    "PAN":  {"smiles": "[*]CC(C#N)[*]"},
    "PE":   {"smiles": "[*]CC[*]"}
}

COLOR_MAP = {name: num for name, num in zip(POLYMERS.keys(), [7, 8, 9, 15, 16, 17, 35, 53])}

# =================================================================
# 2. RATIO CALCULATION LOGIC
# =================================================================

def calculate_expected_ratios(trans_dict):
    """Calculates the theoretical steady-state ratio of monomers."""
    keys = list(trans_dict.keys())
    size = len(keys)
    matrix = np.array([[trans_dict[row][col] for col in keys] for row in keys])

    # Solve for the eigenvector of the transposed matrix where eigenvalue = 1
    # This represents the stationary distribution (pi * P = pi)
    vals, vecs = np.linalg.eig(matrix.T)

    # Find the eigenvector corresponding to the eigenvalue closest to 1
    stationary = vecs[:, np.isclose(vals, 1.0)].real
    stationary = stationary / stationary.sum()

    ratios = dict(zip(keys, stationary.flatten()))

    print("\n--- THEORETICAL MONOMER RATIOS ---")
    for monomer, ratio in ratios.items():
        print(f"{monomer}: {ratio*100:.2f}%")
    print("----------------------------------\n")
    return ratios

# =================================================================
# 3. HELPER FUNCTIONS
# =================================================================

def view_colored_by_monomer(rdmol, atom_map):
    view_mol = Chem.Mol(rdmol)
    for idx, m_type in atom_map.items():
        view_mol.GetAtomWithIdx(idx).SetAtomicNum(COLOR_MAP[m_type])
    AllChem.Compute2DCoords(view_mol)
    f = io.StringIO(Chem.MolToMolBlock(view_mol))
    view(read(f, format='sdf'))

def run_obabel_uff(mol_block, output_fmt="mol"):
    cmd = ["obabel", "-imol", "--minimize", "--ff", "UFF", "--steps", "1000", f"-o{output_fmt}"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, _ = proc.communicate(input=mol_block)
    return out

def get_conn_indices(mol):
    dummies = [at.GetIdx() for at in mol.GetAtoms() if at.GetSymbol() == '*']
    h = mol.GetAtomWithIdx(dummies[0]).GetNeighbors()[0].GetIdx()
    t = mol.GetAtomWithIdx(dummies[1]).GetNeighbors()[0].GetIdx()
    return h, t

# =================================================================
# 4. CORE LOGIC
# =================================================================

def build_copolymer():
    # 0. Predict Ratio
    calculate_expected_ratios(TRANSITIONS)

    # 1. Sequence Generation
    available_monomers = list(TRANSITIONS.keys())
    current_type = random.choice(available_monomers)
    sequence = [current_type]
    for _ in range(CHAIN_LENGTH - 1):
        weights = TRANSITIONS[current_type]
        current_type = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        sequence.append(current_type)

    print(f"Generated Full Sequence: {'-'.join(sequence)}")

    # 2. Assembly
    full_chain = Chem.RWMol(Chem.MolFromSmiles(POLYMERS[sequence[0]]["smiles"]))
    atom_to_type = {i: sequence[0] for i in range(full_chain.GetNumAtoms())}
    _, current_tail = get_conn_indices(full_chain)

    for i in range(1, len(sequence)):
        m_type = sequence[i]
        next_monomer = Chem.MolFromSmiles(POLYMERS[m_type]["smiles"])
        next_head, next_tail = get_conn_indices(next_monomer)
        offset = full_chain.GetNumAtoms()
        full_chain.InsertMol(next_monomer)
        for j in range(next_monomer.GetNumAtoms()):
            atom_to_type[j + offset] = m_type
        full_chain.AddBond(current_tail, next_head + offset, Chem.rdchem.BondType.SINGLE)
        current_tail = next_tail + offset

    # 3. Cleanup Dummies
    all_dummies = [at.GetIdx() for at in full_chain.GetAtoms() if at.GetSymbol() == '*']
    for d_idx in sorted(all_dummies, reverse=True):
        full_chain.RemoveAtom(d_idx)
        atom_to_type = { (k-1 if k > d_idx else k): v for k, v in atom_to_type.items() if k != d_idx }

    raw_mol = full_chain.GetMol()
    Chem.SanitizeMol(raw_mol)

    # Visual Check 1 (Colored)
    view_colored_by_monomer(raw_mol, atom_to_type)

    # 4. Optimization
    print("Embedding and Optimizing...")
    AllChem.EmbedMolecule(raw_mol, AllChem.ETKDG())
    backbone_mol = run_obabel_uff(Chem.MolToMolBlock(raw_mol), "mol")
    temp_rdmol = Chem.MolFromMolBlock(backbone_mol)
    final_rdmol = Chem.AddHs(temp_rdmol, addCoords=True)

    final_mol_data = run_obabel_uff(Chem.MolToMolBlock(final_rdmol), "mol")
    final_xyz_data = run_obabel_uff(Chem.MolToMolBlock(final_rdmol), "xyz")

    # Visual Check 2 (Final)
    view(read(io.StringIO(final_mol_data), format='sdf'))

    return final_mol_data, final_xyz_data

if __name__ == "__main__":
    mol_out, xyz_out = build_copolymer()
    with open(MOL_OUTPUT, "w") as f: f.write(mol_out)
    with open(XYZ_OUTPUT, "w") as f: f.write(xyz_out)
