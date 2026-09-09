"""
rmsd_process.py — Compute RMSD using VMD (pbc unwrap -all)
for one or more LAMMPS atom types, then save transformed data
(dummy modifiedX MSD dummy) as rmsd.<dumpfile>.
"""

import sys
import os
import subprocess
import numpy as np


# =========================
# Step 1: Run VMD RMSD
# =========================
def run_vmd_rmsd(dumpfile, atom_types, outfile="rmsd.dat"):
    """Run VMD to unwrap PBCs and compute RMSD for given atom types."""

    # build selection string
    seltext = " or ".join([f"type {t}" for t in atom_types])

    # nice printable string
    type_string = " ".join(map(str, atom_types))

    vmd_script = f"""
package require pbctools
mol new {dumpfile} type lammpstrj waitfor all
pbc unwrap -all

set seltext "{seltext}"
set n [molinfo top get numframes]

set outf [open "{outfile}" w]
puts $outf "# Frame RMSD (atom types {type_string})"

set ref [atomselect top $seltext frame 0]

for {{set i 0}} {{$i < $n}} {{incr i}} {{
    set sel [atomselect top $seltext frame $i]
    set val [measure rmsd $sel $ref]
    puts $outf "$i $val"
}}

close $outf
exit
"""

    with open("vmd_rmsd.tcl", "w") as f:
        f.write(vmd_script)

    print(f"Running VMD RMSD for atom types {atom_types}...")
    subprocess.run(
        ["vmd", "-dispdev", "text", "-e", "vmd_rmsd.tcl"],
        check=True
    )

    os.remove("vmd_rmsd.tcl")
    print(f"RMSD data saved to {outfile}")


# =========================
# Step 2: Transform and save
# =========================
def transform_rmsd(input_file, dumpfile):
    """Add dummy columns, scale x, square y, and save final MSD file."""

    data = np.loadtxt(input_file, comments="#")

    x = data[:, 0]
    y = data[:, 1] ** 2   # RMSD → MSD

    dummy = np.zeros_like(x)

    outdata = np.column_stack((dummy, x, y, dummy))

    outname = f"rmsd.{os.path.basename(dumpfile)}"

    np.savetxt(
        outname,
        outdata,
        fmt="%.6f",
        header="dummy modifiedX MSD dummy",
        comments=""
    )

    print(f"Transformed MSD data saved to {outname}")


# =========================
# Step 3: Main
# =========================
def main():

    if len(sys.argv) < 3:
        print("Usage: python rmsd_process.py dump.lammpstrj TYPE1 TYPE2 TYPE3 ...")
        sys.exit(1)

    dumpfile = sys.argv[1]

    # Multiple atom types
    atom_types = [int(t) for t in sys.argv[2:]]

    if not os.path.exists(dumpfile):
        print(f"File not found: {dumpfile}")
        sys.exit(1)

    run_vmd_rmsd(dumpfile, atom_types, "rmsd.dat")
    transform_rmsd("rmsd.dat", dumpfile)


if __name__ == "__main__":
    main()