#!/usr/bin/env python3

import sys
import os
import argparse
from ase import io
from ase.optimize import BFGS, LBFGS
from orb_models.forcefield import pretrained
from orb_models.forcefield.calculator import ORBCalculator

# ----- ORB models -----
ORB_MODELS = {
    1: "orb-v3-conservative-omol",
    2: "orb-v3-direct-omol",
    3: "orb-v3-conservative-inf-omat",
    4: "orb-v3-direct-inf-omat",
    5: "orb-v3-conservative-inf-mpa",
    6: "orb-v3-direct-inf-mpa",
}

# ----- Optimizers -----
OPTIMIZERS = {1: "BFGS", 2: "LBFGS"}

# Default fmax
DEFAULT_FMAX = 0.01


def show_usage_and_models():
    print("\n=== Available ORB Models ===")
    for k, v in ORB_MODELS.items():
        print(f"  {k}: {v}")

    print("\n=== Optimizers ===")
    for k, v in OPTIMIZERS.items():
        print(f"  {k}: {v}")

    print(f"\nDefault fmax (convergence criterion): {DEFAULT_FMAX}")

    print("\n=== Usage ===")
    print("For chekpoint file trained on OMOL25 (*-omol):")
    print(
        "  ./opt_orb.py --model <num> --input <file> --charge <int> --spin <int> [--optimizer <num>] [--fmax <float>]\n"
    )
    print("For other checkpoint files (orb-v3-*):")
    print(
        "  ./opt_orb.py --model <num> --input <file> [--optimizer <num>] [--fmax <float>]\n"
    )
    sys.exit(0)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Optimize structures using pretrained ORB models.", add_help=True
    )

    parser.add_argument(
        "--model",
        "-m",
        type=int,
        help="Model number (see list in output if none provided)",
    )
    parser.add_argument("--input", "-i", type=str, help="Input structure file")
    parser.add_argument(
        "--charge",
        "-c",
        type=int,
        help="Total charge (required for molecular ORB models)",
    )
    parser.add_argument(
        "--spin", "-s", type=int, help="Total spin (required for molecular ORB models)"
    )
    parser.add_argument(
        "--optimizer",
        "-o",
        type=int,
        default=1,
        choices=OPTIMIZERS.keys(),
        help=f"Optimizer number (default: 1 = {OPTIMIZERS[1]})",
    )
    parser.add_argument(
        "--fmax",
        "-f",
        type=float,
        default=DEFAULT_FMAX,
        help=f"Convergence criterion (default: {DEFAULT_FMAX})",
    )

    # Show models & usage if no arguments are provided
    if len(sys.argv) == 1:
        show_usage_and_models()

    args = parser.parse_args()

    return args


def main():
    args = parse_arguments()

    # Validate model
    if args.model not in ORB_MODELS:
        print("Error: Invalid or missing model number.\n")
        show_usage_and_models()
    model_name = ORB_MODELS[args.model]

    # Validate input file
    if not args.input or not os.path.isfile(args.input):
        print("Error: Please specify a valid input file using --input <file>.\n")
        sys.exit(1)

    # Check charge/spin requirements dynamically
    if "omol" in model_name:
        if args.charge is None or args.spin is None:
            print("Error: Molecular ORB models require both --charge and --spin.\n")
            sys.exit(1)
    else:
        if args.charge is not None or args.spin is not None:
            print("Warning: Charge and spin will be ignored for non-molecular models.")

    optimizer_name = OPTIMIZERS[args.optimizer]
    fmax = args.fmax

    print(f"Using model: {model_name}")
    print(f"Optimizer: {optimizer_name}")
    print(f"fmax: {fmax}")

    # ----- Read atoms -----
    try:
        atoms = io.read(args.input)
    except Exception as e:
        print(f"Error reading {args.input}: {e}")
        sys.exit(1)

    # ----- Set charge and spin if needed -----
    if "omol" in model_name:
        atoms.info["charge"] = args.charge
        atoms.info["spin"] = args.spin

    # ----- Load ORB model -----
    print(f"Loading ORB model: {model_name} ...")
    device = "cuda"
    orb_func_name = model_name.replace("-", "_")
    orbff = getattr(pretrained, orb_func_name)(device=device, precision="float32-high")

    calc = ORBCalculator(orbff, device=device)
    atoms.calc = calc

    # ----- Create output folder -----
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    folder = base_name
    os.makedirs(folder, exist_ok=True)

    # ----- Optimize -----
    # Define the trajectory file path inside the folder
    traj_file = os.path.join(folder, f"{base_name}.traj")
    print(f"Optimizing with {optimizer_name} ... (Trajectory: {traj_file})")
    
    # Pass the trajectory path to the optimizer
    if optimizer_name == "BFGS":
        dyn = BFGS(atoms, trajectory=traj_file)
    elif optimizer_name == "LBFGS":
        dyn = LBFGS(atoms, trajectory=traj_file)
    else:
        dyn = BFGS(atoms, trajectory=traj_file)

    dyn.run(fmax=fmax)
    # ----- Save optimized structure -----
    ext = os.path.splitext(args.input)[1]
    output_file = os.path.join(folder, f"{base_name}_opt.xyz")
    io.write(output_file, atoms)
    print(f"Optimized structure saved to: {output_file}")


if __name__ == "__main__":
    main()
