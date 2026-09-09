from pymatgen.core import Structure
from pymatgen.io.cif import CifWriter

# ---------------- PARAMETERS ----------------
input_cif = "cubic-LLZO.cif"
output_cif = "cubic-LLZO_4x4x2.cif"
supercell_dims = (2, 2, 1)  # a x b x c
# --------------------------------------------

# Load structure
structure = Structure.from_file(input_cif)
print(f"[+] Original structure: {len(structure.sites)} atoms")

# Make supercell
structure.make_supercell(supercell_dims)
print(f"[+] Supercell created: {len(structure.sites)} atoms")
print(f"[+] Supercell lattice:\n{structure.lattice.matrix}")

# Write CIF
writer = CifWriter(structure)
writer.write_file(output_cif)
print(f"[+] Supercell CIF written: {output_cif}")
