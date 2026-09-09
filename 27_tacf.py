import numpy as np
import matplotlib.pyplot as plt
import sys

# -------------------------
# Helper functions
# -------------------------
def vector(p1, p2):
    return np.array(p2) - np.array(p1)

def dihedral(p0, p1, p2, p3):
    """Compute dihedral angle (radians) between 4 points"""
    b0 = -1.0 * vector(p0, p1)
    b1 = vector(p1, p2)
    b2 = vector(p2, p3)
    b1 /= np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1) * b1
    w = b2 - np.dot(b2, b1) * b1
    x = np.dot(v, w)
    y = np.dot(np.cross(b1, v), w)
    return np.arctan2(y, x)

# -------------------------
# Main
# -------------------------
if len(sys.argv) != 3:
    print("Usage: python tacf_avg_only.py dump.lammpstrj datafile")
    sys.exit(1)

dumpfile = sys.argv[1]
datafile = sys.argv[2]

# -------------------------
# Step 1: parse dihedral types
# -------------------------
dihedral_dict = {}  # key: type, value: list of atoms
with open(datafile, 'r') as f:
    section = None
    for line in f:
        if 'Dihedrals' in line:
            section = 'dihedrals'
            next(f)  # skip header
            continue
        if section == 'dihedrals':
            if line.strip() == '':
                break
            parts = line.split()
            d_type = parts[1]
            atoms = list(map(int, parts[2:6]))
            if d_type not in dihedral_dict:
                dihedral_dict[d_type] = []
            dihedral_dict[d_type].append(atoms)

# List dihedral types
if len(dihedral_dict) == 0:
    print("No dihedrals found in data file.")
    sys.exit(1)

types_sorted = sorted(dihedral_dict.keys(), key=int)
print("Detected dihedral types in data file:")
for dt in types_sorted:
    print(f" - {dt}")

# Ask user to pick one type
selected_type = input("Enter the dihedral type to compute TACF for: ").strip()
if selected_type not in dihedral_dict:
    print(f"No dihedrals of type {selected_type} found. Exiting.")
    sys.exit(1)

dihedrals = dihedral_dict[selected_type]
print(f"Found {len(dihedrals)} dihedrals of type {selected_type}")

# -------------------------
# Step 2: read dump file
# -------------------------
frames = []
with open(dumpfile, 'r') as f:
    while True:
        line = f.readline()
        if not line:
            break
        if "ITEM: TIMESTEP" in line:
            timestep = int(f.readline())
            # Skip to "ITEM: NUMBER OF ATOMS"
            while "ITEM: NUMBER OF ATOMS" not in line:
                line = f.readline()
            n_atoms = int(f.readline().strip())
            # Skip BOX BOUNDS
            while "ITEM: ATOMS" not in line:
                line = f.readline()
            # Read atom positions
            atoms_pos = {}
            for _ in range(n_atoms):
                parts = f.readline().split()
                atom_id = int(parts[0])
                x, y, z = map(float, parts[2:5])
                atoms_pos[atom_id] = np.array([x, y, z])
            frames.append(atoms_pos)

nframes = len(frames)
print(f"Read {nframes} frames from {dumpfile}")

# -------------------------
# Step 3: compute dihedrals
# -------------------------
dihedral_angles = np.zeros((len(dihedrals), nframes))
for fidx, frame in enumerate(frames):
    for didx, atoms in enumerate(dihedrals):
        p0, p1, p2, p3 = [frame[a] for a in atoms]
        dihedral_angles[didx, fidx] = dihedral(p0, p1, p2, p3)

# -------------------------
# Step 3.1: Unwrap dihedrals
# -------------------------
print("Unwrapping dihedral angles...")
# We use np.diff to find jumps and np.round to find how many 2*pi multiples to shift
for i in range(len(dihedrals)):
    diffs = np.diff(dihedral_angles[i, :])
    # Find jumps larger than pi and shift them by 2*pi
    adjustments = np.hstack(([0], -2 * np.pi * np.round(diffs / (2 * np.pi))))
    dihedral_angles[i, :] += np.cumsum(adjustments)
    
# -------------------------
# Step 4: compute normalized average TACF
# -------------------------
cos_phi0 = np.cos(dihedral_angles[:, 0])
denominator = np.mean(cos_phi0**2) - np.mean(cos_phi0)**2

tacf_avg = np.zeros(nframes)
for t in range(nframes):
    cos_phi_t = np.cos(dihedral_angles[:, t])
    numerator = np.mean(cos_phi_t * cos_phi0) - np.mean(cos_phi0)**2
    tacf_avg[t] = numerator / denominator

# -------------------------
# Step 5: save results
# -------------------------
np.savetxt("tacf_avg.dat", tacf_avg)
print("Saved tacf_avg.dat")

# -------------------------
# Step 6: plot
# -------------------------
time = np.arange(nframes)  # multiply by dt*dump_freq if needed

plt.figure()
plt.plot(time, tacf_avg, 'k', lw=2, label="Average TACF")
plt.xlabel("Frame")
plt.ylabel("Normalized TACF")
plt.title(f"Torsional Autocorrelation Function (type {selected_type})")
plt.legend()
plt.show()