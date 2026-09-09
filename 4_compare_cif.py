import os
from ase.io import read
from ase.geometry import cell_to_cellpar
from itertools import combinations
import numpy as np

def are_structures_identical(a1, a2, tol=1e-5):
    """Compare two ASE Atoms objects for exact structural equivalence."""
    if len(a1) != len(a2):
        return False
    if not np.allclose(cell_to_cellpar(a1.cell), cell_to_cellpar(a2.cell), atol=tol):
        return False

    s1 = sorted(zip(a1.get_chemical_symbols(), np.round(a1.get_positions(), 5).tolist()))
    s2 = sorted(zip(a2.get_chemical_symbols(), np.round(a2.get_positions(), 5).tolist()))
    return s1 == s2


def compare_cif_folder(folder_path):
    """Compare all CIF files in a folder and print only identical groups."""
    cif_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".cif")]
    structures = {}

    for f in cif_files:
        path = os.path.join(folder_path, f)
        try:
            structures[f] = read(path)
        except Exception:
            continue  # skip unreadable CIFs

    groups = []
    visited = set()

    for f1, f2 in combinations(structures.keys(), 2):
        if are_structures_identical(structures[f1], structures[f2]):
            found_group = None
            for g in groups:
                if f1 in g or f2 in g:
                    found_group = g
                    break
            if found_group:
                found_group.update([f1, f2])
            else:
                groups.append(set([f1, f2]))
            visited.update([f1, f2])

    if groups:
        print("🔍 Identical CIF Groups Found:")
        for i, g in enumerate(groups, 1):
            print(f"Group {i} ({len(g)} files): {', '.join(sorted(g))}")
    else:
        # No duplicates found — stay silent
        pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python compare_cifs.py <folder_path>")
    else:
        compare_cif_folder(sys.argv[1])
