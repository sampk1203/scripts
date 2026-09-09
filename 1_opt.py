#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

# ========================
# Hardcoded ORCA options
# ========================
METHODS = ["B3LYP", "PBE0", "M06-2X"]
BASES = ["DEF2-SVP", "DEF2-TZVP"]

# ========================
# Default values
# ========================
CHARGE = 0
UHF = 0
MULT = None  # will calculate later
METHOD = "B3LYP"
BASIS = "DEF2-SVP"
DO_FREQ = False
ONLY_XTB = False  # new flag

# ========================
# Parse command-line args
# ========================
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <molecule.xyz|molecule.mol> [--chrg N] [--uhf M] [--mult K] [--freq] [--method METHOD] [--basis BASIS] [--xtb]")
    print(f"Available methods: {METHODS}")
    print(f"Available bases: {BASES}")
    sys.exit(1)

INPUT = sys.argv[1]
args = sys.argv[2:]

i = 0
while i < len(args):
    if args[i] == "--chrg":
        CHARGE = int(args[i+1])
        i += 2
    elif args[i] == "--uhf":
        UHF = int(args[i+1])
        i += 2
    elif args[i] == "--mult":
        MULT = int(args[i+1])
        i += 2
    elif args[i] == "--freq":
        DO_FREQ = True
        i += 1
    elif args[i] == "--method":
        METHOD = args[i+1]
        i += 2
    elif args[i] == "--basis":
        BASIS = args[i+1]
        i += 2
    elif args[i] == "--xtb":
        ONLY_XTB = True
        i += 1
    else:
        print(f"Unknown option: {args[i]}")
        sys.exit(1)

# ========================
# Preprocess input
# ========================
EXT = os.path.splitext(INPUT)[1].lower()

if EXT != ".xyz":
    xyz_file = os.path.splitext(INPUT)[0] + ".xyz"
    conv_cmd = ["obabel", INPUT, "-O", xyz_file]
    print(f"Converting {INPUT} -> {xyz_file} with Open Babel...")
    subprocess.run(conv_cmd, check=True)
    INPUT = xyz_file  # continue with xyz version

# ========================
# Check binaries
# ========================
xtb_path = shutil.which("xtb")
orca_path = shutil.which("orca")
obabel_path = shutil.which("obabel")

if xtb_path is None:
    print("Error: xtb not found in PATH")
    sys.exit(1)
if not ONLY_XTB and orca_path is None:
    print("Error: orca not found in PATH")
    sys.exit(1)
if obabel_path is None:
    print("Error: obabel not found in PATH (required for .mol/.sdf inputs)")
    sys.exit(1)

# ========================
# Setup directories
# ========================
BASENAME = os.path.splitext(os.path.basename(INPUT))[0]
XTB_DIR = os.path.join(BASENAME, "xtb")
ORCA_DIR = os.path.join(BASENAME, "orca")
os.makedirs(XTB_DIR, exist_ok=True)
if not ONLY_XTB:
    os.makedirs(ORCA_DIR, exist_ok=True)

# ========================
# Save note of calculation flags
# ========================
flags_note = os.path.join(BASENAME, "calculation_flags.txt")
with open(flags_note, "w") as f:
    f.write(f"Input file: {INPUT}\n")
    f.write(f"Charge: {CHARGE}\n")
    f.write(f"Unpaired electrons (UHF): {UHF}\n")
    f.write(f"Multiplicity: {MULT if MULT is not None else 'Auto-calculated'}\n")
    f.write(f"Method: {METHOD}\n")
    f.write(f"Basis: {BASIS}\n")
    f.write(f"Frequency calculation: {'Yes' if DO_FREQ else 'No'}\n")
    f.write(f"Only XTB: {'Yes' if ONLY_XTB else 'No'}\n")

# ========================
# Run XTB
# ========================
try:
    shutil.copy(INPUT, XTB_DIR)
    os.chdir(XTB_DIR)

    # Use --ohess if frequency calculation requested, else --opt
    if DO_FREQ:
        xtb_cmd = [xtb_path, os.path.basename(INPUT), "--ohess"]
        if CHARGE != 0:
            xtb_cmd += ["--chrg", str(CHARGE)]
        if UHF != 0:
            xtb_cmd += ["--uhf", str(UHF)]
    else:
        xtb_cmd = [xtb_path, os.path.basename(INPUT), "--opt"]
        if CHARGE != 0:
            xtb_cmd += ["--chrg", str(CHARGE)]
        if UHF != 0:
            xtb_cmd += ["--uhf", str(UHF)]

    print("Running XTB...")
    with open("xtb.log", "w") as logf:
        subprocess.run(xtb_cmd, stdout=logf, stderr=subprocess.STDOUT, check=True)

    if not os.path.isfile("xtbopt.xyz"):
        print("Error: XTB optimization failed.")
        sys.exit(1)
except Exception as e:
    print("Error: XTB run stopped:", e)
    sys.exit(1)

# ========================
# Run ORCA via mpirun (only if not ONLY_XTB)
# ========================
if not ONLY_XTB:
    try:
        os.chdir(os.path.join("..", "orca"))
        shutil.copy(os.path.join("..", "xtb", "xtbopt.xyz"), ".")

        # Calculate multiplicity if not given
        if MULT is None:
            S = UHF / 2
            MULT = int(2*S + 1)

        inp_file = f"{BASENAME}.inp"
        with open(inp_file, "w") as f:
            line = f"! {METHOD} {BASIS} OPT"
            if DO_FREQ:
                line += " FREQ"
            f.write(line + "\n\n")
            f.write(f"* xyzfile {CHARGE} {MULT} xtbopt.xyz\n")

        log_file = f"{BASENAME}.log"
        print("Running ORCA via mpirun...")
        num_procs = os.cpu_count()
        with open(log_file, "w") as logf:
            result = subprocess.run(
                ["mpirun", "-np", str(num_procs), orca_path, inp_file],
                stdout=logf,
                stderr=subprocess.STDOUT
            )

        if result.returncode != 0:
            print(f"ORCA finished with return code {result.returncode}. Check log for details.")
        else:
            print("ORCA finished successfully.")
    except Exception as e:
        print("Error: ORCA run stopped:", e)
        sys.exit(1)

# ========================
# Done
# ========================
print("Calculation done successfully.")

