import sys
import os
from ase.io import read, write
from ase.optimize import BFGS
from ase.filters import UnitCellFilter
from orb_models.forcefield import pretrained
from orb_models.forcefield.calculator import ORBCalculator

# --- CHECK ARGUMENTS ---
if len(sys.argv) < 2:
    print("Usage: python relax_orb.py <input_structure>")
    sys.exit(1)

input_file = sys.argv[1]
if not os.path.isfile(input_file):
    print(f"Error: file '{input_file}' not found.")
    sys.exit(1)

# --- CREATE OUTPUT NAME ---
base, ext = os.path.splitext(input_file)
output_file = f"{base}_relaxed{ext}"

# --- SETTINGS ---
device = "cuda"
fmax = 0.05

# --- LOAD STRUCTURE ---
atoms = read(input_file)

# --- SET UP ORB CALCULATOR ---
orbff = pretrained.orb_v3_conservative_inf_omat(
    device=device,
    precision="float32-high"
)
calc = ORBCalculator(orbff, device=device)
atoms.calc = calc

# --- DETERMINE IF PERIODIC ---
is_periodic = atoms.get_pbc().any()

print("Periodic structure:", is_periodic)

# --- RELAX ---
if is_periodic:
    print("Relaxing cell + positions (periodic system)...")
    ucf = UnitCellFilter(atoms)
    dyn = BFGS(ucf)
else:
    print("Relaxing positions only (molecule)...")
    dyn = BFGS(atoms)

dyn.run(fmax=fmax)

# --- SAVE RESULT ---
write(output_file, atoms)
print(f"Relaxation complete. Relaxed structure written to {output_file}")