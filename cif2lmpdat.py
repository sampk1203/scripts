# cif_to_lammps.py

import sys
import shutil
from pymatgen.core import Structure
from pymatgen.io.lammps.data import LammpsData
from pymatgen.io.xyz import XYZ

def convert_cif_to_outputs(cif_file, output_data):
    try:
        structure = Structure.from_file(cif_file)
        print(f"[INFO] Read structure with {len(structure)} atoms.")

        # Write LAMMPS data file
        lammps_data = LammpsData.from_structure(structure, atom_style="charge")
        lammps_data.write_file(output_data)
        print(f"[SUCCESS] Wrote LAMMPS data file: {output_data}")

        # Write XYZ file
        xyz_output = output_data.replace(".data", ".xyz")
        XYZ(structure).write_file(xyz_output)
        print(f"[SUCCESS] Wrote XYZ file: {xyz_output}")

    except Exception as e:
        print(f"[ERROR] {e}")

def print_usage():
    print("Usage: python cif_to_lammps.py <input.cif> <output.data>")
    print("Example: python cif_to_lammps.py tetragonal_LLZO.cif LLZO.data")
    print("!!! Only for ML potentials (e.g., ORB, DeepMD) !!!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("[ERROR] Invalid number of arguments.")
        print_usage()
    elif not sys.argv[1].endswith(".cif") or not sys.argv[2].endswith(".data"):
        print("[ERROR] File extensions must be: .cif for input, .data for output.")
        print_usage()
    else:
        cif_input = sys.argv[1]
        output_data = sys.argv[2]
        convert_cif_to_outputs(cif_input, output_data)

