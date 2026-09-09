#!/usr/bin/env python3
import os
import sys

# ========================
# Check input
# ========================
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <molecule.(xyz|mol|sdf|...)>")
    sys.exit(1)

INPUT = sys.argv[1]
# Strip off extension, only basename matters for locating workdir
BASENAME = os.path.splitext(os.path.basename(INPUT))[0]
WORKDIR = BASENAME  # Folder name same as molecule basename

XTB_LOG = os.path.join(WORKDIR, "xtb", "xtb.log")
ORCA_LOG = os.path.join(WORKDIR, "orca", f"{BASENAME}.log")
XTB_TRAJ = os.path.join(WORKDIR, "xtb", "xtbopt.log")
ORCA_TRAJ = os.path.join(WORKDIR, "orca", f"{BASENAME}_trj.xyz")
FLAGS_FILE = os.path.join(WORKDIR, "calculation_flags.txt")

# Output files in current directory
MERGED_TRAJ = f"{BASENAME}_traj.xyz"
SUMMARY_FILE = f"{BASENAME}_summary.txt"

# ========================
# Merge trajectories
# ========================
input_dir = os.path.dirname(os.path.abspath(INPUT))
MERGED_TRAJ = os.path.join(input_dir, f"{BASENAME}_traj.xyz")

sources = []
if os.path.isfile(XTB_TRAJ):
    sources.append(XTB_TRAJ)
if os.path.isfile(ORCA_TRAJ):
    sources.append(ORCA_TRAJ)

with open(MERGED_TRAJ, "w") as out:
    if sources:
        for fname in sources:
            with open(fname) as f:
                out.write(f.read())
        print(f"✅ Merged trajectory written to {MERGED_TRAJ}")
    else:
        out.write("# No trajectory data found\n")
        print("⚠️ No trajectory data found, empty file created.")

import shutil

# ========================
# Copy final optimized structures
# ========================
xtb_opt_file = os.path.join(WORKDIR, "xtb", "xtbopt.xyz")
orca_opt_file = os.path.join(WORKDIR, "orca", f"{BASENAME}.xyz")

if os.path.isfile(xtb_opt_file):
    dest = os.path.join(input_dir, f"{BASENAME}_xtbopt.xyz")
    try:
        shutil.copy(xtb_opt_file, dest)
        print(f"✅ Copied XTB optimized structure to {dest}")
    except Exception as e:
        print(f"⚠️ Could not copy XTB optimized structure: {e}")

if os.path.isfile(orca_opt_file):
    dest = os.path.join(input_dir, f"{BASENAME}_orcaopt.xyz")
    try:
        shutil.copy(orca_opt_file, dest)
        print(f"✅ Copied ORCA optimized structure to {dest}")
    except Exception as e:
        print(f"⚠️ Could not copy ORCA optimized structure: {e}")


# ========================
# Extract XTB energy
# ========================
XTB_ENERGY = "N/A"
if os.path.isfile(XTB_LOG):
    with open(XTB_LOG) as f:
        for line in f:
            if "TOTAL ENERGY" in line:
                parts = line.split()
                if len(parts) >= 5:
                    XTB_ENERGY = f"{parts[3]} {parts[4]}"

# ========================
# Extract ORCA energy
# ========================
ORCA_ENERGY = "N/A"
if os.path.isfile(ORCA_LOG):
    with open(ORCA_LOG) as f:
        for line in f:
            if "FINAL SINGLE POINT ENERGY" in line:
                parts = line.split()
                if len(parts) >= 5:
                    ORCA_ENERGY = f"{parts[4]} Eh"

# ========================
# Check for frequency calculation
# ========================
freq_calc_done = False
if os.path.isfile(FLAGS_FILE):
    with open(FLAGS_FILE) as f:
        for line in f:
            if "Frequency calculation" in line:
                if "Yes" in line:
                    freq_calc_done = True
                break

xtb_imag = []
orca_imag = []

# ========================
# XTB vibrational analysis
# ========================
if freq_calc_done:
    XTB_VIB = os.path.join(WORKDIR, "xtb", "vibspectrum")
    if os.path.isfile(XTB_VIB):
        with open(XTB_VIB) as f:
            lines = f.readlines()
        # Print first 3 lines
        xtb_first3 = [l.strip() for l in lines[:3]]
        # Process wave numbers
        for l in lines[3:]:
            if l.strip() == "" or l.startswith("$") or l.startswith("#"):
                continue
            parts = l.split()
            if len(parts) >= 3:
                try:
                    wn = float(parts[2])
                    if wn < -1e-6:  # treat -0.00 as 0
                        xtb_imag.append(l.strip())
                except:
                    continue

# ========================
# ORCA vibrational analysis
# ========================
if freq_calc_done and os.path.isfile(ORCA_LOG):
    with open(ORCA_LOG) as f:
        lines = f.readlines()
    ir_start = None
    for i, l in enumerate(lines):
        if "IR SPECTRUM" in l:
            ir_start = i
            break
    orca_header = []
    if ir_start is not None:
        # Collect the header block (next ~5 lines)
        orca_header = [lines[ir_start].rstrip(),
                       lines[ir_start+1].rstrip(),
                       lines[ir_start+2].rstrip(),
                       lines[ir_start+3].rstrip(),
                       lines[ir_start+4].rstrip(),
                       lines[ir_start+5].rstrip()]
        # Scan frequencies
        for l in lines[ir_start+6:]:
            if l.strip() == "" or l.startswith("-"):
                continue
            parts = l.split()
            if len(parts) >= 2:
                try:
                    freq = float(parts[1])
                    if freq < -1e-6:  # Imaginary frequency
                        orca_imag.append(l.strip())
                except:
                    continue

# ========================
# Read calculation flags
# ========================
calc_flags_text = []
if os.path.isfile(FLAGS_FILE):
    with open(FLAGS_FILE) as f:
        calc_flags_text = [line.strip() for line in f.readlines()]

# ========================
# Write summary
# ========================
with open(SUMMARY_FILE, "w") as f:
    # First write calculation flags
    for line in calc_flags_text:
        print(line)
        f.write(line + "\n")
    f.write("\n")
    
    # Then the rest of the summary
    summary_lines = [
        "==== Post Processing Summary ====",
        f"XTB Energy: {XTB_ENERGY}",
        f"ORCA Final Energy: {ORCA_ENERGY}",
        f"Trajectory merged into: {MERGED_TRAJ}",
        f"====================================="
    ]
    for line in summary_lines:
        print(line)
        f.write(line + "\n")

    if freq_calc_done:
        # XTB vib info
        print("\nXTB Vibrational Analysis:")
        f.write("\nXTB Vibrational Analysis:\n")
        for l in xtb_first3:
            print(l)
            f.write(l + "\n")
        if xtb_imag:
            print("Imaginary frequencies:")
            f.write("Imaginary frequencies:\n")
            for row in xtb_imag:
                print(row)
                f.write(row + "\n")
        else:
            print("No imaginary frequencies found in xTB.")
            f.write("No imaginary frequencies found in xTB.\n")

        # ORCA vib info
        print("\nORCA Vibrational Analysis:")
        f.write("\nORCA Vibrational Analysis:\n")
        for l in orca_header:
            print(l)
            f.write(l + "\n")
        if orca_imag:
            print("Imaginary frequencies:")
            f.write("Imaginary frequencies:\n")
            for row in orca_imag:
                print(row)
                f.write(row + "\n")
        else:
            print("No imaginary frequencies found in ORCA.")
            f.write("No imaginary frequencies found in ORCA.\n")

