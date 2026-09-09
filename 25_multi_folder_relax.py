import os
import glob
import re
from ase.io import read, write
from ase.optimize import BFGS
from ase.constraints import UnitCellFilter
from orb_models.forcefield import pretrained
from orb_models.forcefield.calculator import ORBCalculator


def natural_sort_key(s):
    """Sort strings with numbers in human order, e.g., 2 < 10"""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", s)
    ]


def relax_cifs(folder):
    print(f"--- Processing folder: {folder} ---")

    # Get CIF files sorted naturally
    cif_files = sorted(glob.glob(os.path.join(folder, "*.cif")), key=natural_sort_key)
    if not cif_files:
        print(f"No CIF files found in {folder}")
        return

    # Load ORB model + calculator (only once per folder)
    orbff = pretrained.orb_v3_conservative_inf_omat(
        device="cuda", precision="float32-high"
    )
    calc = ORBCalculator(orbff, device="cuda")

    results = []

    for cif_file in cif_files:
        atoms = read(cif_file)
        atoms.calc = calc

        ucf = UnitCellFilter(atoms)
        dyn = BFGS(ucf, logfile=None)
        dyn.run(fmax=0.05)

        energy = atoms.get_potential_energy()
        results.append((os.path.basename(cif_file), energy))

        relaxed_file = cif_file.replace(".cif", "_relaxed.cif")
        write(relaxed_file, atoms)
        print(f"Relaxed: {relaxed_file} | Energy: {energy:.6f} eV")

    # Sort naturally
    results.sort(key=lambda x: natural_sort_key(x[0]))

    # Write energies
    energies_file = os.path.join(folder, "energies.txt")
    with open(energies_file, "w") as f:
        for fname, e in results:
            f.write(f"{fname}\t{e:.6f}\n")

    print(f"All energies written to {energies_file}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Relax CIF files in one or more folders using ORBModels."
    )
    parser.add_argument(
        "folders",
        nargs="+",
        help="One or more folders containing CIF files"
    )

    args = parser.parse_args()

    for folder in args.folders:
        relax_cifs(folder)

